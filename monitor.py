import os
import requests
import json

# GitHubの金庫からSlackのURLとリクルートのAPIキーを読み込みます
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
        print("APIキーが設定されていません")
        return

    # 🎯 ホットペッパーのグルメ店検索APIを叩きます（新着順で最大20件取得）
    # ※ start=1, count=20 で最新の20件を引っ張ります
    url = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"
    params = {
        "key": RECRUIT_API_KEY,
        "keyword": "OPEN", # 「OPEN」や「新着」などのキーワードで絞り込み（自由に変えられます）
        "order": 4,        # 4 = おすすめ順（または新着順に近い動きをするものに設定）
        "count": 20,
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
    
    for shop in shops:
        shop_id = shop.get("id")
        shop_name = shop.get("name")
        shop_url = shop.get("urls", {}).get("pc")
        catch_phrase = shop.get("catch", "") # お店のキャッチコピー
        open_info = shop.get("open", "")     # 営業時間やオープン情報
        
        if not shop_id or not shop_url:
            continue
            
        # すでに通知済みの店舗（ID）ならスルー
        if shop_id in state:
            continue
            
        # 🎉 ホットペッパー公式APIデータを使った、超リッチな通知レイアウト！
        msg = (
            f"🔥 🉐 **ホットペッパー 新店・新着検知（公式API版）** 🉐 🔥\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏪 **店舗名**: {shop_name}\n"
            f"📝 **キャッチ**: {catch_phrase}\n"
            f"📅 **オープン情報/営業**: {open_info}\n"
            f"🔗 **ショップページ**: {shop_url}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        send_slack_notification(msg)
        new_state.append(shop_id) # URLの代わりに確実なリクルート独自の店舗IDで記憶します
        
    save_state(new_state)

if __name__ == "__main__":
    main()
