#!/usr/bin/env python3
"""
TECHNIQUE 2 v3 — Facebook Comments Crawler
Playwright + Cookie Injection + m.facebook.com
CLICK vao comments section → parse DOM sau khi load

PREREQUISITE: python crawl\fb_export_cookies.py (da chay)

Co che:
  1. Load cookies tu fb_state.json (da verified)
  2. Navigate toi post URL tren m.facebook.com
  3. Click "binh luan" button de mo comments view
  4. Scroll/click "Xem them" de load more comments
  5. Parse comments tu DOM: span.f20 (username) + aria-label (text)
  6. Insert DB voi crawl_source='pw_mobile'
"""
import json, time, random, re, argparse
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
import psycopg2

DB = dict(host='localhost', port=5434, dbname='social_listening',
          user='sl_admin', password='YOUR_DB_PASSWORD')

STATE_FILE = Path("crawl/.cookies/fb_state.json")
BRANDS = ["phuc_long", "highlands", "katinat"]

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)


def get_posts_needing_comments(conn, brand, top_n=30, min_existing=5):
    cur = conn.cursor()
    cur.execute("""
        SELECT fp.post_id, fp.post_url, fp.comments_count as reported,
               COALESCE(fc.cnt, 0) as existing
        FROM raw.facebook_posts fp
        LEFT JOIN (
            SELECT post_id, COUNT(*) as cnt
            FROM raw.facebook_comments WHERE brand = %s GROUP BY post_id
        ) fc ON fp.post_id = fc.post_id
        WHERE fp.brand = %s
          AND fp.post_url IS NOT NULL AND fp.post_url != ''
          AND fp.comments_count > 3
          AND COALESCE(fc.cnt, 0) < %s
        ORDER BY (fp.comments_count - COALESCE(fc.cnt, 0)) DESC
        LIMIT %s
    """, (brand, brand, min_existing, top_n))
    rows = cur.fetchall()
    cur.close()
    return rows


def convert_to_mobile_url(post_url):
    if not post_url:
        return None
    url = post_url.replace("www.facebook.com", "m.facebook.com")
    url = url.replace("//facebook.com", "//m.facebook.com")
    url = url.replace("web.facebook.com", "m.facebook.com")
    if "?" in url:
        url = url.split("?")[0]
    return url


