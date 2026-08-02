import streamlit as st
import json
import os
from anthropic import AnthropicBedrock  # 🌟 使用 Anthropic Bedrock SDK
from api import TOOL_MAP, TOOLS_SCHEMA

# ==========================================
# 🌟 動態解析側邊欄設定，生成專屬 Schema 與 Prompt
# ==========================================
def get_dynamic_agent_config(tools_config):
    """根據 sidebar 的勾選狀態，動態過濾工具並產生系統提示"""
    enabled_sentiment = tools_config.get("sentiment_tools", {})
    enabled_tech = tools_config.get("tech_tools", {})
    enabled_news = tools_config.get("news_tools", {})  # 🌟 取得新聞設定
    
    # 1. 過濾 TOOLS_SCHEMA
    filtered_schema = []
    allowed_api_names = ["get_allowed_symbol"]
    
    # 🌟 修正情緒工具名稱對應
    if enabled_sentiment.get("fear_greed") or enabled_sentiment.get("long_short"):
        allowed_api_names.append("get_vote_feargreed")
        allowed_api_names.append("get_social_ai_analysis")
        
    # 🌟 修正技術工具名稱對應
    if any(enabled_tech.values()):
        allowed_api_names.append("get_technical_data")
        allowed_api_names.append("get_kline_ai_analysis")

    # 🌟 確保新聞工具加入白名單
    if enabled_news.get("crypto_news", True):
        allowed_api_names.append("get_crypto_news")
        allowed_api_names.append("get_news_ai_analysis")
        
    for tool in TOOLS_SCHEMA:
        if tool["function"]["name"] in allowed_api_names:
            filtered_schema.append(tool)
            
    # 2. 建立動態 System Prompt
    allowed_metrics_names = []
    if enabled_sentiment.get("fear_greed"): allowed_metrics_names.append("恐懼貪婪指數")
    if enabled_sentiment.get("long_short"): allowed_metrics_names.append("多空投票比")
    if enabled_tech.get("bollinger"): allowed_metrics_names.append("布林通道(Bollinger Bands)")
    if enabled_tech.get("rsi"): allowed_metrics_names.append("RSI")
    if enabled_tech.get("ma"): allowed_metrics_names.append("MA (移動平均線)")
    if enabled_tech.get("ema"): allowed_metrics_names.append("EMA")
    if enabled_news.get("crypto_news", True): allowed_metrics_names.append("加密貨幣即時新聞與消息面 AI 分析")
    
    sys_instruct = (
        "你是一個專業的加密貨幣量化分析師。請善用工具來獲取即時數據。\n\n"
        "【⚠️ 最高指令限制】\n"
        f"使用者目前在控制面板中，『僅允許』你使用與分析以下指標與功能：{', '.join(allowed_metrics_names)}。\n"
        "即使你的 API 工具回傳了其他未經允許的數據，你都必須『假裝沒看到』，絕對不能在回答中主動提及未勾選的指標。"
        "若使用者直接詢問了未勾選的指標，請禮貌地提醒他：「您尚未在側邊欄開啟該指標功能，請開啟後再詢問」。"
    )
    
    return filtered_schema, sys_instruct

# ==========================================
# 核心功能與工具綁定 (Anthropic 格式轉換)
# ==========================================
def convert_schema_to_anthropic_format(tools_schema):
    """將 OpenAI/通用 Schema 轉換為 Anthropic Tools 格式"""
    anthropic_tools = []
    for tool in tools_schema:
        if tool.get("type") == "function":
            func_def = tool["function"]
            anthropic_tools.append({
                "name": func_def["name"],
                "description": func_def.get("description", ""),
                "input_schema": func_def.get("parameters", {}) # Anthropic 使用 input_schema
            })
    return anthropic_tools

def execute_function_call(function_name, function_args):
    """執行本地工具"""
    if function_name in TOOL_MAP:
        try:
            args_dict = dict(function_args) if function_args else {}
            result = TOOL_MAP[function_name](**args_dict)
            return result if isinstance(result, (dict, list)) else {"result": result}
        except Exception as e:
            return {"error": str(e)}
    return {"error": f"Unknown function: {function_name}"}

