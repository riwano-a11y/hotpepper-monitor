import os
import requests
import json

WEBHOOK = os.environ.get("SLACK_WEBHOOK")
RECRUIT_API_KEY = os.environ.get("RECRUIT_API_KEY")
STATE_FILE = "hotpepper_monitor_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f: json.dump(state, f, indent=4)
    except: pass

def send_slack_notification(message):
    if not WEBHOOK: return
    payload = {"text": message}
    try: requests.post(WEBHOOK, json=payload, timeout=10)
    except: pass

def main():
    if not RECRUIT_API_KEY:
        print("APIキーが金庫に設定されていません")
        return

    # 🎯 秘密のAPIキーを使って、リクルートの公式サーバーからデータを直接引っこ抜きます
    url = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"
    params = {
        "key": RECRUIT_API_KEY,
        "keyword": "OPEN 新着", # 最新のオープン情報を狙い撃ち
        "count": 10,
        "format": "json"
    }
    
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200: return
        data = r.json()
    except:
        return

    shops = data.get("results", {}).get("shop", [])
    state = load_state()
    new_state = state.copy()
    
    found_count = 0
    for shop in shops:
        shop_id = shop.get("id")
        shop_name = shop.get("name")
        shop_url = shop.get("urls", {}).get("pc")
        catch_phrase = shop.get("catch", "新着オープン店舗です！")
        
        if not shop_id or not shop_url:
            continue
            
        if shop_id in state:
            continue
            
        found_count += 1
        # 🎉 公式データを使った超リッチな確定レイアウト通知！
        msg = (
            f"🔥 🉐 **ホットペッパー 新店オープン検知（公式API版）** 🉐 🔥\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏪 **店舗名**: {shop_name}\n"
            f"📝 **キャッチ**: {catch_phrase}\n"
            f"🔗 **ショップページ**: {shop_url}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        send_slack_notification(msg)
        new_state.append(shop_id)
        
    save_state(new_state)
    print(f"APIによる検知店舗数: {found_count}")

if __name__ == "__main__":
    main()