def extract_comments_from_page(page, post_id, brand, max_comments=150):
    """Extract comments tu rendered DOM cua m.facebook.com."""
    comments = []
    seen = set()

    # Method 1: Find comments via aria-label pattern
    # m.facebook.com 2026 uses: aria-label="<text>, Double tap and hold to interact"
    elements = page.query_selector_all('[aria-label*="Double tap and hold"]')
    for el in elements:
        try:
            label = el.get_attribute("aria-label") or ""
            # Extract comment text from aria-label
            # Pattern: "comment text, Double tap and hold to interact with this comment"
            text = re.sub(r',?\s*Double tap and hold.*$', '', label, flags=re.I).strip()
            if len(text) < 2 or len(text) > 2000:
                continue

            cid = str(hash(text[:60] + post_id + brand))
            if cid in seen:
                continue
            seen.add(cid)

            # Try to find username from parent/sibling
            usr = ""
            try:
                parent = el.evaluate_handle("el => el.closest('[data-tracking-duration-id]')")
                if parent:
                    name_el = parent.as_element().query_selector('span.f20')
                    if name_el:
                        usr = name_el.inner_text()[:50]
            except:
                pass

            comments.append({
                "comment_id": cid, "post_id": post_id, "brand": brand,
                "comment_text": text[:2000], "like_count": 0,
                "reply_count": 0, "create_time": None, "user_name": usr,
            })
            if len(comments) >= max_comments:
                break
        except:
            continue

    # Method 2: Find comments via bg-s4 class (comment bubble background)
    if len(comments) < 5:
        bubbles = page.query_selector_all('.bg-s4')
        for bubble in bubbles:
            try:
                # Comment bubble contains: username (f20) + text (f1)
                inner = bubble.inner_text()
                if len(inner) < 3 or len(inner) > 2000:
                    continue

                lines = inner.strip().split('\n')
                if len(lines) < 2:
                    continue

                usr = lines[0][:50]
                text = '\n'.join(lines[1:]).strip()

                # Skip if it looks like navigation/UI text
                skip = ['Thich', 'Tra loi', 'Reply', 'Like', 'Xem', 'View',
                        'Viet binh luan', 'Write a comment']
                if any(text.strip() == s for s in skip):
                    continue
                if len(text) < 2:
                    continue

                cid = str(hash(text[:60] + post_id + brand))
                if cid in seen:
                    continue
                seen.add(cid)

                comments.append({
                    "comment_id": cid, "post_id": post_id, "brand": brand,
                    "comment_text": text[:2000], "like_count": 0,
                    "reply_count": 0, "create_time": None, "user_name": usr,
                })
                if len(comments) >= max_comments:
                    break
            except:
                continue

    # Method 3: Find all tracking-duration containers that look like comments
    if len(comments) < 5:
        containers = page.query_selector_all('[data-tracking-duration-id]')
        for container in containers:
            try:
                # Comment containers have: profile image (rounded) + text bubble
                has_rounded = container.query_selector('img.rounded')
                if not has_rounded:
                    continue

                text = container.inner_text()
                if len(text) < 5 or len(text) > 2000:
                    continue

                # Parse: first line = username, rest = comment
                lines = text.strip().split('\n')
                # Filter out UI elements
                clean_lines = [l for l in lines if l.strip() and
                              l.strip() not in ['Thich', 'Tra loi', 'Reply',
                                               'Like', 'Phan hoi']]
                if len(clean_lines) < 2:
                    continue

                usr = clean_lines[0][:50]
                # Remove timestamp patterns
                comment_lines = []
                for l in clean_lines[1:]:
                    if re.match(r'^\d+\s*(thang|gio|phut|ngay|tuan)', l.strip()):
                        continue
                    if l.strip() in ['Thích', 'Trả lời', 'Like', 'Reply']:
                        continue
                    comment_lines.append(l)

                comment_text = ' '.join(comment_lines).strip()
                if len(comment_text) < 2:
                    continue

                cid = str(hash(comment_text[:60] + post_id + brand))
                if cid in seen:
                    continue
                seen.add(cid)

                comments.append({
                    "comment_id": cid, "post_id": post_id, "brand": brand,
                    "comment_text": comment_text[:2000], "like_count": 0,
                    "reply_count": 0, "create_time": None, "user_name": usr,
                })
                if len(comments) >= max_comments:
                    break
            except:
                continue

    return comments


def crawl_post_comments(page, post_url, post_id, brand, max_comments=150):
    """Crawl comments tu 1 Facebook post."""
    mobile_url = convert_to_mobile_url(post_url)
    if not mobile_url:
        return []

    try:
        page.goto(mobile_url, wait_until="domcontentloaded", timeout=20000)
    except:
        try:
            page.goto(mobile_url, timeout=30000)
        except:
            return []

    time.sleep(random.uniform(3, 5))

    # Step 1: Click on "binh luan" / comments button to open comments view
    clicked_comments = False
    for selector in [
        '[aria-label*="comment"]',
        '[aria-label*="bình luận"]',
        '[aria-label*="binh luan"]',
        'text=bình luận',
    ]:
        try:
            btns = page.query_selector_all(selector)
            for btn in btns:
                label = btn.get_attribute("aria-label") or ""
                text = btn.inner_text() or ""
                # Find the "X comments" button (not "write comment")
                if re.search(r'\d', label) or re.search(r'\d', text):
                    btn.click()
                    clicked_comments = True
                    time.sleep(random.uniform(3, 5))
                    break
            if clicked_comments:
                break
        except:
            continue

    if not clicked_comments:
        # Try clicking any element with comment count
        try:
            count_els = page.query_selector_all('[aria-label*="comments"]')
            for el in count_els:
                el.click()
                clicked_comments = True
                time.sleep(3)
                break
        except:
            pass

    # Step 2: Click "View more comments" / "Xem them binh luan" multiple times
    for _ in range(5):
        try:
            more_btns = page.query_selector_all(
                'text=/Xem.*bình luận|View.*comment|Xem thêm/')
            for btn in more_btns:
                try:
                    btn.click()
                    time.sleep(random.uniform(2, 4))
                except:
                    pass
        except:
            pass

        # Scroll down to trigger loading
        page.mouse.wheel(0, random.randint(800, 1500))
        time.sleep(random.uniform(1.5, 3))

    # Step 3: Extract comments from rendered DOM
    comments = extract_comments_from_page(page, post_id, brand, max_comments)

    return comments


