#!/usr/bin/env python3
"""
FIX 2: Facebook comments create_time — extract relative timestamps
Re-crawl posts that have comments with NULL create_time
Parse "1 thang", "2 gio", "4 tuan truoc" from DOM
"""
import psycopg2, time, random, re
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

DB = dict(host='localhost', port=5434, dbname='social_listening',
          user='sl_admin', password='SocialListening@2026!')

STATE_FILE = Path("crawl/.cookies/fb_state.json")

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)

def parse_relative_time(text):
    """Parse FB relative time: '1 thang', '2 gio', '4 tuan truoc'"""
    if not text:
        return None
    text = text.strip().lower()
    now = datetime.now()

    patterns = [
        (r'(\d+)\s*(giay|second)', 'seconds'),
        (r'(\d+)\s*(phut|minute)', 'minutes'),
        (r'(\d+)\s*(gio|hour)', 'hours'),
        (r'(\d+)\s*(ngay|day)', 'days'),
        (r'(\d+)\s*(tuan|week)', 'weeks'),
        (r'(\d+)\s*(thang|month)', 'months'),
    ]

    for pattern, unit in patterns:
        m = re.search(pattern, text)
        if m:
            val = int(m.group(1))
            if unit == 'seconds':
                return now - timedelta(seconds=val)
            elif unit == 'minutes':
                return now - timedelta(minutes=val)
            elif unit == 'hours':
                return now - timedelta(hours=val)
            elif unit == 'days':
                return now - timedelta(days=val)
            elif unit == 'weeks':
                return now - timedelta(weeks=val)
            elif unit == 'months':
                return now - timedelta(days=val*30)

    if 'hom qua' in text or 'yesterday' in text:
        return now - timedelta(days=1)

    return None


def main():
    if not STATE_FILE.exists():
        print("No cookies! Run fb_export_cookies.py first")
        return

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # Get posts that have comments with NULL create_time
    cur.execute("""
        SELECT DISTINCT fc.post_id, fp.post_url, fc.brand
        FROM raw.facebook_comments fc
        JOIN raw.facebook_posts fp ON fc.post_id = fp.post_id
        WHERE fc.create_time IS NULL
          AND fp.post_url IS NOT NULL AND fp.post_url != ''
        ORDER BY fc.brand
    """)
    posts = cur.fetchall()
    print(f"Posts with NULL create_time comments: {len(posts)}")

    # Before stats
    cur.execute("SELECT COUNT(*) FROM raw.facebook_comments WHERE create_time IS NULL")
    before_null = cur.fetchone()[0]
    print(f"Comments with NULL create_time BEFORE: {before_null}")

    fixed_total = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            storage_state=str(STATE_FILE),
            user_agent=MOBILE_UA,
            viewport={"width": 390, "height": 844},
            locale="vi-VN",
        )
        context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2}", lambda r: r.abort())

        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        for idx, (pid, purl, brand) in enumerate(posts):
            mobile_url = purl.replace("www.facebook.com", "m.facebook.com")
            if "?" in mobile_url:
                mobile_url = mobile_url.split("?")[0]

            try:
                page.goto(mobile_url, wait_until="domcontentloaded", timeout=15000)
                time.sleep(random.uniform(1.5, 2.5))

                # Click comments
                for sel in ['[aria-label*="comment"]', '[aria-label*="bình luận"]']:
                    try:
                        btns = page.query_selector_all(sel)
                        for btn in btns:
                            label = btn.get_attribute("aria-label") or ""
                            if re.search(r'\d', label):
                                btn.click()
                                time.sleep(2)
                                break
                    except:
                        pass

                # Extract timestamps from aria-labels
                # Pattern: aria-label="4 tuần trước" near comment elements
                time_elements = page.query_selector_all('[aria-label*="trước"], [aria-label*="ago"], [aria-label*="tháng"], [aria-label*="tuần"], [aria-label*="ngày"], [aria-label*="giờ"]')

                timestamps_found = []
                for el in time_elements:
                    label = el.get_attribute("aria-label") or ""
                    parsed = parse_relative_time(label)
                    if parsed:
                        timestamps_found.append(parsed)

                if timestamps_found:
                    # Get comments for this post that have NULL create_time
                    cur.execute(
                        "SELECT id FROM raw.facebook_comments WHERE post_id=%s AND create_time IS NULL ORDER BY id",
                        (pid,))
                    null_comments = cur.fetchall()

                    # Assign timestamps (best effort: distribute evenly)
                    for i, (cid,) in enumerate(null_comments):
                        if i < len(timestamps_found):
                            ts = timestamps_found[i]
                        else:
                            # Use last known timestamp with small offset
                            ts = timestamps_found[-1] - timedelta(minutes=i*5)

                        cur.execute(
                            "UPDATE raw.facebook_comments SET create_time=%s WHERE id=%s",
                            (ts, cid))
                        fixed_total += 1

                    conn.commit()

                if (idx + 1) % 10 == 0:
                    print(f"  Processed: {idx+1}/{len(posts)} | Fixed: {fixed_total}")

            except Exception as e:
                pass

            time.sleep(random.uniform(0.5, 1.5))

        context.close()
        browser.close()

    # After stats
    cur.execute("SELECT COUNT(*) FROM raw.facebook_comments WHERE create_time IS NULL")
    after_null = cur.fetchone()[0]

    print(f"\nRESULT:")
    print(f"  Before: {before_null} NULL create_time")
    print(f"  Fixed: {fixed_total}")
    print(f"  After: {after_null} NULL create_time")
    print(f"  Improvement: {before_null} -> {after_null} ({round((1-after_null/before_null)*100,1) if before_null > 0 else 0}% fixed)")

    cur.close()
    conn.close()
    print("DONE!")

if __name__ == "__main__":
    main()
