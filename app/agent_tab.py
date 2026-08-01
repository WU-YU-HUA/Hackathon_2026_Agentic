import streamlit as st
import json
import os
from google import genai
from google.genai import types
from api import TOOL_MAP, TOOLS_SCHEMA

# ==========================================
# 🌟 動態解析側邊欄設定，生成專屬 Schema 與 Prompt
# ==========================================
def get_dynamic_agent_config(tools_config):
    """根據 sidebar 的勾選狀態，動態過濾工具並產生系統提示"""
    
    # 1. 讀取側邊欄傳入的三大分類設定
    enabled_news = tools_config.get("news_tools", {})
    enabled_sentiment = tools_config.get("sentiment_tools", {})
    enabled_tech = tools_config.get("tech_tools", {})
    
    filtered_schema = []
    allowed_api_names = ["get_allowed_symbol"]  # 白名單查詢工具永遠開啟
    
    # 📰 新聞面工具 (包含即時新聞與 AI 分析)
    if enabled_news.get("news"):
        allowed_api_names.extend(["get_crypto_news", "get_news_ai_analysis"])
        
    # 👥 社群情緒工具 (對齊 TOOLS_SCHEMA 真實 Name)
    if enabled_sentiment.get("fear_greed"):
        allowed_api_names.append("get_vote_feargreed")
        
    if enabled_sentiment.get("long_short"):
        allowed_api_names.append("get_social_ai_analysis")
        
    # 📈 技術指標工具 (包含純數據與 K 線 AI 分析)
    if any(enabled_tech.values()):
        allowed_api_names.extend(["get_technical_data", "get_kline_ai_analysis"])
        
    # 過濾出 Gemini 能呼叫的 Tool Schema
    for tool in TOOLS_SCHEMA:
        if tool["function"]["name"] in allowed_api_names:
            filtered_schema.append(tool)
            
    # 2. 建立動態 System Prompt
    allowed_metrics_names = []
    if enabled_news.get("news"): 
        allowed_metrics_names.append("加密貨幣即時新聞與新聞 AI 分析")
    if enabled_sentiment.get("fear_greed"): 
        allowed_metrics_names.append("恐懼貪婪指數")
    if enabled_sentiment.get("long_short"): 
        allowed_metrics_names.append("社群多空投票與情緒 AI 分析")
    if enabled_tech.get("bollinger"): 
        allowed_metrics_names.append("布林通道 (Bollinger Bands)")
    if enabled_tech.get("rsi"): 
        allowed_metrics_names.append("RSI")
    if enabled_tech.get("ma"): 
        allowed_metrics_names.append("MA (移動平均線)")
    if enabled_tech.get("ema"): 
        allowed_metrics_names.append("EMA")
    
    # 將使用者的限制寫入系統提示詞
    sys_instruct = (
        "你是一個專業的加密貨幣量化分析師。請善用工具來獲取即時數據與進行 AI 分析。\n\n"
        "【⚠️ 最高指令限制】\n"
        f"使用者目前在控制面板中，『僅允許』你使用與分析以下指標與功能：{', '.join(allowed_metrics_names)}。\n"
        "即使 API 工具回傳了其他未經允許的數據，你都必須『假裝沒看到』，絕對不能在回答中主動提及未勾選的指標。\n"
        "若使用者詢問了未勾選的指標或功能，請禮貌地提醒他：「您尚未在側邊欄開啟該功能，請開啟後再詢問」。"
    )
    
    return filtered_schema, sys_instruct

# ==========================================
# 核心功能與工具綁定
# ==========================================
def convert_schema_to_genai_format(tools_schema):
    """將 tools schema 轉換為 Google GenAI 格式"""
    function_declarations = []
    for tool in tools_schema:
        if tool.get("type") == "function":
            func_def = tool["function"]
            function_declarations.append(
                types.FunctionDeclaration(
                    name=func_def["name"],
                    description=func_def["description"],
                    parameters=func_def["parameters"]
                )
            )
    return [types.Tool(function_declarations=function_declarations)] if function_declarations else []

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

def init_gemini_chat(api_key, tools_config):
    """初始化全新的 Gemini Chat Session"""
    if "gemini_client" not in st.session_state:
        st.session_state.gemini_client = genai.Client(api_key=api_key)
        
    client = st.session_state.gemini_client
    
    # 取得過濾後的 Schema 與動態 Prompt
    filtered_schema, sys_instruct = get_dynamic_agent_config(tools_config)
    
    # 轉換為 Gemini Tools 格式
    tools = convert_schema_to_genai_format(filtered_schema)
    
    chat = client.chats.create(
        model='gemini-flash-latest',
        config=types.GenerateContentConfig(
            tools=tools if tools else None,
            temperature=0.7,
            system_instruction=sys_instruct
        )
    )
    return chat

