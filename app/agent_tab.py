import streamlit as st
import json
import os
from google import genai
from google.genai import types
from api import TOOL_MAP, TOOLS_SCHEMA

# ==========================================
# 🌟 新增：動態解析側邊欄設定，生成專屬 Schema 與 Prompt
# ==========================================
def get_dynamic_agent_config(tools_config):
    """根據 sidebar 的勾選狀態，動態過濾工具並產生系統提示"""
    print(tools_config)
    enabled_sentiment = tools_config.get("sentiment_tools", {})
    enabled_tech = tools_config.get("tech_tools", {})
    
    # 1. 過濾 TOOLS_SCHEMA (控制 AI 能呼叫哪些 API)
    filtered_schema = []
    allowed_api_names = ["get_allowed_symbol"] # 白名單查詢工具永遠開啟
    
    if enabled_sentiment.get("fear_greed"):
        allowed_api_names.append("get_fear_and_greed")
        
    if enabled_sentiment.get("long_short"):
        allowed_api_names.append("get_social_sentiment")
        
    # 只要有勾選任何一個技術指標，就允許呼叫技術分析 API
    if any(enabled_tech.values()):
        allowed_api_names.append("get_technical_data")
        
    for tool in TOOLS_SCHEMA:
        if tool["function"]["name"] in allowed_api_names:
            filtered_schema.append(tool)
            
    # 2. 建立動態 System Prompt (控制 AI 回答的內容限制)
    allowed_metrics_names = []
    if enabled_sentiment.get("fear_greed"): allowed_metrics_names.append("恐懼貪婪指數")
    if enabled_sentiment.get("long_short"): allowed_metrics_names.append("多空投票比")
    if enabled_tech.get("bollinger"): allowed_metrics_names.append("布林通道(Bollinger Bands)")
    if enabled_tech.get("rsi"): allowed_metrics_names.append("RSI")
    if enabled_tech.get("ma"): allowed_metrics_names.append("MA (移動平均線)")
    if enabled_tech.get("ema"): allowed_metrics_names.append("EMA")
    
    # 將使用者的限制寫入最高指導原則
    sys_instruct = (
        "你是一個專業的加密貨幣量化分析師。請善用工具來獲取即時數據。\n\n"
        "【⚠️ 最高指令限制】\n"
        f"使用者目前在控制面板中，『僅允許』你使用與分析以下指標：{', '.join(allowed_metrics_names)}。\n"
        "即使你的 API 工具回傳了其他未經允許的數據，你都必須『假裝沒看到』，絕對不能在回答中主動提及未勾選的指標。"
        "若使用者直接詢問了未勾選的指標，請禮貌地提醒他：「您尚未在側邊欄開啟該指標功能，請開啟後再詢問」。"
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
    return [types.Tool(function_declarations=function_declarations)]

def execute_function_call(function_name, function_args):
    """執行本地工具"""
    if function_name in TOOL_MAP:
        try:
            args_dict = dict(function_args) if function_args else {}
            result = TOOL_MAP[function_name](**args_dict)
            return result if isinstance(result, dict) else {"result": result}
        except Exception as e:
            return {"error": str(e)}
    return {"error": f"Unknown function: {function_name}"}

# 🌟 修改：將 tools_config 傳入，讓初始化時能吃到最新的設定
def init_gemini_chat(api_key, tools_config):
    """初始化全新的 Gemini Chat Session (具備獨立記憶與連線保護)"""
    
    # 確保 client 存入 session_state，避免被 Python 回收關閉連線
    if "gemini_client" not in st.session_state:
        st.session_state.gemini_client = genai.Client(api_key=api_key)
        
    client = st.session_state.gemini_client
    
    # 🌟 取得過濾後的 Schema 與動態 Prompt
    filtered_schema, sys_instruct = get_dynamic_agent_config(tools_config)
    
    # 轉換成 Google 需要的格式 (現在傳入的是瘦身版的 schema)
    tools = convert_schema_to_genai_format(filtered_schema)
    
    chat = client.chats.create(
        model='gemini-flash-latest',  # 使用最新的 flash 模型指標
        config=types.GenerateContentConfig(
            tools=tools,
            temperature=0.7,
            system_instruction=sys_instruct
        )
    )
    return chat

# ==========================================
# UI 與對話管理邏輯
# ==========================================
def render_agent_tab(tools_config):
    """渲染自由對話 Agent 介面 (支援多重對話紀錄與正確的排版)"""
    st.header("💬 AI Agent")
    
    # 取得 API Key
    api_key = tools_config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.warning("⚠️ 請先在左側邊欄輸入 Gemini API Key 或設定環境變數。")
        return

    # 1. 初始化多會話資料結構 (🌟 將 tools_config 傳給 init_gemini_chat)
    if "agent_sessions" not in st.session_state:
        st.session_state.agent_sessions = {
            "新對話 1": {"messages": [], "gemini_chat": init_gemini_chat(api_key, tools_config)}
        }
        st.session_state.current_session_name = "新對話 1"
        st.session_state.session_counter = 1
        st.session_state.last_tools_config_str = json.dumps(tools_config, sort_keys=True)

    current_config_str = json.dumps(tools_config, sort_keys=True)
    if st.session_state.get("last_tools_config_str") != current_config_str:
        # 設定已經改變，更新記憶
        st.session_state.last_tools_config_str = current_config_str
        
        current_session = st.session_state.agent_sessions[st.session_state.current_session_name]
        
        # 情境 A：如果當前聊天室是空的，直接在背景「無痛換腦」
        if len(current_session["messages"]) == 0:
            current_session["gemini_chat"] = init_gemini_chat(api_key, tools_config)
            
        # 情境 B：如果已經聊到一半了，保留舊歷史，自動開啟新對話來套用新規則
        else:
            st.session_state.session_counter += 1
            new_name = f"新對話 {st.session_state.session_counter}"
            st.session_state.agent_sessions[new_name] = {
                "messages": [], 
                "gemini_chat": init_gemini_chat(api_key, tools_config)
            }
            st.session_state.current_session_name = new_name
            # 在畫面右下角彈出漂亮的小通知
            st.toast("🔧 偵測到側邊欄設定變更，已為您自動開啟新對話套用新規則！", icon="✨")
            
    # 2. 頂部對話管理介面
    col_selector, col_new_btn = st.columns([4, 1])
    
    with col_selector:
        # 下拉選單切換歷史對話
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
        # 新增對話按鈕 (🌟 開新對話時，根據側邊欄設定重塑 AI 性格)
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

    # 3. 載入當前選定對話的資料
    current_session = st.session_state.agent_sessions[st.session_state.current_session_name]
    chat_history = current_session["messages"]
    gemini_chat = current_session["gemini_chat"]

    # 關鍵修復：建立獨立的訊息容器，確保對話輸入框永遠置底
    messages_container = st.container()

    # 將歷史訊息寫入容器中
    with messages_container:
        for msg in chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

    # 4. 處理使用者輸入
    if user_input := st.chat_input("問問 Crypto Chatbot"):
        
        # [加分體驗] 如果是新對話的第一次輸入，自動將對話重新命名為問題的前10個字
        if len(chat_history) == 0 and st.session_state.current_session_name.startswith("新對話"):
            auto_name = user_input[:10] + "..." if len(user_input) > 10 else user_input
            # 搬移字典 Key
            st.session_state.agent_sessions[auto_name] = st.session_state.agent_sessions.pop(st.session_state.current_session_name)
            st.session_state.current_session_name = auto_name
            current_session = st.session_state.agent_sessions[auto_name]
            chat_history = current_session["messages"]

        # 將新的使用者對話與 AI 回應也強制渲染在容器中
        with messages_container:
            # 顯示並儲存使用者訊息
            st.chat_message("user").write(user_input)
            chat_history.append({"role": "user", "content": user_input})

            with st.chat_message("assistant"):
                with st.status("🧠 AI 思考與處理中...", expanded=True) as status_box:
                    try:
                        # 傳送訊息給當前專屬的 Gemini Chat 物件
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
                
                # 顯示最終回答並儲存
                st.write(final_text)
                chat_history.append({"role": "assistant", "content": final_text})