import os
import requests
import json
from bs4 import BeautifulSoup

# GitHubの金庫からSlackのURLを読み込みます
WEBHOOK = os.environ.get("SLACK_WEBHOOK")
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
    # 🎯 ホットペッパー公式の「ニューオープン（新着店舗）」一覧ページを直接狙い撃ちします
    url = "https://www.hotpepper.jp/gstr00001/new_open/" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"アクセス失敗: {r.status_code}")
            return
    except Exception as e:
        print(f"エラー: {e}")
        return

    soup = BeautifulSoup(r.text, "html.parser")
    state = load_state()
    new_state = state.copy()
    
    # 🎯 2026年現在のホットペッパー店舗カードの目印（クラス名）を徹底スキャン
    # リンク（aタグ）の中から店舗個別ページ（/strXXXXX/）をすべて抜き出します
    links = soup.find_all("a")
    found_count = 0
    
    for link in links:
        href = link.get("href", "")
        
        # 店舗個別ページのURLだけを綺麗に抽出します
        if "/str" in href and "new_open" not in href and "report" not in href and "map" not in href:
            if href.startswith("/"):
                shop_url = f"https://www.hotpepper.jp{href}"
            else:
                shop_url = href
                
            # URLの後ろについている余計な文字（?ジャンル等）をカットして綺麗にします
            shop_url = shop_url.split("?")[0]
            
            # 店舗名（テキスト）を取得
            shop_name = link.text.strip()
            # 空っぽのものや、写真リンクなどの余計なテキストはスルー
            if not shop_name or len(shop_name) < 3 or "店" not in shop_name and "無料" in shop_name:
                continue
                
            # すでに通知済みのURLならスルーします
            if shop_url in state:
                continue
                
            found_count += 1
            # 🎉 ホットペッパー専用の可愛い100点満点レイアウトで通知！
            msg = (
                f"🔥 🉐 **ホットペッパー 新店オープン検知** 🉐 🔥\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏪 **店舗名**: {shop_name}\n"
                f"🔗 **ショップページ**: {shop_url}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            send_slack_notification(msg)
            new_state.append(shop_url)
            
    save_state(new_state)
    print(f"検知した新着店舗数: {found_count}")

if __name__ == "__main__":
    main()
