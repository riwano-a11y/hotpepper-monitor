import os
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime # 🛠️【追加】時間を計算する部品を呼び出す
import pytz # 🛠️【追加】日本時間を正確に測る部品

WEBHOOK = os.environ.get("SLACK_WEBHOOK")
STATE_FILE = "hotpepper_monitor_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try: with open(STATE_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_state(state):
    try: with open(STATE_FILE, "w") as f: json.dump(state, f, indent=4)
    except: pass

def send_slack_notification(message):
    if not WEBHOOK: return
    payload = {"text": message}
    try: requests.post(WEBHOOK, json=payload, timeout=10)
    except: pass

def main():
    url = "https://www.hotpepper.jp/gstr00001/new_open/" 
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: return
    except: return

    soup = BeautifulSoup(r.text, "html.parser")
    state = load_state()
    new_state = state.copy()
    
    links = soup.find_all("a")
    found_count = 0
    
    for link in links:
        href = link.get("href", "")
        if "/str" in href and not any(x in href for x in ["new_open", "report", "map", "photo", "course", "review"]):
            if href.startswith("/"): shop_url = f"https://www.hotpepper.jp{href}"
            else: shop_url = href
            shop_url = shop_url.split("?")[0].rstrip("/") + "/"
            
            if shop_url in state or shop_url in new_state: continue
            shop_name = link.text.strip()
            if not shop_name or len(shop_name) < 3 or any(x in shop_name for x in ["無料", "写真", "クーポン"]): continue
                
            found_count += 1
            msg = f"🔥 🉐 **ホットペッパー 新店オープン検知** 🉐 🔥\n🏪 **店舗名**: {shop_name}\n🔗 {shop_url}"
            send_slack_notification(msg)
            new_state.append(shop_url)
            
    save_state(new_state)
    
    # 🛠️【大改造】現在の日本時間を「○時○分○秒」の形でゲットする
    tokyo_time = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%H:%M:%S')
    
    if found_count == 0:
        # 🎯 文章の末尾に毎回違う時間をくっつけることで、GitHubのエコ機能を一撃でブチ破る！
        send_slack_notification(f"🟢 【ホットペッパー監視】定期巡回完了（正常稼働中） ➔ タイムスタンプ: 【{tokyo_time}】")

if __name__ == "__main__":
    main()
