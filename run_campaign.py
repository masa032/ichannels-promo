# ==============================================================================
# run_campaign.py — 全自動推廣主控執行器 v3.0 (0成本最大收益版)
# 功能：AI生成獨特文案 -> 分潤連結 -> SEO最佳化HTML + Sitemap + 結構化資料
# 帳號：masatsai032@gmail.com / af000094185
# 0成本策略：Gemini免費額度 + GitHub Pages免費部署 + Windows排程自動化
# ==============================================================================

import os
import sys
import json
import random
import urllib.parse
import requests
from datetime import datetime
from dotenv import load_dotenv

# Windows cp950 終端機 emoji 相容修正
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

GEMINI_API_KEY       = os.environ.get("GEMINI_API_KEY", "")
ICHANNELS_AFFILIATE_ID = os.environ.get("ICHANNELS_AFFILIATE_ID", "af000094185")
WEBHOOK_URL          = os.environ.get("WEBHOOK_URL", "")

CAMPAIGNS_FILE = os.path.join(BASE_DIR, "campaigns.json")
OUTPUT_DIR     = os.path.join(BASE_DIR, "output")
LOGS_DIR       = os.path.join(BASE_DIR, "logs")
LIFE_DIR       = os.path.join(OUTPUT_DIR, "life")
HTML_FILE      = os.path.join(LIFE_DIR, "index.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR,   exist_ok=True)
os.makedirs(LIFE_DIR,   exist_ok=True)

# ── Gemini 初始化（有 Key 才啟用）──────────────────────────────────────────
ai_client = None
if GEMINI_API_KEY and GEMINI_API_KEY != "請填入您的_GEMINI_API_KEY":
    try:
        from google import genai
        from google.genai import types
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        print("[AI] ✅ Gemini AI 已就緒")
    except ImportError:
        print("[AI] ⚠️  google-genai 未安裝，請執行: pip install google-genai")
else:
    print("[AI] ℹ️  未設定 GEMINI_API_KEY，將使用內建備用文案範本")


# ── 核心函式 ─────────────────────────────────────────────────────────────────

def load_campaigns() -> list:
    with open(CAMPAIGNS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [c for c in data["campaigns"] if c.get("active")]


def make_affiliate_link(url: str, uid: str) -> str:
    """在原始 URL 追加 ic= 與 uid= 聯盟追蹤參數。"""
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    params["ic"]  = [ICHANNELS_AFFILIATE_ID]
    params["uid"] = [uid]
    new_query = urllib.parse.urlencode(params, doseq=True)
    return urllib.parse.urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, new_query, parsed.fragment
    ))


# 文案角度輪流，讓 Google 不認為重複內容（SEO重點）
_COPY_ANGLES = [
    "從使用者親身體驗角度出發，150-250字，重點說用完的真實感受與改變",
    "從解決生活痛點角度出發，150-250字，先講困擾再帶出商品解方",
    "從限時優惠稀缺感角度出發，150-250字，製造緊迫感促進立即行動",
    "從送禮推薦角度出發，150-250字，適合節慶送禮的理由與產品優點",
    "從CP值比較角度出發，150-250字，說明為何這是市場上最值得買的選擇",
]