def insert_comments(conn, comments):
    cur = conn.cursor()
    n = 0
    for c in comments:
        if not c:
            continue
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
            if cur.rowcount > 0:
                n += 1
        except:
            conn.rollback()
    conn.commit()
    cur.close()
    return n


def print_status(conn):
    cur = conn.cursor()
    print(f"\n{'='*60}")
    print("  COMMENTS STATUS:")
    cur.execute("""
        SELECT 'TikTok' as p, brand, COUNT(*) FROM raw.tiktok_comments GROUP BY brand
        UNION ALL
        SELECT 'Facebook', brand, COUNT(*) FROM raw.facebook_comments GROUP BY brand
        ORDER BY 1, 2
    """)
    total = 0
    for r in cur.fetchall():
        print(f"    {r[0]:10} | {r[1]:12}: {r[2]:>5}")
        total += r[2]
    print(f"    {'TOTAL':10} | {'':12}: {total:>5}")
    cur.close()
    return total


def main():
    parser = argparse.ArgumentParser(
        description="T2-v3: Facebook Comments (Playwright + Click Comments)")
    parser.add_argument("--brands", nargs="+",
                        choices=BRANDS + ["all"], default=["all"])
    parser.add_argument("--top-n", type=int, default=30)
    parser.add_argument("--max-comments", type=int, default=150)
    parser.add_argument("--min-existing", type=int, default=5)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    brands = BRANDS if "all" in args.brands else [b for b in args.brands if b in BRANDS]
    headless = not args.headed

    if not STATE_FILE.exists():
        print(f"  COOKIES NOT FOUND: {STATE_FILE}")
        print(f"  Run: python crawl\\fb_export_cookies.py")
        return

    print("=" * 60)
    print("  TECHNIQUE 2 v3 — Facebook Comments")
    print("  Playwright + Cookies + Click Comments View")
    print(f"  Mode: {'headless' if headless else 'HEADED (debug)'}")
    print(f"  Brands: {brands}")
    print(f"  Top-N: {args.top_n} | Max cmt/post: {args.max_comments}")
    print("=" * 60)

    conn = psycopg2.connect(**DB)
    current_total = print_status(conn)
    grand_total = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )

        for brand in brands:
            print(f"\n{'─'*60}")
            print(f"  [{brand}] Facebook Comments")
            print(f"{'─'*60}")

            posts = get_posts_needing_comments(
                conn, brand, args.top_n, args.min_existing)
            print(f"  Posts to crawl: {len(posts)}")

            if not posts:
                continue

            # Create context with cookies
            context = browser.new_context(
                storage_state=str(STATE_FILE),
                user_agent=MOBILE_UA,
                viewport={"width": 390, "height": 844},
                locale="vi-VN",
            )
            page = context.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

            brand_new = 0
            zero_count = 0

            for idx, (pid, purl, reported, existing) in enumerate(posts):
                comments = crawl_post_comments(
                    page, purl, pid, brand, max_comments=args.max_comments)

                if comments and not args.dry_run:
                    n = insert_comments(conn, comments)
                    brand_new += n
                    grand_total += n
                    zero_count = 0
                    print(f"    [{idx+1}/{len(posts)}] {pid[:20]}: "
                          f"+{n} new ({len(comments)} got, "
                          f"had={existing}, reported={reported})")
                elif comments:
                    zero_count = 0
                    print(f"    [{idx+1}/{len(posts)}] {pid[:20]}: "
                          f"{len(comments)} collected (dry-run)")
                else:
                    zero_count += 1
                    if zero_count <= 3:
                        print(f"    [{idx+1}/{len(posts)}] {pid[:20]}: "
                              f"0 (reported={reported})")
                    if zero_count >= 6:
                        print(f"    Stopping {brand} — cookie may need refresh")
                        break

                time.sleep(random.uniform(2, 5))

            context.close()
            print(f"  [{brand}] New: {brand_new}")

        browser.close()

    final_total = print_status(conn)
    print(f"\n  SESSION: +{grand_total} | {current_total} -> {final_total}")
    conn.close()
    print(f"\n{'='*60}")
    print("  DONE!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
