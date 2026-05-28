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
    tokyo_time = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%H:%M:%S')
    state = load_state()
    new_state = state.copy()
    found_count = 0
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    # 🎯 確実に新着が載っているメインページだけを一撃必殺で狙い撃ち（余計なページめくりはしない）
    targets = [
        {"name": "グルメ", "url": "https://www.hotpepper.jp/gstr00030/newopen/"},
        {"name": "ビューティー", "url": "https://beauty.hotpepper.jp/svcSA/stb0020/"}
    ]

    for target in targets:
        try:
            r = requests.get(target["url"], headers=headers, timeout=15)
            if r.status_code != 200: continue
        except:
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        
        # --- ① グルメ側の超高速スキャン ---
        if target["name"] == "グルメ":
            for shop_box in soup.find_all("h3", class_="shopListVolShopName"):
                link_tag = shop_box.find("a")
                if link_tag:
                    shop_name = link_tag.text.strip()
                    relative_url = link_tag.get("href")
                    if not shop_name or not relative_url: continue
                    if shop_name in state or shop_name in new_state: continue
                    
                    shop_url = f"https://www.hotpepper.jp{relative_url}"
                    found_count += 1
                    msg = f"🉐 🔥 **ホットペッパー グルメ新店** 🔥 🉐\n🏪 **店舗名**: {shop_name}\n🔗 **お店のページ**: {shop_url}"
                    send_slack_notification(msg)
                    new_state.append(shop_name)
                    
        # --- ② ビューティー側の超高速スキャン ---
        else:
            # ページ内のすべてのリンクから、サロン詳細（/slnH）だけを光速でぶっこ抜く！
            for link_tag in soup.find_all("a", href=True):
                href = link_tag.get("href")
                if "/slnH" in href and "catalog" not in href and "coupon" not in href:
                    shop_name = link_tag.text.strip()
                    
                    # ナビゲーションや無駄なゴミ文字、重複を完全にシャットアウト
                    if not shop_name or len(shop_name) < 3 or any(x in shop_name for x in ["一覧", "空席", "検索", "メニュー", "ヘア", "スタイル", "こだわり"]): continue
                    if shop_name in state or shop_name in new_state: continue
                    
                    shop_url = href if href.startswith("http") else f"https://beauty.hotpepper.jp{href}"
                    found_count += 1
                    msg = f"💅 🔥 **ホットペッパー ビューティー新店** 🔥 💅\n🏪 **店舗名**: {shop_name}\n🔗 **サロンのページ**: {shop_url}"
                    send_slack_notification(msg)
                    new_state.append(shop_name)
                    
    save_state(new_state)
    
    # 本当に完全新規が0件だった時だけ完了報告
    if found_count == 0:
        send_slack_notification(f"🉐 【ホットペッパー監視】グルメ＆ビューティー7分巡回完了 ➔ 【{tokyo_time}】")

if __name__ == "__main__":
    main()