def ai_write_copy(brand: str, name: str, desc: str, category: str) -> str:
    """呼叫 Gemini 以隨機角度生成獨特推廣文案，避免每次重複。"""
    if ai_client:
        from google.genai import types
        angle = random.choice(_COPY_ANGLES)
        prompt = f"""你是台灣頂級聯盟行銷文案師。
請為以下品牌撰寫一篇 Facebook／LINE 群組高轉換率推廣貼文。

要求：
1. 繁體中文台灣口語，不要像廣告，要像真人心得
2. 適度使用 Emoji（不要每句都用）
3. 寫作角度：{angle}
4. 結尾必須有明確 CTA（Call to Action）
5. 禁止使用「我要分享」「超值好物」「必買」這類陳腔濫調開頭

品牌：{brand}
活動名稱：{name}
商品特色：{desc}
類別：{category}"""
        try:
            resp = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.92, max_output_tokens=500)
            )
            response_text = getattr(resp, "text", "") or ""
            if response_text.strip():
                return response_text.strip()
            print("[AI] ⚠️  Gemini 回傳空內容，改用範本")
        except BaseException as e:
            print(f"[AI] ⚠️  Gemini 呼叫失敗: {e}，改用範本")

    # 備用範本（有 API 時不會走到這）
    templates = {
        "購物商城":    f"🛒 【{brand}】近期優惠真的很實在～\n{desc}\n\n手刀點連結查看👇，錯過要等很久！🔥",
        "3C家電":      f"📱 科技控注意！【{brand}】現在正是入手時機！\n{desc}\n\n點連結查看最新優惠👇",
        "美容保養/服飾精品": f"✨ 【{brand}】用過就回不去了～\n{desc}\n\n手刀點連結搶購👇 庫存有限！💄",
        "教育學習":    f"📚 【{brand}】投資自己最划算！\n{desc}\n\n趁特價趕快入手👇 投資自己最實在💡",
        "休閒旅遊":    f"✈️ 【{brand}】旅遊優惠登場！\n{desc}\n\n點連結查看行程👇 訂越早越便宜！🏖️",
        "美食保健":    f"🍽️ 【{brand}】吃過一次就愛上！\n{desc}\n\n點連結搶購👇 值得長期回購！😋",
    }
    return templates.get(category, f"🌟 【{brand}】限時優惠！\n{desc}\n\n點連結馬上查看👇")


