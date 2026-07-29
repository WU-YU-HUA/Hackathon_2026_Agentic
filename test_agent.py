"""
測試 Agent 與 Tools 整合
可以輸入問題，Agent 會使用 api/__init__.py 中的 tools 來回答
使用最新的 google-genai SDK
"""

import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from api import TOOL_MAP, TOOLS_SCHEMA

# 載入環境變數
load_dotenv()

def convert_schema_to_genai_format(tools_schema):
    """將 OpenAI 格式的 tools schema 轉換為 Google GenAI 格式"""
    function_declarations = []
    
    for tool in tools_schema:
        if tool["type"] == "function":
            func_def = tool["function"]
            function_declarations.append(
                types.FunctionDeclaration(
                    name=func_def["name"],
                    description=func_def["description"],
                    parameters=func_def["parameters"]
                )
            )
    
    return [types.Tool(function_declarations=function_declarations)]

def execute_function_call(function_name, function_args):
    """執行 function call"""
    if function_name in TOOL_MAP:
        func = TOOL_MAP[function_name]
        try:
            # 將 args 轉換為 dict (如果是 SDK 原生的結構)
            args_dict = dict(function_args) if function_args else {}
            # 執行函數
            result = func(**args_dict)
            
            # GenAI SDK 要求 function_response 必須是 dict 格式
            if not isinstance(result, dict):
                return {"result": result}
            return result
            
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": f"Unknown function: {function_name}"}

def chat_with_agent(chat_session, user_message):
    """與 Agent 對話，手動處理 Function Calling 循環"""
    
    try:
        # 1. 傳送使用者訊息
        response = chat_session.send_message(user_message)
        
        # 2. 檢查模型是否要求呼叫工具 (使用 while 處理可能的多重/連續呼叫)
        while response.function_calls:
            for func_call in response.function_calls:
                func_name = func_call.name
                func_args = func_call.args
                
                print(f"🔧 模型請求呼叫工具: {func_name}")
                print(f"   傳入參數: {func_args}")
                
                # 3. 執行本地端對應的 Python 函式
                result = execute_function_call(func_name, func_args)
                print(f"   ✅ 工具執行完畢，將數據回傳給模型...\n")
                
                # 4. 將結果包裝並回傳給模型，讓模型接續回答
                response = chat_session.send_message(
                    types.Part.from_function_response(
                        name=func_name,
                        response=result
                    )
                )
        
        # 5. 顯示最終整合了數據的回答
        if response.text:
            print("="*60)
            print(f"🤖 Agent 回答:")
            print(f"{response.text}\n")
        else:
            print("⚠️ 無文字回應")
            
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        print(f"{'='*60}\n")


def main():
    """主程式"""
    print("=" * 60)
    print("🤖 Agent Tools 測試程式 (使用 google-genai)")
    print("=" * 60)
    print("可用的 Tools:")
    for tool in TOOLS_SCHEMA:
        func = tool["function"]
        print(f"  - {func['name']}: {func['description']}")
    print("=" * 60)
    print("輸入 'quit' 或 'exit' 離開\n")
    
    # 檢查 API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 錯誤: 找不到 GEMINI_API_KEY")
        print("請在 .env 檔案中設定 GEMINI_API_KEY")
        return
    
    print(f"✅ API Key 已載入: {api_key[:10]}...\n")
    
    # 初始化客戶端
    client = genai.Client(api_key=api_key)
    tools = convert_schema_to_genai_format(TOOLS_SCHEMA)
    
    # === 關鍵修改：建立 Chat Session ===
    # 讓模型具有上下文記憶，這樣它呼叫工具拿到數據後，才知道要回答什麼
    chat = client.chats.create(
        model='gemini-flash-latest',  # 建議使用 2.0-flash 或 1.5-flash
        config=types.GenerateContentConfig(
            tools=tools,
            temperature=0.7,
        )
    )
    
    # 對話循環
    while True:
        try:
            user_input = input("你: ")
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再見！")
                break
            
            if not user_input.strip():
                continue
            
            # 將共用的 chat instance 傳入
            chat_with_agent(chat, user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 再見！")
            break
        except Exception as e:
            print(f"❌ 未預期錯誤: {e}\n")

if __name__ == "__main__":
    main()