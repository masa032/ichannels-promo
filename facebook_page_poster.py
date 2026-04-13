import os
import json
import glob
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DRAFT_DIR = os.path.join(BASE_DIR, "drafts")
IMAGES_DIR = os.path.join(BASE_DIR, "images", "hanryul")
SITE_URL = "https://hanryul32.github.io/promo/life/"
FACEBOOK_PAGE_URL = "https://www.facebook.com/gogo.buy.it/"
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")


def load_latest_records():
    files = sorted(glob.glob(os.path.join(LOGS_DIR, "log_*.json")))
    if files:
        with open(files[-1], "r", encoding="utf-8") as f:
            return json.load(f)
    # Fallback: 從 campaigns.json 直接讀取（獨立路徑，不需先跑 run_campaign.py）
    campaigns_path = os.path.join(BASE_DIR, "campaigns.json")
    if os.path.exists(campaigns_path):
        with open(campaigns_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [
            {
                "brand": c["brand"],
                "category": c["category"],
                "copy": c.get("desc", ""),
                "affiliate_link": c.get("url", ""),
                "highlight": c.get("highlight", ""),
            }
            for c in data.get("campaigns", []) if c.get("active", True)
        ]
    return []


def build_post(records):
    top = records[:3]
    items = []
    for record in top:
        hl = (record.get("highlight") or record.get("copy", ""))[:35]
        line = f"- {record['brand']}"
        if hl:
            line += f"：{hl}"
        items.append(line)

    intro = "今天幫大家整理了幾個我自己會先點開看的優惠，先把值得逛的放在這裡，省點比價時間。"
    body = "\n".join(items)
    close = f"\n\n想看完整整理可以直接逛這裡：{SITE_URL}\n也歡迎追蹤粉絲頁一起挖好物：{FACEBOOK_PAGE_URL}"
    return intro + "\n\n" + body + close


def save_draft(message):
    os.makedirs(DRAFT_DIR, exist_ok=True)
    with open(os.path.join(DRAFT_DIR, "facebook_post.txt"), "w", encoding="utf-8") as f:
        f.write(message)


def pick_image():
    """輪播選取圖片：依照今天是第幾天（mod 總張數）選圖，無圖則回傳 None"""
    if not os.path.isdir(IMAGES_DIR):
        return None
    exts = (".jpg", ".jpeg", ".png", ".webp")
    images = sorted([
        os.path.join(IMAGES_DIR, f)
        for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith(exts)
    ])
    if not images:
        return None
    day_index = datetime.now().timetuple().tm_yday  # 1-365
    return images[day_index % len(images)]


def post_to_facebook(message):
    import requests
    if not FACEBOOK_PAGE_ID or not FACEBOOK_PAGE_ACCESS_TOKEN:
        print("[Facebook] 未設定 PAGE_ID / ACCESS_TOKEN，已僅產生草稿")
        return False

    image_path = pick_image()

    if image_path and os.path.exists(image_path):
        # 使用 /photos 端點上傳圖片貼文
        url = f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/photos"
        print(f"[Facebook] 附上圖片: {os.path.basename(image_path)}")
        with open(image_path, "rb") as img_file:
            mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
            resp = requests.post(
                url,
                data={
                    "message": message,
                    "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
                },
                files={"source": (os.path.basename(image_path), img_file, mime)},
                timeout=60,
            )
    else:
        # 無圖片：純文字 + 連結
        url = f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/feed"
        resp = requests.post(
            url,
            data={
                "message": message,
                "link": SITE_URL,
                "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
            },
            timeout=20,
        )

    print(f"[Facebook] HTTP {resp.status_code}")
    if resp.status_code == 200:
        print("[Facebook] 貼文發佈成功")
        return True
    print(resp.text[:400])
    return False


def main():
    records = load_latest_records()
    if not records:
        print("[Facebook] 無最新 log，略過")
        return
    message = build_post(records)
    save_draft(message)
    post_to_facebook(message)


if __name__ == "__main__":
    main()