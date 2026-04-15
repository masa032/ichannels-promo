import os
import json
import glob
import random
from datetime import datetime
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DRAFT_DIR = os.path.join(BASE_DIR, "drafts")
IMAGES_DIR = os.path.join(BASE_DIR, "images", "hanryul")
SITE_URL = "https://hanryul32.github.io/promo/life/"
FACEBOOK_PAGE_URL = "https://www.facebook.com/hanryul.daily/"
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")

LIFESTYLE_TIPS = [
    "今日美肌小提醒 ✨\n\n防曬！防曬！防曬！\n不管晴天雨天，這一步都不能省。\n\n今天防曬了嗎？",
    "韓式保養的核心秘訣 💆‍♀️\n\n「保濕」才是一切的基礎。\n就算只做一件事，補水就夠了！",
    "今天的能量補給 ☀️\n\n工作累了就喝杯水、伸展一下，\n再難的事情拆成一小步就好。\n\n我們一起撐過去！",
    "放鬆一下 🧘‍♀️\n\n今天有沒有讓自己快樂的時刻？\n記得留一點時間給自己，\n10分鐘就夠 ✨",
    "美麗秘訣 💄\n\n讓人覺得美的，不只是外型，是狀態！\n今天的你，狀態如何？😊",
    "換季提醒 🌿\n\n保濕、防曬、修護這三樣記得補貨！\n有整理好的優惠都在這裡 👉 " + SITE_URL,
    "每週一問 💬\n\n最近在用哪些保養品？\n留言告訴我，一起交流心得 😊",
]


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


def load_funny_videos():
    """從 funny_videos.json 讀取作用中的影片清單"""
    path = os.path.join(BASE_DIR, "funny_videos.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        videos = json.load(f)
    return [v for v in videos if v.get("active", True)]


def build_video_post(video):
    prefixes = [
        "給大家補充下午的快樂能量 😄",
        "今天刷到這個，笑到不行 😂",
        "工作累了嗎？來補充一下 ☀️",
        "今日療癒時間 🥹",
        "笑一笑，今天過得去 😊",
        "分享私藏，超好笑！🤣",
    ]
    prefix = random.choice(prefixes)
    caption = video.get("caption", "")
    return f"{prefix}\n\n{caption}\n\n追蹤我讓每天都有好心情：{FACEBOOK_PAGE_URL}"


def build_lifestyle_post():
    tip = random.choice(LIFESTYLE_TIPS)
    return tip + f"\n\n更多分享追蹤這裡：{FACEBOOK_PAGE_URL}"


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
    if not FACEBOOK_PAGE_ID or not FACEBOOK_PAGE_ACCESS_TOKEN:
        print("[Facebook] 未設定 PAGE_ID / ACCESS_TOKEN，已僅產生草稿")
        return False

    # 優先：用 Gemini Imagen 3 自動生成情境照片
    image_bytes, image_mime = None, None
    try:
        from auto_generate_image import generate_image
        image_bytes, image_mime = generate_image()
    except Exception as e:
        print(f"[ImageGen] 略過自動生成: {e}")

    if image_bytes:
        # 使用 /photos 端點上傳 AI 生成圖片
        url = f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/photos"
        print("[Facebook] 附上 AI 生成照片")
        import io
        resp = requests.post(
            url,
            data={
                "message": message,
                "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
            },
            files={"source": ("hanryul_daily.png", io.BytesIO(image_bytes), image_mime)},
            timeout=90,
        )
    else:
        # Fallback：本機輪播照片
        image_path = pick_image()
        if image_path and os.path.exists(image_path):
            url = f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/photos"
            print(f"[Facebook] 附上本機照片: {os.path.basename(image_path)}")
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


def post_link(message, url):
    """發文字＋連結貼文（適合影片分享、生活提醒）"""
    if not FACEBOOK_PAGE_ID or not FACEBOOK_PAGE_ACCESS_TOKEN:
        print("[Facebook] 未設定 PAGE_ID / ACCESS_TOKEN，已僅產生草稿")
        return False
    endpoint = f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/feed"
    resp = requests.post(
        endpoint,
        data={
            "message": message,
            "link": url,
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
    hour_utc = datetime.utcnow().hour

    # 發文時段分配（以 UTC 小時判斷）：
    #  UTC 00-04 (台北 08-12) → 早安商品推薦 + 圖片
    #  UTC 05-10 (台北 13-18) → 娛樂：影片分享或生活小提醒
    #  UTC 11-16 (台北 19-00) → 晚間商品推薦
    if 5 <= hour_utc < 11:
        # 娛樂 / 互動時段
        videos = load_funny_videos()
        if videos:
            video = random.choice(videos)
            message = build_video_post(video)
            save_draft(message)
            post_link(message, video["url"])
        else:
            message = build_lifestyle_post()
            save_draft(message)
            post_link(message, SITE_URL)
    else:
        # 商品推薦時段（早上 / 晚上）
        records = load_latest_records()
        if not records:
            print("[Facebook] 無最新 log，略過")
            return
        message = build_post(records)
        save_draft(message)
        post_to_facebook(message)


if __name__ == "__main__":
    main()