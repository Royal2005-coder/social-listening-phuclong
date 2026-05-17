#!/usr/bin/env python3
"""
TECHNIQUE 2 PRODUCTION — Facebook Posts + Comments Crawler
Engine: undetected-chromedriver (headless, bypass anti-bot)
Schema: raw.facebook_posts + raw.facebook_comments (dong bo Apify)
FIX: Hashtag extraction tu post_text

Install:
  pip install undetected-chromedriver selenium psycopg2-binary

Co che:
  - undetected-chromedriver patch ChromeDriver tu dong
  - Rename Selenium variables -> giong browser that
  - Headless mode OK (bypass Cloudflare/DataDome)
  - Auto download dung version ChromeDriver cho Chrome da cai

Chay:
  python crawl\technique2_facebook.py --brands all
  python crawl\technique2_facebook.py --brands phuc_long --target 50
  python crawl\technique2_facebook.py --comments --top-n 30
"""
import json, time, random, re, argparse
from datetime import datetime, timedelta
import psycopg2

DB = dict(host='localhost', port=5434, dbname='social_listening',
          user='sl_admin', password='SocialListening@2026!')

BRANDS = {
    "phuc_long":  "https://www.facebook.com/PhuclongCoffeeandTea",
    "highlands":  "https://www.facebook.com/highlandscoffeevietnam",
    "katinat":    "https://www.facebook.com/katinat.vn",
}

MAX_SCROLLS = 40
SCROLL_DELAY = (2, 4)
TARGET = 100


def extract_hashtags(text):
    if not text: return ""
    tags = re.findall(r'#([\w\u00C0-\u024F\u1E00-\u1EFF]+)', text, re.UNICODE)
    return ",".join(tags)


def get_driver(headless=True):
    """Create undetected Chrome driver."""
    import undetected_chromedriver as uc

    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,900')
    options.add_argument('--lang=vi-VN')
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = uc.Chrome(options=options, use_subprocess=False)
    return driver


def crawl_facebook_posts(brand, url, headless=True, target=TARGET):
    """Crawl Facebook fanpage posts."""
    from selenium.webdriver.common.by import By

    print(f"\n{'='*60}")
    print(f"  [T2] Facebook Posts — {brand}")
    print(f"  Engine: undetected-chromedriver ({'headless' if headless else 'headed'})")
    print(f"{'='*60}")

    driver = get_driver(headless=headless)
    posts = []
    seen = set()

    try:
        driver.get(url)
        time.sleep(random.uniform(4, 6))

        # Close login popup
        for _ in range(3):
            try:
                close_btns = driver.find_elements(By.CSS_SELECTOR,
                    '[aria-label="Close"], [aria-label="Đóng"]')
                for btn in close_btns:
                    btn.click()
                    time.sleep(1)
                    break
            except:
                pass

        for scroll_i in range(MAX_SCROLLS):
            if len(posts) >= target:
                break

            articles = driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]')
            for art in articles:
                try:
                    # Post text
                    text_els = art.find_elements(By.CSS_SELECTOR,
                        '[data-ad-comet-preview="message"]')
                    post_text = text_els[0].text if text_els else ""
                    if not post_text or len(post_text.strip()) < 5:
                        continue

                    phash = str(hash(post_text[:100] + brand))
                    if phash in seen:
                        continue
                    seen.add(phash)

                    # Engagement
                    likes = 0; comments_count = 0; shares = 0
                    try:
                        spans = art.find_elements(By.TAG_NAME, 'span')
                        for sp in spans:
                            t = sp.text or ""
                            tl = t.lower()
                            if any(w in tl for w in ['like', 'reaction', 'thich']):
                                m = re.search(r'(\d[\d,.]*)', t)
                                if m:
                                    likes = int(m.group(1).replace(',','').replace('.',''))
                            elif any(w in tl for w in ['comment', 'binh luan']):
                                m = re.search(r'(\d+)', t)
                                if m: comments_count = int(m.group(1))
                            elif any(w in tl for w in ['share', 'chia se']):
                                m = re.search(r'(\d+)', t)
                                if m: shares = int(m.group(1))
                    except:
                        pass

                    # Post URL + ID
                    post_url = ""; post_id = phash
                    try:
                        links = art.find_elements(By.CSS_SELECTOR, 'a[href*="/posts/"]')
                        if links:
                            post_url = links[0].get_attribute("href") or ""
                            pid_m = re.search(r'/posts/(\d+)', post_url)
                            if pid_m: post_id = pid_m.group(1)
                    except:
                        pass

                    # Post type
                    has_video = bool(art.find_elements(By.TAG_NAME, 'video'))
                    has_img = bool(art.find_elements(By.CSS_SELECTOR, 'img[src*="scontent"]'))
                    post_type = "video" if has_video else ("photo" if has_img else "status")

                    # Hashtags from text
                    hashtags = extract_hashtags(post_text)

                    posts.append({
                        "post_id": post_id, "brand": brand,
                        "post_text": post_text[:5000], "post_type": post_type,
                        "publish_time": None,
                        "likes_count": likes, "shares_count": shares,
                        "comments_count": comments_count,
                        "reactions_breakdown": None,
                        "hashtags": hashtags, "post_url": post_url,
                        "crawl_source": "uc_chrome",
                    })
                except:
                    continue

            driver.execute_script(f"window.scrollBy(0, {random.randint(800, 1500)})")
            d = random.uniform(*SCROLL_DELAY)
            print(f"    Scroll {scroll_i+1}/{MAX_SCROLLS} | posts: {len(posts)} | wait {d:.1f}s")
            time.sleep(d)

    except Exception as e:
        print(f"  ERROR: {e}")
    finally:
        driver.quit()

    print(f"  Total {brand}: {len(posts)}")
    return posts