def publish_to_webhook(post_text: str, link: str) -> None:
    """推播至 Webhook（未設定則跳過）。"""
    if not WEBHOOK_URL or WEBHOOK_URL.strip() == "":
        return
    try:
        payload = {
            "text": f"{post_text}\n\n👉 立即查看：\n{link}",
            "timestamp": datetime.now().isoformat()
        }
        resp = requests.post(
            WEBHOOK_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        if resp.status_code in [200, 204]:
            print("[Webhook] 🎉 推播成功")
        else:
            print(f"[Webhook] ⚠️  狀態碼 {resp.status_code}")
    except Exception as e:
        print(f"[Webhook] ❌ 推播失敗: {e}")


def save_log(records: list) -> None:
    log_path = os.path.join(LOGS_DIR, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[系統] 📝 推廣紀錄 → {os.path.basename(log_path)}")


def generate_html_page(records: list) -> None:
        """生成更像人氣購物推薦站的 SEO 靜態 HTML + Sitemap + robots。"""
        now_str = datetime.now().strftime("%Y/%m/%d %H:%M")
        iso_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
        site_url = "https://hanryul32.github.io/promo/life/"
        facebook_page_url = "https://www.facebook.com/gogo.buy.it/"

        category_colors = {
            "購物商城": "#e84876",
            "3C家電": "#1c6dd0",
            "教育學習": "#2f855a",
            "美容保養/服飾精品": "#8b5cf6",
            "美容保養_服飾精品": "#8b5cf6",
            "休閒旅遊": "#0ea5e9",
            "美食保健": "#f97316",
        }
        category_icons = {
            "購物商城": "🛍️",
            "3C家電": "📱",
            "教育學習": "🎓",
            "美容保養/服飾精品": "👗",
            "美容保養_服飾精品": "👗",
            "休閒旅遊": "✈️",
            "美食保健": "🍱",
        }
        domain_map = {
            "momo": "momoshop.com.tw",
            "蝦皮": "shopee.tw",
            "博客來": "books.com.tw",
            "dyson": "dyson.com.tw",
            "Dyson": "dyson.com.tw",
            "小米": "mi.com",
            "Xiaomi": "mi.com",
            "Nike": "nike.com",
            "Hahow": "hahow.in",
            "Klook": "klook.com",
            "KKday": "kkday.com",
            "Agoda": "agoda.com",
            "快車": "kuaiche.com.tw",
            "白蘭氏": "brandsworld.com.tw",
        }

        def escape_html(value: str) -> str:
            return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def brand_domain(name: str) -> str:
            for keyword, domain in domain_map.items():
                if keyword in name:
                    return domain
            return "example.com"

        # JSON-LD
        jsonld = json.dumps({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "每日精選好物特惠",
            "description": "嚴選合作品牌最新優惠，天天更新，幫你找到最值得入手的好物。",
            "dateModified": iso_date,
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index + 1,
                    "name": record["brand"],
                    "url": record["affiliate_link"],
                }
                for index, record in enumerate(records)
            ],
        }, ensure_ascii=False)

        cards_html = ""
        for record in records:
            safe_copy = escape_html(record["copy"]).replace("\n", "<br>")
            safe_brand = escape_html(record["brand"])
            safe_category = escape_html(record["category"])
            card_color = category_colors.get(record["category"], "#c2185b")
            card_icon = category_icons.get(record["category"], "🏷️")
            category_id = record["category"].replace("/", "_")
            favicon = f"https://www.google.com/s2/favicons?domain={brand_domain(record['brand'])}&sz=128"
            hero_image = record.get("asset_image") or record.get("image") or favicon
            card_badge = record.get("badge", "")
            card_tags = record.get("tags") or ["官方通路", "熱門優惠", "每日整理"]
            card_highlight = record.get("highlight", "")
            card_cta = record.get("cta_text") or "立即查看優惠"
            badge_html = f'<span class="promo-badge">{escape_html(card_badge)}</span>' if card_badge else ""
            tags_html = "".join(f"<span>{escape_html(t)}</span>" for t in card_tags)
            highlight_html = f'<p class="card-highlight">💡 {escape_html(card_highlight)}</p>' if card_highlight else ""

            cards_html += f"""
  <article class="card" id="{category_id}" itemscope itemtype="https://schema.org/Product">
    <div class="card-cover" style="--card-color:{card_color}">
      <img class="cover-bg-img" src="{hero_image}" alt="" loading="lazy" aria-hidden="true" onerror="this.style.display='none'">
      <div class="cover-scrim"></div>
      <div class="cover-top">
        <img class="cover-icon" src="{favicon}" alt="{safe_brand}" loading="lazy" onerror="this.style.display='none'">
        {badge_html}
      </div>
      <span class="cat-pill">{card_icon} {safe_category}</span>
    </div>
    <div class="card-body">
      <h2 itemprop="name">{safe_brand}</h2>
      <div class="mini-tags">{tags_html}</div>
      {highlight_html}
      <div class="copy" itemprop="description">{safe_copy}</div>
      <div class="trust-row">
        <span>✅ 真品保障</span>
        <span>🔒 安心連結</span>
        <span>💳 定價透明</span>
      </div>
      <a class="btn" href="{record['affiliate_link']}" target="_blank" rel="sponsored noopener">
        {card_cta}
      </a>
    </div>
  </article>"""

        categories = sorted(set(record["category"] for record in records))
        cat_nav = "".join(
            f'<a href="#{category.replace("/", "_")}" style="border-color:{category_colors.get(category, "#c2185b")};color:{category_colors.get(category, "#c2185b")}">{category_icons.get(category, "🏷️")} {category}</a>'
            for category in categories
        )

        host_avatar = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="72" height="72">
  <circle cx="50" cy="50" r="50" fill="#ff7a45"/>
  <circle cx="50" cy="36" r="18" fill="#ffe0bd"/>
  <ellipse cx="50" cy="82" rx="27" ry="22" fill="#ffe0bd"/>
  <circle cx="43" cy="35" r="3" fill="#2d2d2d"/>
  <circle cx="57" cy="35" r="3" fill="#2d2d2d"/>
  <path d="M42 46 Q50 54 58 46" fill="none" stroke="#d9480f" stroke-width="3" stroke-linecap="round"/>
  <circle cx="42" cy="42" r="4" fill="#ffcabd" opacity=".8"/>
  <circle cx="58" cy="42" r="4" fill="#ffcabd" opacity=".8"/>
