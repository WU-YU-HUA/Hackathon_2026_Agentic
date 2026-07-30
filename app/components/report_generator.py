# app/components/report_generator.py
import markdown
import datetime
import pandas as pd
from google import genai

# ==========================================
# 1. 負責 Prompt Engineering 與獲取 AI 報告
# ==========================================
def generate_ai_report_markdown(analysis_result, api_key):
    """
    接收分析數據，組裝 Prompt，並回傳 AI 產生的 Markdown 報告
    """
    symbol = analysis_result.get('symbol', 'Unknown')
    risk_level = analysis_result.get('risk_level', 'Conservative')
    
    multi_timeframe_data = analysis_result.get('multi_timeframe', analysis_result.get('tech_data'))
    custom_strategy = analysis_result.get('custom_bb_strategy', '尚未提供')
    fear_greed = analysis_result.get('fear_greed', '無數據')
    social = analysis_result.get('social', '無數據')
    
    prompt = f"""
    【⚠️ 系統最高級別強制指令】
    你是一個純粹的數據分析輸出引擎。
    絕對禁止輸出任何人類問候語、自我介紹、或前言結語！
    禁止出現：「尊敬的投資者」、「您好」、「作為一位...」、「我將為您...」等廢話。
    你的回覆必須、立刻、直接從「### 1. 市場趨勢總結」這幾個字開始！

    【使用者背景】
    - 選擇幣種：{symbol}
    - 風險偏好：{risk_level} (請務必嚴格根據此風險等級調整你的資金分配與止損建議)
    
    【多維度市場數據】
    1. 技術面 (短期1h、中期6h、長期1d)：
    {multi_timeframe_data}
    
    2. 獨家布林通道策略訊號：
    {custom_strategy}
    
    3. 情緒面：
    - 恐懼貪婪指數：{fear_greed}
    - CoinGecko 多空比：{social}
    
    【報告輸出格式要求】
    請嚴格按照以下架構，使用 Markdown 格式輸出：
    
    ### 1. 市場趨勢總結
    (綜合評估目前的多空力道與情緒面狀況)
    
    ### 2. 多維度時間框架分析 
    * **短期 (1h 線)**：...
    * **中期 (6h 線)**：...
    * **長期 (1d 線)**：...
    
    ### 3. 具體操作建議表 (基於 {risk_level} 風險)
    請務必連同「表頭」與「分隔線」完整輸出以下 Markdown 表格：

    | 決策指標 | 具體建議數值與行動 |
    | :--- | :--- |
    | **建議方向** | (填寫：買入 / 做空 / 觀望) |
    | **資金分配** | (建議佔總資產 %) |
    | **建倉區間** | (請給出具體價格) |
    | **止贏目標** | (請給出具體價格) |
    | **止損防守** | (請給出具體價格) |
    | **分批時機** | (針對 {risk_level} 風險的加碼或減倉條件) |
    """
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt,
        )
        if response.text:
            return response.text
        else:
            return "❌ AI 未回傳任何文字，可能是遭到 Google API 安全過濾器阻擋。"
    except Exception as e:
        return f"❌ 產生報告時發生錯誤：{str(e)}"

# ==========================================
# 輔助函式：生成完美適應 HTML 報告的 SVG 半圓儀表圖
# ==========================================
def render_html_gauge(value, title):
    """產出 100% 原生 Vector SVG 儀表盤，解決 Plotly 在外打包 HTML 時的排版破圖問題"""
    try:
        val = float(value)
    except:
        val = 50.0
    val = max(0.0, min(100.0, val))
    
    # 計算半圓角度 (0 到 180 度)
    angle = (val / 100.0) * 180
    
    # 判斷顏色狀態
    if val < 30:
        color_class = "#ef4444" # 紅色
        status_text = "極度恐懼 / 看空"
    elif val < 45:
        color_class = "#f97316" # 橘色
        status_text = "恐懼"
    elif val < 60:
        color_class = "#eab308" # 黃色
        status_text = "中立"
    elif val < 75:
        color_class = "#84cc16" # 淺綠
        status_text = "貪婪"
    else:
        color_class = "#22c55e" # 綠色
        status_text = "極度貪婪 / 看多"

    svg_code = f"""
    <div class="html-gauge-card">
        <div class="gauge-title">{title}</div>
        <div class="gauge-svg-container">
            <svg viewBox="0 0 200 120" class="gauge-svg">
                <!-- 背景灰弧線 -->
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#e2e8f0" stroke-width="16" stroke-linecap="round"/>
                <!-- 數值彩色弧線 (使用 stroke-dasharray 模擬) -->
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="{color_class}" stroke-width="16" stroke-linecap="round"
                      stroke-dasharray="{angle * 2.51} 500"/>
            </svg>
            <div class="gauge-value" style="color: {color_class};">{val:.1f}</div>
        </div>
        <div class="gauge-status">{status_text}</div>
    </div>
    """
    return svg_code

