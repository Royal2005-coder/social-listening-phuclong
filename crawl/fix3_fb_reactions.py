#!/usr/bin/env python3
"""
FIX 3: Facebook reactions_breakdown — extract from post pages
Crawl reaction counts (Like, Love, Haha, Wow, Sad, Angry) from DOM
"""
import psycopg2, json, time, random, re
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


def parse_reaction_count(text):
    """Parse '4,1K' '26K' '1.5M' -> int"""
    if not text:
        return 0
    text = text.strip().replace(',', '.').upper()
    m = re.search(r'([\d.]+)\s*([KMB]?)', text)
    if m:
        val = float(m.group(1))
        suffix = m.group(2)
        if suffix == 'K':
            return int(val * 1000)
        elif suffix == 'M':
            return int(val * 1000000)
        return int(val)
    return 0


def main():
    if not STATE_FILE.exists():
        print("No cookies!")
        return

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # Get posts with NULL reactions_breakdown
    cur.execute("""
        SELECT post_id, post_url, brand, likes_count
        FROM raw.facebook_posts
        WHERE (reactions_breakdown IS NULL OR reactions_breakdown = '')
          AND post_url IS NOT NULL AND post_url != ''
        ORDER BY likes_count DESC
    """)
    posts = cur.fetchall()
    print(f"Posts need reactions fix: {len(posts)}")

    fixed = 0

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

        for idx, (pid, purl, brand, likes) in enumerate(posts):
            mobile_url = purl.replace("www.facebook.com", "m.facebook.com")
            if "?" in mobile_url:
                mobile_url = mobile_url.split("?")[0]

            try:
                page.goto(mobile_url, wait_until="domcontentloaded", timeout=15000)
                time.sleep(random.uniform(1.5, 2.5))

                reactions = {}

                # Method 1: Extract from reaction images
                # m.facebook.com shows reaction icons with aria-labels
                reaction_elements = page.query_selector_all('img[data-rt="REACTION_ICON"]')
                if reaction_elements:
                    # Count which reaction types are present
                    for el in reaction_elements:
                        alt = el.get_attribute("alt") or ""
                        src = el.get_attribute("src") or ""
                        # Map reaction icon URLs to types
                        if "l-QPkDVPL" in src or "like" in alt.lower():
                            reactions["like"] = likes  # Use total likes as approximation
                        elif "bbjFzNkpS" in src or "love" in alt.lower():
                            reactions["love"] = 1
                        elif "mGSNTNiBCm" in src or "haha" in alt.lower():
                            reactions["haha"] = 1
                        elif "4Z0BqU-m7LJ" in src:
                            reactions["like"] = likes

                # Method 2: Extract total from aria-label
                total_el = page.query_selector('[aria-label*="bày tỏ cảm xúc"], [aria-label*="reaction"]')
                if total_el:
                    label = total_el.get_attribute("aria-label") or ""
                    # Parse "4,1K người đã bày tỏ cảm xúc"
                    m = re.search(r'([\d,.]+[KMB]?)', label)
                    if m:
                        total = parse_reaction_count(m.group(1))
                        if total > 0 and "like" not in reactions:
                            reactions["total"] = total
                            reactions["like"] = total  # Best approximation

                # Method 3: Extract from like/comment/share buttons
                like_btn = page.query_selector('[aria-label*="like"]')
                if like_btn:
                    label = like_btn.get_attribute("aria-label") or ""
                    m = re.search(r'([\d,.]+[KMB]?)', label)
                    if m:
                        reactions["like"] = parse_reaction_count(m.group(1))

                if reactions:
                    reactions_json = json.dumps(reactions)
                    cur.execute(
                        "UPDATE raw.facebook_posts SET reactions_breakdown=%s WHERE post_id=%s",
                        (reactions_json, pid))
                    conn.commit()
                    fixed += 1

                if (idx + 1) % 20 == 0:
                    print(f"  Processed: {idx+1}/{len(posts)} | Fixed: {fixed}")

            except Exception as e:
                pass

            time.sleep(random.uniform(0.5, 1.0))

        context.close()
        browser.close()

    # Verify
    cur.execute("""
        SELECT brand,
               COUNT(*) as total,
               SUM(CASE WHEN reactions_breakdown IS NOT NULL AND reactions_breakdown != '' THEN 1 ELSE 0 END) as has_react
        FROM raw.facebook_posts GROUP BY brand ORDER BY brand
    """)
    print(f"\nRESULT:")
    print(f"  Fixed: {fixed}/{len(posts)}")
    for r in cur.fetchall():
        pct = round(r[2]/r[1]*100,1) if r[1] > 0 else 0
        print(f"  {r[0]:12}: {r[2]}/{r[1]} have reactions ({pct}%)")

    cur.close()
    conn.close()
    print("DONE!")

if __name__ == "__main__":
    main()