def crawl_post_comments(post_url, post_id, brand, headless=True, max_comments=50):
    """Crawl comments from a single Facebook post."""
    from selenium.webdriver.common.by import By

    driver = get_driver(headless=headless)
    comments = []
    seen = set()

    try:
        driver.get(post_url)
        time.sleep(random.uniform(3, 5))

        # Close popup
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, '[aria-label="Close"]')
            for b in btns: b.click(); time.sleep(1)
        except: pass

        # Click "View more comments"
        for _ in range(3):
            try:
                more = driver.find_elements(By.XPATH,
                    '//span[contains(text(),"Xem thêm") or contains(text(),"View more")]')
                for m in more: m.click(); time.sleep(2)
            except: pass

        # Scroll
        for _ in range(6):
            driver.execute_script(f"window.scrollBy(0, {random.randint(500, 1000)})")
            time.sleep(random.uniform(1.5, 3))

        # Extract
        articles = driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]')
        for el in articles:
            try:
                txt = el.text or ""
                if len(txt.strip()) < 3 or len(txt) > 1500: continue
                cid = str(hash(txt[:50] + post_id))
                if cid in seen: continue
                seen.add(cid)

                lines = txt.strip().split('\n')
                usr = lines[0][:50] if lines else ""
                comment_text = '\n'.join(lines[1:]) if len(lines) > 1 else txt
                if len(comment_text.strip()) < 2: continue

                comments.append({
                    "comment_id": cid, "post_id": post_id, "brand": brand,
                    "comment_text": comment_text[:2000],
                    "like_count": 0, "reply_count": 0,
                    "create_time": None, "user_name": usr,
                })
                if len(comments) >= max_comments: break
            except: continue

    except Exception as e:
        print(f"    Error: {e}")
    finally:
        driver.quit()

    return comments


def insert_posts(conn, posts):
    cur = conn.cursor(); n = 0
    for p in posts:
        try:
            cur.execute("""
                INSERT INTO raw.facebook_posts
                (post_id, brand, post_text, post_type, publish_time,
                 likes_count, shares_count, comments_count,
                 reactions_breakdown, hashtags, post_url, crawl_source)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(post_id) DO NOTHING
            """, (p["post_id"], p["brand"], p["post_text"], p["post_type"],
                  p["publish_time"], p["likes_count"], p["shares_count"],
                  p["comments_count"], p["reactions_breakdown"],
                  p["hashtags"], p["post_url"], p["crawl_source"]))
            if cur.rowcount > 0: n += 1
        except: conn.rollback()
    conn.commit(); cur.close()
    return n