def get_bedrock_client(tools_config):
    """初始化 Anthropic Bedrock Client"""
    # 支援透過環境變數或 config 讀取金鑰
    aws_access_key = tools_config.get("aws_access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = tools_config.get("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = tools_config.get("aws_region") or os.getenv("AWS_REGION", "us-east-1")

    return AnthropicBedrock(
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        aws_region=aws_region
    )

# ==========================================
# UI 與對話管理邏輯
# ==========================================
def render_agent_tab(tools_config):
    st.header("💬 AI Agent (Bedrock Claude)")
    
    # 1. 檢查與初始化 Client
    try:
        client = get_bedrock_client(tools_config)
    except Exception as e:
        st.error(f"⚠️ 初始化 AWS Bedrock 失敗：{e}")
        return

    # 設定模型 ID (依據 AWS Bedrock 實際可用的 Model ID 或 Inference Profile ID)
    MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # 2. 初始化多會話資料結構
    if "agent_sessions" not in st.session_state:
        st.session_state.agent_sessions = {
            "新對話 1": {"ui_messages": [], "api_messages": []}
        }
        st.session_state.current_session_name = "新對話 1"
        st.session_state.session_counter = 1
        st.session_state.last_tools_config_str = json.dumps(tools_config, sort_keys=True)

    current_config_str = json.dumps(tools_config, sort_keys=True)
    if st.session_state.get("last_tools_config_str") != current_config_str:
        st.session_state.last_tools_config_str = current_config_str
        current_session = st.session_state.agent_sessions[st.session_state.current_session_name]
        
        # 情境：已經聊到一半了，自動開啟新對話套用新側邊欄規則
        if len(current_session["ui_messages"]) > 0:
            st.session_state.session_counter += 1
            new_name = f"新對話 {st.session_state.session_counter}"
            st.session_state.agent_sessions[new_name] = {"ui_messages": [], "api_messages": []}
            st.session_state.current_session_name = new_name
            st.toast("🔧 偵測到側邊欄設定變更，已為您自動開啟新對話套用新規則！", icon="✨")

    # 3. 頂部對話選擇器
    col_selector, col_new_btn = st.columns([4, 1])
    with col_selector:
        session_names = list(st.session_state.agent_sessions.keys())
        selected_session = st.selectbox(
            "📁 選擇歷史對話：", 
            options=session_names, 
            index=session_names.index(st.session_state.current_session_name),
            label_visibility="collapsed"
        )
        if selected_session != st.session_state.current_session_name:
            st.session_state.current_session_name = selected_session
            st.rerun()

    with col_new_btn:
        if st.button("➕ 開啟新對話", use_container_width=True):
            st.session_state.session_counter += 1
            new_name = f"新對話 {st.session_state.session_counter}"
            st.session_state.agent_sessions[new_name] = {"ui_messages": [], "api_messages": []}
            st.session_state.current_session_name = new_name
            st.rerun()

    st.divider()

    # 4. 載入當前會話
    current_session = st.session_state.agent_sessions[st.session_state.current_session_name]
    ui_history = current_session["ui_messages"]
    api_history = current_session["api_messages"]

    messages_container = st.container()

    # 渲染歷史對話
    with messages_container:
        for msg in ui_history:
            st.chat_message(msg["role"]).write(msg["content"])

    # 5. 處理使用者輸入
    if user_input := st.chat_input("問問 Crypto Chatbot"):
        
        # 自動重新命名選單
        if len(ui_history) == 0 and st.session_state.current_session_name.startswith("新對話"):
            auto_name = user_input[:10] + "..." if len(user_input) > 10 else user_input
            st.session_state.agent_sessions[auto_name] = st.session_state.agent_sessions.pop(st.session_state.current_session_name)
            st.session_state.current_session_name = auto_name
            current_session = st.session_state.agent_sessions[auto_name]
            ui_history = current_session["ui_messages"]
            api_history = current_session["api_messages"]

        with messages_container:
            # UI 顯示與記錄
            st.chat_message("user").write(user_input)
            ui_history.append({"role": "user", "content": user_input})
            
            # 將使用者輸入加到 API 對話歷史
            api_history.append({"role": "user", "content": user_input})

            with st.chat_message("assistant"):
                with st.status("🧠 AI 思考與處理中...", expanded=True) as status_box:
                    try:
                        # 取得動態 Prompt 與轉換後的 Tools Schema
                        filtered_schema, sys_instruct = get_dynamic_agent_config(tools_config)
                        anthropic_tools = convert_schema_to_anthropic_format(filtered_schema)

                        # 第一次向 Bedrock 提出請求
                        response = client.messages.create(
                            model=MODEL_ID,
                            max_tokens=2048,
                            temperature=0.7,
                            system=sys_instruct,
                            tools=anthropic_tools if anthropic_tools else None,
                            messages=api_history
                        )

                        # 🌟 處理 Anthropic 的 Function Calling 迴圈
                        while response.stop_reason == "tool_use":
                            # 將模型的輸出（包含 tool_use 區塊）記錄進歷史
                            api_history.append({"role": "assistant", "content": response.content})

                            tool_results = []
                            for content_block in response.content:
                                if content_block.type == "tool_use":
                                    func_name = content_block.name
                                    func_args = content_block.input
                                    tool_id = content_block.id

                                    st.write(f"⚙️ **呼叫工具**: `{func_name}`")
                                    st.write(f"🔍 **參數**: `{func_args}`")

                                    # 執行本地 Python Function
                                    exec_result = execute_function_call(func_name, func_args)
                                    st.write("✅ **數據獲取完成**")

                                    # 組裝回傳給 Anthropic 的 tool_result 結構
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": tool_id,
                                        "content": json.dumps(exec_result, ensure_ascii=False)
                                    })

                            # 將工具結果作為 user 角色訊息追加回歷史中
                            api_history.append({"role": "user", "content": tool_results})

                            # 再次呼叫模型
                            response = client.messages.create(
                                model=MODEL_ID,
                                max_tokens=2048,
                                temperature=0.7,
                                system=sys_instruct,
                                tools=anthropic_tools if anthropic_tools else None,
                                messages=api_history
                            )

                        # 工具調用結束，取得最終回答
                        status_box.update(label="分析完成！", state="complete", expanded=False)
                        
                        # 提取純文字回應
                        final_text = ""
                        for block in response.content:
                            if block.type == "text":
                                final_text += block.text

                        # 記錄最後這一次的模型回答到歷史中
                        api_history.append({"role": "assistant", "content": response.content})

                    except Exception as e:
                        status_box.update(label="發生錯誤", state="error")
                        final_text = f"抱歉，處理過程中發生錯誤：{str(e)}"

                # 畫面顯示與 UI 歷史紀錄
                st.write(final_text)
                ui_history.append({"role": "assistant", "content": final_text})