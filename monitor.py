import os
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

WEBHOOK = os.environ.get("SLACK_WEBHOOK")
STATE_FILE = "monitor_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
    except:
        pass

def send_slack_notification(message):
    if not WEBHOOK: return
    payload = {"text": message}
    try: requests.post(WEBHOOK, json=payload, timeout=10)
    except: pass

def main():
    tokyo_time = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%H:%M:%S')
    url = "https://www.hotpepper.jp/gstr00030/newopen/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            send_slack_notification(f"🉐 【ホットペッパー】巡回完了（サイト混雑）➔ 【{tokyo_time}】")
            return
    except:
        send_slack_notification(f"🉐 【ホットペッパー】巡回完了（通信混雑）➔ 【{tokyo_time}】")
        return

    soup = BeautifulSoup(r.text, "html.parser")
    state = load_state()
    new_state = state.copy()
    
    found_count = 0
    # 🎯 センサー強化：新店名の目印を網羅
    for tag in soup.find_all(["h3", "div", "span"]):
        if tag.get("class") and any("ShopName" in c or "shopName" in c for c in tag.get("class")):
            shop_name = tag.text.strip()
            if not shop_name or len(shop_name) < 2: continue
            if shop_name in state or shop_name in new_state: continue
            
            found_count += 1
            msg = f"🉐 🔥 **ホットペッパー 新店検知** 🔥 🉐\n🏪 **店舗名**: {shop_name}"
            send_slack_notification(msg)
            new_state.append(shop_name)
            
    save_state(new_state)
    if found_count == 0:
        send_slack_notification(f"🉐 【ホットペッパー監視】7分定期巡回完了 ➔ タイムスタンプ: 【{tokyo_time}】")

if __name__ == "__main__":
    main()
