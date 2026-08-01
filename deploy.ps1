<#
    crypto-agent 部署腳本 (ECR image-based -> AWS App Runner)
    使用方式:
        1. 先安裝並設定 AWS CLI (aws configure)
        2. 在下方 CONFIG 區塊填入你的 AWS 帳號資訊與機密值
        3. 執行:  ./deploy.ps1
    腳本具冪等性設計:重複執行時已存在的資源會略過建立,只更新映像並觸發部署。
#>

$ErrorActionPreference = "Stop"

# ============================================================
# CONFIG - 請依實際情況修改
# ============================================================
$AccountId   = "<ACCOUNT_ID>"          # 例: 123456789012
$Region      = "ap-northeast-1"         # 你的 AWS 區域
$RepoName    = "crypto-agent"
$ServiceName = "crypto-agent"
$ImageTag    = "latest"

# 機密值 (部署前填入;或改成從環境變數讀取,避免寫在檔案裡)
$GeminiApiKey = $env:GEMINI_API_KEY
$MaxAccess    = $env:MAX_ACCESS
$MaxSecret    = $env:MAX_SECRET
# ============================================================

$EcrUri   = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$ImageUri = "$EcrUri/$RepoName`:$ImageTag"

Write-Host "=== 1. 建立 ECR Repository (若不存在) ===" -ForegroundColor Cyan
aws ecr describe-repositories --repository-names $RepoName --region $Region 2>$null
if ($LASTEXITCODE -ne 0) {
    aws ecr create-repository --repository-name $RepoName --region $Region --image-scanning-configuration scanOnPush=true
    Write-Host "  ECR Repository 已建立: $RepoName" -ForegroundColor Green
} else {
    Write-Host "  ECR Repository 已存在,略過" -ForegroundColor Yellow
}

Write-Host "=== 2. 登入 ECR ===" -ForegroundColor Cyan
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $EcrUri

Write-Host "=== 3. 建置並推送映像 ===" -ForegroundColor Cyan
docker build -t "$RepoName`:$ImageTag" .
docker tag "$RepoName`:$ImageTag" $ImageUri
docker push $ImageUri
Write-Host "  映像已推送: $ImageUri" -ForegroundColor Green

Write-Host "=== 4. 建立 / 更新 Secrets Manager 機密 ===" -ForegroundColor Cyan
function Set-Secret($name, $value) {
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Host "  警告: $name 值為空,略過" -ForegroundColor Yellow
        return
    }
    aws secretsmanager describe-secret --secret-id "crypto-agent/$name" --region $Region 2>$null
    if ($LASTEXITCODE -ne 0) {
        aws secretsmanager create-secret --name "crypto-agent/$name" --secret-string $value --region $Region | Out-Null
        Write-Host "  已建立機密: crypto-agent/$name" -ForegroundColor Green
    } else {
        aws secretsmanager put-secret-value --secret-id "crypto-agent/$name" --secret-string $value --region $Region | Out-Null
        Write-Host "  已更新機密: crypto-agent/$name" -ForegroundColor Green
    }
}
Set-Secret "GEMINI_API_KEY" $GeminiApiKey
Set-Secret "MAX_ACCESS" $MaxAccess
Set-Secret "MAX_SECRET" $MaxSecret

Write-Host "=== 5. 建立 IAM 角色 (若不存在) ===" -ForegroundColor Cyan
# ECR 存取角色 (App Runner 拉映像用)
aws iam get-role --role-name AppRunnerECRAccessRole 2>$null
if ($LASTEXITCODE -ne 0) {
    aws iam create-role --role-name AppRunnerECRAccessRole `
        --assume-role-policy-document file://deploy/ecr-access-role-trust.json | Out-Null
    aws iam attach-role-policy --role-name AppRunnerECRAccessRole `
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess | Out-Null
    Write-Host "  已建立 AppRunnerECRAccessRole" -ForegroundColor Green
} else {
    Write-Host "  AppRunnerECRAccessRole 已存在,略過" -ForegroundColor Yellow
}

# 實例角色 (App Runner 執行時讀取 Secrets Manager 用)
aws iam get-role --role-name AppRunnerInstanceRole 2>$null
if ($LASTEXITCODE -ne 0) {
    aws iam create-role --role-name AppRunnerInstanceRole `
        --assume-role-policy-document file://deploy/instance-role-trust.json | Out-Null
    aws iam put-role-policy --role-name AppRunnerInstanceRole `
        --policy-name ReadCryptoAgentSecrets `
        --policy-document file://deploy/instance-role-secrets-policy.json | Out-Null
    Write-Host "  已建立 AppRunnerInstanceRole" -ForegroundColor Green
} else {
    Write-Host "  AppRunnerInstanceRole 已存在,略過" -ForegroundColor Yellow
}

Write-Host "=== 6. 建立 / 更新 App Runner 服務 ===" -ForegroundColor Cyan
$ServiceArn = aws apprunner list-services --region $Region `
    --query "ServiceSummaryList[?ServiceName=='$ServiceName'].ServiceArn" --output text

if ([string]::IsNullOrWhiteSpace($ServiceArn)) {
    Write-Host "  服務不存在,建立新服務 (使用 apprunner-service.json)..." -ForegroundColor Green
    Write-Host "  注意:請先確認 apprunner-service.json 內的 <ACCOUNT_ID>/<REGION> 已替換正確" -ForegroundColor Yellow
    aws apprunner create-service --cli-input-json file://apprunner-service.json --region $Region
} else {
    Write-Host "  服務已存在,觸發重新部署..." -ForegroundColor Green
    aws apprunner start-deployment --service-arn $ServiceArn --region $Region
}

Write-Host "`n=== 部署流程完成 ===" -ForegroundColor Cyan
Write-Host "可用以下指令查看服務狀態與網址:" -ForegroundColor White
Write-Host "  aws apprunner list-services --region $Region" -ForegroundColor Gray
