# app/components/report_generator.py
import markdown
import datetime
import pandas as pd
import json

# 🌟 直接引入繪圖模組，不隱藏錯誤
from app.components.charts import create_candlestick_chart

# ==========================================
# 1. 輔助函式：生成完美適應 HTML 報告的 SVG 半圓儀表圖
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
# 2. 負責排版與產生 HTML (對齊 Chat Tab 的順序與內容)
# ==========================================
def generate_html_report(analysis_result, ai_report_json):
    """
    將分析數據、圖表與新版 AI JSON 報告結構打包成精美的 HTML 檔案
    """
    # 提取 Metadata 與策略資料
    metadata = ai_report_json.get("metadata", {})
    market_assess = ai_report_json.get("market_assessment", {})
    strategy = ai_report_json.get("personalized_strategy", {})
    
    symbol = metadata.get("symbol", analysis_result.get('symbol', 'Unknown')).upper()
    risk_label = strategy.get("risk_profile_label", "未知")
    risk_level = strategy.get("risk_level", 5)
    
    # 處理建議方向與信心指數顏色
    recommendation = market_assess.get("recommendation", "hold").upper()
    confidence = market_assess.get("confidence", 0)
    
    if recommendation == "BUY":
        rec_color = "#22c55e" # 綠色
        rec_text = "買入 (BUY)"
    elif recommendation == "SELL":
        rec_color = "#ef4444" # 紅色
        rec_text = "賣出 (SELL)"
    else:
        rec_color = "#f59e0b" # 橘色
        rec_text = "觀望 (HOLD)"

    # 處理工具設定狀態
    tools_config = analysis_result.get("tools_config", {})
    sentiment_config = tools_config.get("sentiment_tools", {})
    tech_config = tools_config.get("tech_tools", {})
    news_config = tools_config.get("news_tools", {})
    
    # 提取 K 線資料
    kline_res = analysis_result.get('kline_response', {})
    kline_data_dict = kline_res.get('data', {})
    
    latest_kline = {}
    current_interval = "N/A"
    if isinstance(kline_data_dict, dict) and kline_data_dict:
        for interval in ["1d_data", "6h_data", "1h_data", "15m_data"]:
            if interval in kline_data_dict and len(kline_data_dict[interval]) > 0:
                latest_kline = kline_data_dict[interval][-1]
                current_interval = interval.replace("_data", "")
                break

    price = latest_kline.get('close', 0)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ==========================================
    # 1. 📰 新聞報告 (News)
    # ==========================================
    news_html = ""
    news_report = analysis_result.get("news_report")
    if news_config.get("news") and isinstance(news_report, dict):
        news_md = f"**整體情緒:** {news_report.get('overall_sentiment',{}).get('label', '未知')} (分數: {news_report.get('overall_sentiment',{}).get('score', 0)})\n\n"
        news_md += f"**最新摘要:** {news_report.get('summary', '')}\n\n"
        news_md += "**📌 重點事件解析:**\n\n"
        
        for ev in news_report.get('key_events', []):
            impact = "🔴 利空" if ev.get("impact") == "negative" else "🟢 利多"
            # 🌟 修復 1：加入 <br> 換行與顏色標籤，讓每一則新聞獨立且美觀
            news_md += f"- **[{impact}] {ev.get('title')}**<br><span style='color: #64748b; font-size: 0.95em;'>{ev.get('summary')}</span>\n\n"
            
        news_html = f"<h2>📰 新聞分析報告</h2><div class='sub-report-card'>{markdown.markdown(news_md)}</div><hr>"

    # ==========================================
    # 2. 📊 技術指標表格 (Tables)
    # ==========================================
    tables_html = ""
    if any(tech_config.values()) and latest_kline:
        tables_html += "<h2>📊 技術指標數據 (當前快照)</h2><div class='dashboard-tables'>"
        
        if tech_config.get("ma") and latest_kline.get("ma_7") is not None:
            df_ma = pd.DataFrame({'週期': ['MA 7', 'MA 25', 'MA 99'], 
                                  '數值': [f"${latest_kline.get('ma_7',0):,.2f}", 
                                           f"${latest_kline.get('ma_25',0):,.2f}", 
                                           f"${latest_kline.get('ma_99',0):,.2f}"]})
            tables_html += f"<div class='table-card'><h3>移動平均線 (MA)</h3>{df_ma.to_html(index=False, classes='data-table')}</div>"
            
        if tech_config.get("ema") and latest_kline.get("ema_7") is not None:
            df_ema = pd.DataFrame({'週期': ['EMA 7', 'EMA 25', 'EMA 99'], 
                                   '數值': [f"${latest_kline.get('ema_7',0):,.2f}", 
                                            f"${latest_kline.get('ema_25',0):,.2f}", 
                                            f"${latest_kline.get('ema_99',0):,.2f}"]})
            tables_html += f"<div class='table-card'><h3>指數移動平均線 (EMA)</h3>{df_ema.to_html(index=False, classes='data-table')}</div>"
            
        if tech_config.get("bollinger") and latest_kline.get("bb_middle") is not None:
            df_bb = pd.DataFrame({'指標': ['上軌', '中軌', '下軌'], 
                                  '數值': [f"${latest_kline.get('bb_upper',0):,.2f}", 
                                           f"${latest_kline.get('bb_middle',0):,.2f}", 
                                           f"${latest_kline.get('bb_lower',0):,.2f}"]})
            tables_html += f"<div class='table-card'><h3>布林通道 (Bollinger Bands)</h3>{df_bb.to_html(index=False, classes='data-table')}</div>"
            
        indicators_labels = ['當前價格', '時間範圍']
        indicators_values = [f"${price:,.2f}", current_interval]
        if tech_config.get("rsi") and latest_kline.get("rsi") is not None:
            indicators_labels.insert(1, 'RSI')
            indicators_values.insert(1, f"{latest_kline.get('rsi', 0):.2f}")

        df_misc = pd.DataFrame({'指標': indicators_labels, '數值': indicators_values})
        tables_html += f"<div class='table-card'><h3>綜合數據</h3>{df_misc.to_html(index=False, classes='data-table')}</div>"
        tables_html += "</div><hr>"

    # ==========================================
    # 3. 📈 K線圖 (Plotly Charts embedded as HTML)
    # ==========================================
    charts_html = ""
    if any(tech_config.values()) and isinstance(kline_data_dict, dict):
        charts_html += "<h2>📈 多週期互動式 K 線圖</h2><div class='charts-container'>"
        
        intervals = [("15m_data", "超短期 (15m)"), ("1h_data", "短期 (1h)"), 
                     ("6h_data", "中期 (6h)"), ("1d_data", "長期 (1d)")]
                     
        for intv_key, intv_label in intervals:
            data_list = kline_data_dict.get(intv_key, [])
            if data_list:
                df = pd.DataFrame(data_list[-50:]) # 取最近 50 根
                if not df.empty:
                    try:
                        fig = create_candlestick_chart(df, symbol, risk_label)
                        # 🌟 修復 2：設定 include_plotlyjs='cdn' 自動加載 JS，不依賴 HTML header
                        chart_div = fig.to_html(full_html=False, include_plotlyjs='cdn')
                        charts_html += f"<div class='chart-card'><h3>{intv_label}</h3>{chart_div}</div>"
                    except Exception as e:
                        # 🌟 加入錯誤輸出，若畫圖失敗可以直接在報告看到原因
                        charts_html += f"<div class='chart-card'><h3>{intv_label}</h3><p style='color: #ef4444;'>⚠️ 圖表產生失敗: {str(e)}</p></div>"
        charts_html += "</div><hr>"

    # ==========================================
    # 4. 🤖 K線與技術面報告 (Kline Report)
    # ==========================================
    kline_html = ""
    kline_report = analysis_result.get("kline_report")
    if any(tech_config.values()) and isinstance(kline_report, dict):
        k_rec = kline_report.get('recommendation', 'hold').upper()
        kline_md = f"**綜合操作建議:** {k_rec} (信心度: {kline_report.get('confidence', 0)}%)\n\n"
        kline_md += f"**技術摘要:** {kline_report.get('summary', '')}\n\n"
        kline_md += f"**🎯 入場考量:** {kline_report.get('entry_consideration', '')}\n\n"
        kline_md += f"**🚫 判斷失效位:** {kline_report.get('invalidation_level', '')}\n"
        
        kline_html = f"<h2>🤖 技術分析報告</h2><div class='sub-report-card'>{markdown.markdown(kline_md)}</div><hr>"

    # ==========================================
    # 5. 🎯 半圓儀表圖表 (Gauges)
    # ==========================================
    gauges_html = ""
    active_gauges = []
    
    fear_greed_raw = analysis_result.get('fear_greed', [])
    if sentiment_config.get("fear_greed") and fear_greed_raw:
        if isinstance(fear_greed_raw, list) and len(fear_greed_raw) > 0:
            fg_val = float(fear_greed_raw[0].get('value', 50))
        elif isinstance(fear_greed_raw, dict):
            fg_val = float(fear_greed_raw.get('value', 50))
        else:
            fg_val = 50
        active_gauges.append((fg_val, "恐懼貪婪指數"))
        
    social_data = analysis_result.get('long_short', {})
    if sentiment_config.get("long_short") and social_data:
        up_val = float(social_data.get('up', 50))
        active_gauges.append((up_val, "社群看多比例"))
        
    if tech_config.get("rsi") and latest_kline.get("rsi") is not None:
        rsi_val = float(latest_kline.get('rsi', 50))
        active_gauges.append((rsi_val, "RSI 指標"))

    if active_gauges:
        gauges_html += "<h2>🧭 市場情緒指標</h2><div class='dashboard-gauges'>"
        for val, title in active_gauges:
            gauges_html += render_html_gauge(val, title)
        gauges_html += "</div><hr>"

    # ==========================================
    # 6. 🗣️ 社群情緒報告 (Social Report)
    # ==========================================
    social_html = ""
    social_report = analysis_result.get("social_report")
    if (sentiment_config.get("fear_greed") or sentiment_config.get("long_short")) and isinstance(social_report, dict):
        soc_rec = social_report.get('recommendation', 'hold').upper()
        social_md = f"**情緒決策:** {soc_rec} (信心度: {social_report.get('confidence', 0)}%) | **當前狀態:** {social_report.get('sentiment_regime', '')}\n\n"
        social_md += f"**💡 反向指標觀察:** {social_report.get('contrarian_signal', '')}\n\n"
        social_md += f"**摘要:** {social_report.get('summary', '')}\n\n"
        social_md += f"**🚨 失效條件:** {social_report.get('invalidation_level', '')}\n"
        
        social_html = f"<h2>🗣️ 社群情緒分析報告</h2><div class='sub-report-card'>{markdown.markdown(social_md)}</div><hr>"

    # ==========================================
    # 7. 📝 最終 AI 綜合分析與投資建議 (Final Summary)
    # ==========================================
    safe_md_content = ai_report_json.get("report_markdown", "⚠️ 無法取得 AI 報告 Markdown 內容。")
    ai_html_content = markdown.markdown(safe_md_content, extensions=['tables'])

    # ==========================================
    # === 組裝 HTML 模板 ===
    # ==========================================
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
            .meta-info {{ display: flex; justify-content: flex-start; align-items: center; gap: 15px; color: #64748b; margin-top: 15px; font-size: 1.05em; flex-wrap: wrap; }}
            hr {{ border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0; }}
            
            /* Badge 樣式 */
            .badge {{ padding: 6px 16px; border-radius: 20px; font-weight: 600; border: 1px solid; }}
            .badge-default {{ background-color: #eff6ff; color: #2563eb; border-color: #bfdbfe; }}
            .badge-strategy {{ background-color: {rec_color}15; color: {rec_color}; border-color: {rec_color}40; }}
            
            /* 表格與圖表區塊 */
            .dashboard-tables {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 10px; }}
            .table-card {{ background: #f8fafc; padding: 18px; border-radius: 12px; border: 1px solid #e2e8f0; }}
            .table-card h3 {{ margin-top: 0; margin-bottom: 12px; font-size: 1.05em; color: #334155; }}
            .data-table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }}
            .data-table th, .data-table td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; font-size: 0.95em; }}
            .data-table th {{ background-color: #f1f5f9; color: #475569; font-weight: 600; }}
            
            /* K 線圖容器 */
            .charts-container {{ display: flex; flex-direction: column; gap: 20px; }}
            .chart-card {{ background: #ffffff; padding: 10px; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
            .chart-card h3 {{ margin-top: 0; padding: 10px; color: #334155; font-size: 1.1em; background: #f8fafc; border-bottom: 1px solid #e2e8f0; margin-bottom: 0; }}
            
            /* 半圓儀表盤卡片 */
            .dashboard-gauges {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin-bottom: 10px; }}
            .html-gauge-card {{ background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
            .gauge-title {{ font-weight: 700; font-size: 1.1em; color: #334155; margin-bottom: 15px; }}
            .gauge-svg-container {{ position: relative; width: 180px; margin: 0 auto; }}
            .gauge-svg {{ width: 100%; height: auto; }}
            .gauge-value {{ position: absolute; bottom: 10px; left: 0; right: 0; font-size: 1.8em; font-weight: 800; text-align: center; }}
            .gauge-status {{ margin-top: 8px; font-size: 0.9em; font-weight: 600; color: #64748b; }}
            
            /* AI 子報告與總結卡片 */
            .sub-report-card {{ background: #f8fafc; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; font-size: 0.95em; }}
            .sub-report-card ul {{ margin-top: 5px; padding-left: 20px; }}
            .sub-report-card li {{ margin-bottom: 8px; }}
            .ai-content {{ margin-top: 40px; background: #ffffff; padding: 30px; border-radius: 12px; border: 1px solid #cbd5e1; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
            .ai-content h2 {{ color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; display: inline-block; margin-top: 0; }}
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
                    <span class="badge badge-strategy">策略方向：{rec_text} (信心 {confidence}%)</span>
                    <span class="badge badge-default">風險偏好：{risk_label} (Lv.{risk_level})</span>
                </div>
            </div>
            
            <!-- 模塊：依次插入對齊 UI 的報告與圖表 -->
            {news_html}
            {tables_html}
            {charts_html}
            {kline_html}
            {gauges_html}
            {social_html}
            
            <!-- 最終大總結 -->
            <div class="ai-content">
                <h2>📝 最終 AI 綜合分析與投資建議</h2>
                {ai_html_content}
            </div>
            
            <div style="margin-top: 50px; text-align: center; color: #94a3b8; font-size: 0.85em; border-top: 1px solid #f1f5f9; padding-top: 20px;">
                <p>⚠️ 免責聲明：本報告由 AI 自動生成，內含數據與圖表僅供學習與策略參考，不構成任何實質投資建議。Model: {metadata.get("model", "N/A")}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template