# ==========================================
# 2. 負責排版與產生 HTML
# ==========================================
def generate_html_report(analysis_result, ai_summary_md):
    """
    將分析數據、圖表與 AI 總結打包成精美的 HTML 檔案
    """
    symbol = analysis_result.get('symbol', 'Unknown')
    risk = analysis_result.get('risk_level', 'Unknown')
    
    tools_config = analysis_result.get("tools_config", {})
    sentiment_config = tools_config.get("sentiment_tools", {})
    tech_config = tools_config.get("tech_tools", {})
    
    tech_data = analysis_result.get('tech_data', {})
    fear_greed_data = analysis_result.get('fear_greed', {})
    social_data = analysis_result.get('social', {})
    price = tech_data.get('price', 0) if isinstance(tech_data, dict) else 0
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ==========================================
    # === A. 產生表格區塊的 HTML ===
    # ==========================================
    tables_html = ""
    if any(tech_config.values()) and isinstance(tech_data, dict):
        tables_html += "<h2>📊 技術指標數據</h2><div class='dashboard-tables'>"
        
        # 1. MA 表格
        if tech_config.get("ma") and tech_data.get('ma'):
            ma = tech_data['ma']
            df_ma = pd.DataFrame({'週期': ['MA 7', 'MA 25', 'MA 99'], '數值': [f"${ma.get('ma_7',0):,.2f}", f"${ma.get('ma_25',0):,.2f}", f"${ma.get('ma_99',0):,.2f}"]})
            tables_html += f"<div class='table-card'><h3>移動平均線 (MA)</h3>{df_ma.to_html(index=False, classes='data-table')}</div>"
            
        # 2. EMA 表格
        if tech_config.get("ema") and tech_data.get('ema'):
            ema = tech_data['ema']
            df_ema = pd.DataFrame({'週期': ['EMA 7', 'EMA 25', 'EMA 99'], '數值': [f"${ema.get('ema_7',0):,.2f}", f"${ema.get('ema_25',0):,.2f}", f"${ema.get('ema_99',0):,.2f}"]})
            tables_html += f"<div class='table-card'><h3>指數移動平均線 (EMA)</h3>{df_ema.to_html(index=False, classes='data-table')}</div>"
            
        # 3. 布林通道表格
        if tech_config.get("bollinger") and tech_data.get('bollinger_bands'):
            bb = tech_data['bollinger_bands']
            df_bb = pd.DataFrame({'指標': ['上軌', '中軌', '下軌'], '數值': [f"${bb.get('upper',0):,.2f}", f"${bb.get('middle',0):,.2f}", f"${bb.get('lower',0):,.2f}"]})
            tables_html += f"<div class='table-card'><h3>布林通道 (Bollinger Bands)</h3>{df_bb.to_html(index=False, classes='data-table')}</div>"
            
        # 4. 綜合數據表格
        indicators_labels = ['當前價格']
        indicators_values = [f"${price:,.2f}"]
        
        if tech_config.get("rsi") and tech_data.get('rsi'):
            indicators_labels.append('RSI')
            indicators_values.append(f"{tech_data.get('rsi', {}).get('value', 0):.2f}")
            
        indicators_labels.append('時間範圍')
        indicators_values.append(str(tech_data.get('interval', 'N/A')))

        df_misc = pd.DataFrame({'指標': indicators_labels, '數值': indicators_values})
        tables_html += f"<div class='table-card'><h3>綜合數據</h3>{df_misc.to_html(index=False, classes='data-table')}</div>"
            
        tables_html += "</div>"

    # ==========================================
    # === B. 產生圖表區塊的 HTML (改用超完美原生 SVG 儀表盤) ===
    # ==========================================
    gauges_html = ""
    active_gauges = []
    
    if sentiment_config.get("fear_greed") and fear_greed_data:
        fg_val = fear_greed_data.get('value', 50) if isinstance(fear_greed_data, dict) else 50
        active_gauges.append((fg_val, "恐懼貪婪指數"))
        
    if sentiment_config.get("long_short") and social_data:
        up_val = social_data.get('up', 50)
        active_gauges.append((up_val, "社群看多比例"))
        
    if tech_config.get("rsi") and tech_data.get("rsi"):
        rsi_val = tech_data.get('rsi', {}).get('value', 50)
        active_gauges.append((rsi_val, "RSI 指標"))

    if active_gauges:
        gauges_html += "<h2>🧭 市場情緒指標</h2><div class='dashboard-gauges'>"
        for val, title in active_gauges:
            gauges_html += render_html_gauge(val, title)
        gauges_html += "</div><hr>"

    # === C. 將 AI Markdown 轉為 HTML ===
    safe_md_content = ai_summary_md if ai_summary_md is not None else "⚠️ 無法取得 AI 報告內容，產生過程中斷。"
    ai_html_content = markdown.markdown(safe_md_content, extensions=['tables'])

    # === D. HTML 模板 ===
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{symbol} 量化分析報告</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 1000px; margin: 0 auto; padding: 40px 20px; background-color: #f8fafc; }}
            .report-card {{ background: #ffffff; padding: 40px; border-radius: 16px; box-shadow: 0 4px 20px -2px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
            .header {{ border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; color: #0f172a; font-size: 2.2em; font-weight: 700; }}
            .meta-info {{ display: flex; justify-content: flex-start; align-items: center; gap: 20px; color: #64748b; margin-top: 15px; font-size: 1.05em; flex-wrap: wrap; }}
            .badge {{ background-color: #eff6ff; color: #2563eb; padding: 6px 16px; border-radius: 20px; font-weight: 600; border: 1px solid #bfdbfe; }}
            
            /* 表格區塊 Grid */
            .dashboard-tables {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .table-card {{ background: #f8fafc; padding: 18px; border-radius: 12px; border: 1px solid #e2e8f0; }}
            .table-card h3 {{ margin-top: 0; margin-bottom: 12px; font-size: 1.05em; color: #334155; }}
            .data-table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }}
            .data-table th, .data-table td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; font-size: 0.95em; }}
            .data-table th {{ background-color: #f1f5f9; color: #475569; font-weight: 600; }}
            
            /* 🌟 自訂純 HTML 儀表盤卡片 (保證不破圖、清晰可見) */
            .dashboard-gauges {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .html-gauge-card {{ background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
            .gauge-title {{ font-weight: 700; font-size: 1.1em; color: #334155; margin-bottom: 15px; }}
            .gauge-svg-container {{ position: relative; width: 180px; margin: 0 auto; }}
            .gauge-svg {{ width: 100%; height: auto; }}
            .gauge-value {{ position: absolute; bottom: 10px; left: 0; right: 0; font-size: 1.8em; font-weight: 800; text-align: center; }}
            .gauge-status {{ margin-top: 8px; font-size: 0.9em; font-weight: 600; color: #64748b; }}
            
            /* AI 報告文字區 */
            .ai-content {{ margin-top: 40px; }}
            .ai-content h2 {{ color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; display: inline-block; }}
            .ai-content h3 {{ color: #1e293b; margin-top: 25px; }}
            .ai-content table {{ width: 100%; border-collapse: collapse; margin: 20px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 0 0 1px #e2e8f0; }}
            .ai-content th, .ai-content td {{ border: 1px solid #e2e8f0; padding: 12px 15px; text-align: left; }}
            .ai-content th {{ background-color: #f8fafc; font-weight: 600; color: #334155; }}
            .ai-content tr:nth-child(even) {{ background-color: #fefefe; }}
        </style>
    </head>
    <body>
        <div class="report-card">
            <div class="header">
                <h1>{symbol} AI 量化投資報告</h1>
                <div class="meta-info">
                    <span><strong>分析時間：</strong>{current_date}</span>
                    <span><strong>當前價格：</strong>${price:,.2f}</span>
                    <span class="badge">風險偏好：{risk}</span>
                </div>
            </div>
            
            <!-- 插入 Dashboard 圖表與數據 -->
            {gauges_html}
            {tables_html}
            
            <div class="ai-content">
                <h2>📝 AI 綜合分析與投資建議</h2>
                {ai_html_content}
            </div>
            
            <div style="margin-top: 50px; text-align: center; color: #94a3b8; font-size: 0.85em; border-top: 1px solid #f1f5f9; padding-top: 20px;">
                <p>⚠️ 免責聲明：本報告由 AI 自動生成，內含數據與圖表僅供學習與策略參考，不構成任何實質投資建議。</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template