</svg>
"""

        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="韓律的生活美學筆記｜分享日常穿搭、喜歡的物品、照片與心情。歡迎一起享受美好的小事。">
<meta name="keywords" content="韓律,Han Ryul,생활,穿搭日誌,好物分享,生活美學,日常記錄">
<meta property="og:title" content="韓律 Han Ryul | 生活美學與日常分享">
<meta property="og:description" content="韓律的生活美學筆記｜分享日常穿搭、喜歡的物品、照片與心情。">
<meta property="og:type" content="website">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{site_url}index.html">
<title>韓律 Han Ryul | 生活美學與日常分享</title>
<script type="application/ld+json">{jsonld}</script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Noto Sans TC',system-ui,sans-serif;background:linear-gradient(180deg,#fff7f8 0%,#f6f8fc 100%);color:#222;line-height:1.65}}
a{{color:inherit;text-decoration:none}}
header{{position:relative;overflow:hidden;background:linear-gradient(135deg,#e83e70 0%,#ff8a34 100%);color:#fff;padding:3.2rem 1.2rem 2.2rem;text-align:center}}
header::before{{content:'';position:absolute;inset:0;background:radial-gradient(circle at 20% 30%,rgba(255,255,255,.18) 0,transparent 35%),radial-gradient(circle at 80% 20%,rgba(255,255,255,.12) 0,transparent 30%)}}
header > *{{position:relative}}
header h1{{font-size:clamp(2rem,5vw,3rem);font-weight:900;letter-spacing:.02em;margin-bottom:.7rem;text-shadow:0 8px 24px rgba(0,0,0,.18)}}
.hero-sub{{max-width:980px;margin:0 auto}}
.hero-tagline{{font-size:1.02rem;opacity:.96;margin-bottom:1rem}}
.trust-badges{{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;gap:.6rem;margin-bottom:.9rem}}
.trust-badges li{{padding:.45rem .95rem;border-radius:999px;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.28);backdrop-filter:blur(8px);font-size:.83rem}}
.hero-actions{{display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap;margin-top:.9rem}}
.hero-actions a{{padding:.75rem 1.1rem;border-radius:999px;font-weight:700;font-size:.88rem}}
.hero-primary{{background:#fff;color:#e83e70;box-shadow:0 8px 24px rgba(0,0,0,.15)}}
.hero-secondary{{background:rgba(255,255,255,.14);color:#fff;border:1px solid rgba(255,255,255,.35)}}
.updated{{margin-top:1rem;font-size:.76rem;opacity:.72}}
nav.cats{{display:flex;gap:.55rem;overflow-x:auto;padding:1rem 1rem .2rem;max-width:1180px;margin:0 auto;scrollbar-width:thin}}
nav.cats a{{flex:0 0 auto;padding:.45rem .9rem;border-radius:999px;border:2px solid;font-size:.78rem;font-weight:700;background:#fff}}
nav.cats a:hover{{transform:translateY(-1px)}}
.main-wrap{{max-width:1180px;margin:0 auto;padding:1.4rem 1rem 2.2rem}}
.host-card{{display:grid;grid-template-columns:84px 1fr;gap:1rem;align-items:flex-start;background:#fff;border:1px solid #f0d7dd;border-radius:22px;padding:1.3rem 1.2rem;box-shadow:0 10px 30px rgba(232,62,112,.08);margin:0 0 1.5rem}}
.host-avatar{{width:72px;height:72px;border-radius:50%;overflow:hidden;border:4px solid #fff;box-shadow:0 8px 18px rgba(0,0,0,.12)}}
.host-card h3{{color:#d61f69;font-size:1.08rem;margin-bottom:.35rem}}
.host-card p{{font-size:.9rem;color:#555;line-height:1.82}}
.host-card .soft-note{{display:inline-block;margin-top:.6rem;font-size:.78rem;color:#666;background:#fff5f7;border:1px solid #ffd7e4;border-radius:999px;padding:.28rem .75rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.4rem}}
.card{{background:#fff;border-radius:22px;overflow:hidden;box-shadow:0 8px 28px rgba(30,41,59,.08);transition:transform .18s ease, box-shadow .18s ease}}
.card:hover{{transform:translateY(-4px);box-shadow:0 16px 34px rgba(30,41,59,.12)}}
.card-cover{{position:relative;min-height:165px;padding:.85rem 1rem;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(135deg,var(--card-color),#ffb36b);overflow:hidden}}
.cover-bg-img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;opacity:.72}}
.cover-scrim{{position:absolute;inset:0;background:linear-gradient(160deg,rgba(0,0,0,.3) 0%,rgba(0,0,0,.56) 100%);z-index:1}}
.cover-top{{position:relative;z-index:2;display:flex;align-items:flex-start;justify-content:space-between;gap:.4rem}}
.cover-icon{{width:52px;height:52px;object-fit:contain;border-radius:12px;background:rgba(255,255,255,.94);padding:6px;box-shadow:0 4px 14px rgba(0,0,0,.18)}}
.promo-badge{{background:rgba(255,228,0,.95);color:#7a1818;font-size:.69rem;font-weight:800;padding:.25rem .65rem;border-radius:999px;letter-spacing:.02em;white-space:nowrap}}
.cat-pill{{position:relative;z-index:2;display:inline-flex;align-items:center;gap:.35rem;padding:.38rem .78rem;border-radius:999px;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.28);color:#fff;font-size:.76rem;font-weight:700;backdrop-filter:blur(6px);align-self:flex-end}}
.card-highlight{{font-size:.82rem;color:#d61f69;font-weight:700;margin-bottom:.55rem;background:#fff5f7;border-left:3px solid #e83e70;padding:.3rem .6rem;border-radius:0 8px 8px 0}}
.card-body{{padding:1rem 1rem 1.1rem}}
.card h2{{font-size:1.08rem;line-height:1.45;color:#1f2937;margin-bottom:.55rem}}
.mini-tags{{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.65rem}}
.mini-tags span{{font-size:.68rem;background:#f7f7fb;color:#6b7280;padding:.22rem .5rem;border-radius:999px;border:1px solid #ececf3}}
.copy{{font-size:.86rem;color:#505965;line-height:1.82;min-height:132px;margin-bottom:.75rem}}
.trust-row{{display:flex;flex-wrap:wrap;gap:.45rem;margin-bottom:.8rem}}
.trust-row span{{font-size:.7rem;color:#68707b;background:#f6f8fc;padding:.22rem .55rem;border-radius:8px}}
.btn{{display:block;text-align:center;padding:.82rem 1rem;border-radius:14px;background:linear-gradient(135deg,#e83e70 0%,#ff8a34 100%);color:#fff!important;font-weight:800;letter-spacing:.02em;box-shadow:0 8px 18px rgba(232,62,112,.22)}}
footer{{padding:2.2rem 1rem 3rem;text-align:center;color:#7a7f89;font-size:.82rem}}
footer p + p{{margin-top:.45rem}}
footer a{{color:#d61f69;font-weight:700}}
@media(max-width:640px){{header{{padding:2.5rem 1rem 1.8rem}} .host-card{{grid-template-columns:1fr;text-align:center}} .host-avatar{{margin:0 auto}} .copy{{min-height:auto}}}}
</style>
</head>
<body>
<header>
  <h1>韓律 Han Ryul</h1>
  <div class="hero-sub">
    <p class="hero-tagline">韓律的生活筆記｜記錄日常、風格與喜歡的事物</p>
    <ul class="trust-badges">
      <li>📷 日常穿搭與生活隨拍</li>
      <li>✨ 喜歡的物品與生活好物</li>
      <li>🍃 美好小事，值得慢慢享受</li>
    </ul>
    <div class="hero-actions">
      <a class="hero-primary" href="#好物分享">看看最近喜歡的</a>
      <a class="hero-secondary" href="{facebook_page_url}" target="_blank" rel="noopener">追蹤 Facebook</a>
    </div>
  </div>
  <p class="updated">最近更新：{now_str}</p>
</header>
<nav class="cats">{cat_nav}</nav>
<div class="main-wrap">
  <section class="host-card">
    <div class="host-avatar">{host_avatar}</div>
    <div>
      <h3>Hi~我是韓律 Han Ryul</h3>
      <p>
        這裡是我的生活記錄——穿搭、喜歡的物品、隨手拍的日常，還有一些想說的話。<br>
        沒有什麼特別的目的，就是把覺得美好的事留下來，順手分享給你。<br>
        如果你也喜歡這類的生活感，歡迎來
        <a href="{facebook_page_url}" target="_blank" rel="noopener">Facebook</a> 找我。
      </p>
      <span class="soft-note">部分商品連結含合作推薦，點擊後價格不會有任何變動</span>
    </div>
  </section>
  <main>
    <div class="grid" id="好物分享">
{cards_html}
    </div>
  </main>
</div>
<footer>
  <p>這裡分享的內容，以品牌官方或授權通路頁面資訊為準，活動內容請依實際頁面顯示為主。</p>
  <p><a href="{facebook_page_url}" target="_blank" rel="noopener">Facebook 粉絲頁</a>｜<a href="mailto:masatsai032@gmail.com">聯絡我</a>｜<a href="sitemap.xml">網站地圖</a></p>
</footer>
</body>
</html>"""

        os.makedirs(LIFE_DIR, exist_ok=True)
        with open(HTML_FILE, "w", encoding="utf-8") as file_handle:
            file_handle.write(html)
        print(f"[系統] 🌐 SEO HTML 已生成 → output/life/index.html")

        # 根目錄 redirect → /life/
        root_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0; url=life/">
