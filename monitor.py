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

    targets = [
        {"name": "グルメ", "base_url": "https://www.hotpepper.jp/gstr00030/newopen/"},
        {"name": "ビューティー", "base_url": "https://beauty.hotpepper.jp/svcSA/stb0020/"}
    ]

    for target in targets:
        for page in range(1, 4):
            if target["name"] == "グルメ":
                url = f"{target['base_url']}page{page}.html" if page > 1 else target["base_url"]
            else:
                url = f"{target['base_url']}PN{page}.html" if page > 1 else target["base_url"]
            
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code != 200: break
            except:
                break

            soup = BeautifulSoup(r.text, "html.parser")
            page_has_shops = False
            
            # --- ① グルメ側のスキャン ---
            if target["name"] == "グルメ":
                for shop_box in soup.find_all("h3", class_="shopListVolShopName"):
                    link_tag = shop_box.find("a")
                    if link_tag:
                        shop_name = link_tag.text.strip()
                        relative_url = link_tag.get("href")
                        if not shop_name or not relative_url: continue
                        page_has_shops = True
                        
                        if shop_name in state or shop_name in new_state: continue
                        
                        shop_url = f"https://www.hotpepper.jp{relative_url}"
                        found_count += 1
                        msg = f"🉐 🔥 **ホットペッパー グルメ新店** 🔥 🉐\n🏪 **店舗名**: {shop_name}\n🔗 **お店のページ**: {shop_url}"
                        send_slack_notification(msg)
                        new_state.append(shop_name)
                        
            # --- ② ビューティー側のスキャン ---
            else:
                for shop_box in soup.find_all(["h3", "div"]):
                    class_str = "".join(shop_box.get("class") or [])
                    if "subSrvHdr" in class_str or "c-tile-product__title" in class_str or "slc-storeName" in class_str or shop_box.name == "h3":
                        link_tag = shop_box.find("a")
                        if link_tag:
                            href = link_tag.get("href") or ""
                            if "/slnH" not in href: continue
                            
                            shop_name = link_tag.text.strip()
                            
                            # 🎯【修正完了】コロン（ : ）をバチッと入れ直しました！
                            if not shop_name or len(shop_name) < 3 or "一覧" in shop_name or "空席" in shop_name: continue
                            page_has_shops = True
                            
                            if shop_name in state or shop_name in new_state: continue
                            
                            shop_url = href if href.startswith("http") else f"https://beauty.hotpepper.jp{href}"
                            
                            found_count += 1
                            msg = f"💅 🔥 **ホットペッパー ビューティー新店** 🔥 💅\n🏪 **店舗名**: {shop_name}\n🔗 **サロンのページ**: {shop_url}"
                            send_slack_notification(msg)
                            new_state.append(shop_name)
            
            if not page_has_shops:
                break
                
    save_state(new_state)
    
    if found_count == 0:
        send_slack_notification(f"🉐 【ホットペッパー監視】グルメ＆ビューティー7分巡回完了 ➔ 【{tokyo_time}】")

if __name__ == "__main__":
    main()