def insert_fb_comments(conn, comments):
    cur = conn.cursor(); n = 0
    for c in comments:
        if not c: continue
        try:
            cur.execute("""
                INSERT INTO raw.facebook_comments
                (comment_id, post_id, brand, comment_text,
                 like_count, reply_count, create_time, user_name)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """, (c["comment_id"], c["post_id"], c["brand"],
                  c["comment_text"], c["like_count"], c["reply_count"],
                  c["create_time"], c["user_name"]))
            if cur.rowcount > 0: n += 1
        except: conn.rollback()
    conn.commit(); cur.close()
    return n


def get_top_posts_for_comments(conn, brand, limit=20):
    cur = conn.cursor()
    cur.execute("""
        SELECT fp.post_id, fp.post_url FROM raw.facebook_posts fp
        LEFT JOIN (
            SELECT post_id, COUNT(*) as cnt
            FROM raw.facebook_comments WHERE brand = %s GROUP BY post_id
        ) fc ON fp.post_id = fc.post_id
        WHERE fp.brand = %s AND fp.post_url IS NOT NULL AND fp.post_url != ''
          AND (fc.cnt IS NULL OR fc.cnt < 5)
        ORDER BY (fp.likes_count + fp.comments_count + fp.shares_count) DESC
        LIMIT %s
    """, (brand, brand, limit))
    rows = cur.fetchall(); cur.close()
    return rows


def main():
    parser = argparse.ArgumentParser(description="T2: Facebook Crawler (undetected-chromedriver)")
    parser.add_argument("--brands", nargs="+",
                        choices=list(BRANDS.keys()) + ["all"], default=["all"])
    parser.add_argument("--target", type=int, default=TARGET)
    parser.add_argument("--comments", action="store_true")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    brands_map = BRANDS if "all" in args.brands else {b: BRANDS[b] for b in args.brands if b in BRANDS}
    headless = not args.headed

    if args.comments:
        print("=" * 60)
        print("  TECHNIQUE 2 — Facebook Comments (undetected-chromedriver)")
        print("=" * 60)
        conn = psycopg2.connect(**DB)
        total = 0
        for brand in brands_map:
            posts = get_top_posts_for_comments(conn, brand, args.top_n)
            print(f"\n--- {brand} ({len(posts)} posts) ---")
            for pid, purl in posts:
                if not purl: continue
                cmts = crawl_post_comments(purl, pid, brand, headless=headless)
                if not args.dry_run and cmts:
                    n = insert_fb_comments(conn, cmts)
                    total += n
                    print(f"  {pid[:25]}: {n} new")
                else:
                    print(f"  {pid[:25]}: {len(cmts)} collected")
                time.sleep(random.uniform(3, 6))
        conn.close()
        print(f"  NEW: {total}")
    else:
        print("=" * 60)
        print("  TECHNIQUE 2 — Facebook Posts (undetected-chromedriver)")
        print(f"  Brands: {list(brands_map.keys())}")
        print("=" * 60)
        conn = psycopg2.connect(**DB) if not args.dry_run else None
        total = 0
        for brand, url in brands_map.items():
            posts = crawl_facebook_posts(brand, url, headless=headless, target=args.target)
            if not args.dry_run and posts and conn:
                n = insert_posts(conn, posts)
                total += n
                print(f"  {brand}: {n} new")
            time.sleep(random.uniform(5, 10))
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT brand, COUNT(*) FROM raw.facebook_posts GROUP BY brand")
            print(f"\n  TOTAL:")
            for r in cur.fetchall(): print(f"    {r[0]:12}: {r[1]:>5}")
            cur.close(); conn.close()
        print(f"  NEW: {total}")


if __name__ == "__main__":
    main()