<link rel="canonical" href="{site_url}">
<title>韓律 Han Ryul</title>
</head>
<body>
<script>window.location.replace("life/");</script>
<a href="life/">前往韓律的生活頁</a>
</body>
</html>"""
        root_html_path = os.path.join(OUTPUT_DIR, "index.html")
        with open(root_html_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(root_html)
        print(f"[系統] ↪️  根目錄 redirect 已生成 → output/index.html")

        sitemap_path = os.path.join(OUTPUT_DIR, "sitemap.xml")
        sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{site_url}</loc>
    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
        with open(sitemap_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(sitemap)
        print(f"[系統] 🗺️  Sitemap 已生成 → output/sitemap.xml")

        robots_path = os.path.join(OUTPUT_DIR, "robots.txt")
        with open(robots_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(f"User-agent: *\nAllow: /\nSitemap: {site_url}sitemap.xml\n")
        print(f"[系統] 🤖 robots.txt 已生成 → output/robots.txt")


# ── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print(f"🚀 iChannels 全自動推廣引擎 v3.0 啟動")
    print(f"   帳號: masatsai032@gmail.com")
    print(f"   聯盟ID: {ICHANNELS_AFFILIATE_ID}")
    print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    campaigns = load_campaigns()
    print(f"[系統] 📋 載入 {len(campaigns)} 個推廣任務\n")

    records = []
    for c in campaigns:
        print(f"── 處理: {c['brand']} ({c['id']}) ──")

        copy = ai_write_copy(c["brand"], c["name"], c["desc"], c["category"])
        link = make_affiliate_link(c["url"], c["uid"])

        print(f"[文案] {copy[:60]}...")
        print(f"[連結] {link[:80]}...")

        publish_to_webhook(copy, link)

        records.append({
            "id":            c["id"],
            "brand":         c["brand"],
            "category":      c["category"],
            "copy":          copy,
            "affiliate_link": link,
            "timestamp":     datetime.now().isoformat(),
            "image":         c.get("image", ""),
            "badge":         c.get("badge", ""),
            "highlight":     c.get("highlight", ""),
            "tags":          c.get("tags", []),
            "cta_text":      c.get("cta_text", ""),
        })
        print()

    # 生成 HTML + 儲存日誌
    generate_html_page(records)
    save_log(records)

    print("=" * 60)
    print(f"✅ 全部完成！共處理 {len(records)} 個品牌")
    print(f"   📄 推廣頁: output/index.html")
    print(f"   📝 日誌:   logs/")
    print("=" * 60)


if __name__ == "__main__":
    main()