# ==========================================
# UI 與對話管理邏輯
# ==========================================
def render_agent_tab(tools_config):
    """渲染自由對話 Agent 介面"""
    st.header("💬 AI Agent")
    
    # 取得 API Key
    api_key = tools_config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.warning("⚠️ 請先在左側邊欄輸入 Gemini API Key 或設定環境變數。")
        return

    # 1. 初始化多會話資料結構
    if "agent_sessions" not in st.session_state:
        st.session_state.agent_sessions = {
            "新對話 1": {"messages": [], "gemini_chat": init_gemini_chat(api_key, tools_config)}
        }
        st.session_state.current_session_name = "新對話 1"
        st.session_state.session_counter = 1
        st.session_state.last_tools_config_str = json.dumps(tools_config, sort_keys=True)

    # 偵測側邊欄勾選狀態是否變更
    current_config_str = json.dumps(tools_config, sort_keys=True)
    if st.session_state.get("last_tools_config_str") != current_config_str:
        st.session_state.last_tools_config_str = current_config_str
        current_session = st.session_state.agent_sessions[st.session_state.current_session_name]
        
        # 情境 A：當前聊天室若無歷史紀錄，無痛更新 Chat
        if len(current_session["messages"]) == 0:
            current_session["gemini_chat"] = init_gemini_chat(api_key, tools_config)
            
        # 情境 B：若已有對話，自動開啟新對話套用新設定
        else:
            st.session_state.session_counter += 1
            new_name = f"新對話 {st.session_state.session_counter}"
            st.session_state.agent_sessions[new_name] = {
                "messages": [], 
                "gemini_chat": init_gemini_chat(api_key, tools_config)
            }
            st.session_state.current_session_name = new_name
            st.toast("🔧 偵測到側邊欄設定變更，已自動為您開啟新對話並套用新規則！", icon="✨")
            st.rerun()

    # 2. 頂部對話管理介面
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
            st.session_state.agent_sessions[new_name] = {
                "messages": [], 
                "gemini_chat": init_gemini_chat(api_key, tools_config)
            }
            st.session_state.current_session_name = new_name
            st.rerun()

    st.divider()

    # 3. 載入當前選定對話資料
    current_session = st.session_state.agent_sessions[st.session_state.current_session_name]
    chat_history = current_session["messages"]
    gemini_chat = current_session["gemini_chat"]

    messages_container = st.container()

    # 渲染歷史對話
    with messages_container:
        for msg in chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

    # 4. 處理使用者輸入
    if user_input := st.chat_input("問問 Crypto Chatbot"):
        
        # 新對話第一次輸入時，自動重命名為問題前 10 個字
        if len(chat_history) == 0 and st.session_state.current_session_name.startswith("新對話"):
            auto_name = user_input[:10] + "..." if len(user_input) > 10 else user_input
            st.session_state.agent_sessions[auto_name] = st.session_state.agent_sessions.pop(st.session_state.current_session_name)
            st.session_state.current_session_name = auto_name
            current_session = st.session_state.agent_sessions[auto_name]
            chat_history = current_session["messages"]

        with messages_container:
            st.chat_message("user").write(user_input)
            chat_history.append({"role": "user", "content": user_input})

            with st.chat_message("assistant"):
                with st.status("🧠 AI 思考與處理中...", expanded=True) as status_box:
                    try:
                        response = gemini_chat.send_message(user_input)
                        
                        # 處理 Function Calling 循環
                        while response.function_calls:
                            for func_call in response.function_calls:
                                func_name = func_call.name
                                func_args = func_call.args
                                
                                st.write(f"⚙️ **呼叫工具**: `{func_name}`")
                                st.write(f"🔍 **參數**: `{dict(func_args)}`")
                                
                                result = execute_function_call(func_name, func_args)
                                st.write("✅ **數據獲取完成**")
                                
                                response = gemini_chat.send_message(
                                    types.Part.from_function_response(
                                        name=func_name,
                                        response=result
                                    )
                                )
                        
                        status_box.update(label="分析完成！", state="complete", expanded=False)
                        final_text = response.text

                    except Exception as e:
                        status_box.update(label="發生錯誤", state="error")
                        final_text = f"抱歉，處理過程中發生錯誤：{str(e)}"
                
                st.write(final_text)
                chat_history.append({"role": "assistant", "content": final_text})