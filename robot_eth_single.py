import datetime
import json
import os
from boll_eth import BollStrategy
from my_telegram import send_telegram

STATUS_FILE = "eth_status.json"
CONFIG_FILE = "config.json"

# ==========================================
# 讀取設定檔與狀態檔
# ==========================================
def load_config():
    # 預設參數
    default_config = {
        "symbol": "ETHUSDT",
        "times": 5,
        "windows": 25,
        "dev": 2.2,
        "narrow": 0.06,
        "slop": 0.001,
        "slop_rate": 0.75
    }
    
    # 如果找不到 config.json，就自動建立一份並寫入預設值
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        print(f"⚠️ 找不到 {CONFIG_FILE}，已自動建立並載入預設參數。")
        return default_config
        
    # 如果檔案存在，就正常讀取
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_status(default_slop):
    if not os.path.exists(STATUS_FILE):
        return {
            "order_exist": False,
            "quantity": 0,
            "money": 0,
            "slop": default_slop,
            "open_time": None
        }
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {
                "order_exist": False,
                "quantity": 0,
                "money": 0,
                "slop": default_slop,
                "open_time": None
            }

def save_status(status):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=4)

# ==========================================
# 主程式
# ==========================================
def main():
    # 1. 讀取外部參數
    try:
        cfg = load_config()
    except Exception as e:
        print(str(e))
        return

    # 2. 讀取機器人狀態
    status = load_status(default_slop=cfg["slop"])
    
    logs = []
    error_msg = ""

    def log(msg):
        logs.append(str(msg))

    try:
        # 3. 初始化策略 (參數全部由 config 和 env 動態餵入)
        strategy = BollStrategy(
            symbol=cfg["symbol"], 
            key="", 
            secret="",
            narrow=cfg["narrow"],
            slop=status.get("slop", cfg["slop"]),
            windows=cfg["windows"],
            dev=cfg["dev"]
        )

        # 復原狀態
        strategy.order_exist = status.get("order_exist", False)
        strategy.quantity = status.get("quantity", 0)
        strategy.money = status.get("money", 0)
        strategy.open_time = status.get("open_time", None)

        strategy.data.end = datetime.datetime.now()
        
        # 從 Binance API 再次確認實際艙位數量 (雙重確認防呆)
        binance_quantity = strategy.binance.get_position(cfg["symbol"])
        if binance_quantity:
            strategy.order_exist = True
            strategy.quantity = binance_quantity
        else:
            strategy.order_exist = False
            strategy.quantity = 0

        # --- 判斷邏輯開始 ---
        if not strategy.order_exist: # 尚未入場
            if strategy.detect_in():
                strategy.money = strategy.binance.get_money()
                strategy.order_exist = True
                
                try:
                    current_price = float(strategy.data.kline_date.iloc[-2]['bb_upper']) # 保險起見用倒數第二根已收盤的軌道
                    money_to_use = float(strategy.binance.get_money()) * cfg["times"]
                    strategy.quantity = round(money_to_use / current_price, 2)
                    strategy.open_time = strategy.data.kline_date.iloc[-1].get('open_time')
                    
                    log(f"觸發入場條件，準備買入數量: {strategy.quantity}")
                    
                    strategy.binance.market_order(symbol=strategy.symbol, side="BUY", quantity=strategy.quantity)
                    log("入場成功！")
                except Exception as e:
                    error_msg = f"入場失敗--{str(e)}"
                    log(error_msg)
                    strategy.open_time = None
                    strategy.order_exist = False
                    strategy.quantity = 0
            else:
                log("未觸發入場條件。")

        else: # 已入場
            if strategy.detect_out():
                current_time = strategy.data.kline_date.iloc[-1].get('open_time')
                if strategy.open_time != current_time:
                    try:
                        log(f"觸發出場條件，準備賣出數量: {strategy.quantity}")
                        strategy.binance.market_order(symbol=strategy.symbol, side="SELL", quantity=strategy.quantity)
                        log("出場成功！")
                        
                        strategy.open_time = None
                        strategy.quantity = 0
                        strategy.order_exist = False
                        
                        # 動態調整 slop (使用 config 裡的 slop_rate)
                        current_money = float(strategy.binance.get_money())
                        if float(strategy.money) > current_money:
                            strategy.slop = cfg["slop"] * cfg["slop_rate"]
                            log(f"虧損出場，Slop 調整為 {strategy.slop}")
                        else:
                            strategy.slop = cfg["slop"]
                            log(f"獲利出場，Slop 恢復為 {strategy.slop}")

                    except Exception as e:
                        error_msg = f"出場失敗--{str(e)}"
                        log(error_msg)
                else:
                    log("當前K線與入場K線為同一根，不執行出場。")
            else:
                log("未觸發出場條件。")

        if hasattr(strategy, 'debug_msg') and strategy.debug_msg:
            log(strategy.debug_msg)

    except Exception as e:
        error_msg = f"⚠️執行發生例外錯誤: {str(e)}"
        log(error_msg)

    finally:
        # 將最新的狀態存回檔案
        if 'strategy' in locals():
            status["order_exist"] = strategy.order_exist
            status["quantity"] = strategy.quantity
            status["money"] = strategy.money
            status["slop"] = strategy.slop
            status["open_time"] = strategy.open_time
            save_status(status)

        # 整理 Telegram 訊息
        msg_lines = []
        msg_lines.append("========= 執行狀態 =========")
        msg_lines.append(f"時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if 'strategy' in locals():
            msg_lines.append(f"入場狀態: {strategy.order_exist}")
            msg_lines.append(f"持倉數量: {strategy.quantity}")
            msg_lines.append(f"當前 narrow: {strategy.narrow}")
            msg_lines.append(f"當前 slop: {strategy.slop}")
        else:
            msg_lines.append("狀態: 策略初始化失敗")
            
        msg_lines.append("===========================")
        
        if logs:
            msg_lines.append("執行紀錄:")
            for l in logs:
                msg_lines.append(f"{l}")

        final_message = "\n".join(msg_lines)
        
        # 發送 Telegram
        try:
            send_telegram(final_message)
        except Exception as e:
            with open("error_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Telegram 發送失敗: {e}\n")

if __name__ == '__main__':
    main()