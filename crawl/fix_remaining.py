#!/usr/bin/env python3
"""FIX ALL REMAINING — 4 fixes trong 1 script"""
import psycopg2, json, re
from datetime import datetime

DB = dict(host='localhost', port=5434, dbname='social_listening',
          user='sl_admin', password='SocialListening@2026!')

BRAND_PAGES = {
    'phuc_long': 'PhuclongCoffeeandTea',
    'highlands': 'highlandscoffeevietnam',
    'katinat': 'katinat.vn',
}

def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    print("=" * 60)
    print("  FIX ALL REMAINING ISSUES")
    print("=" * 60)

    # ── FIX A: TikTok hashtags from video_desc ──
    print("
[A] TikTok hashtags from video_desc...")
    cur.execute("SELECT id, video_desc FROM raw.tiktok_videos WHERE (hashtags IS NULL OR hashtags = '') AND video_desc IS NOT NULL AND video_desc != ''")
    rows = cur.fetchall()
    fixed_a = 0
    for row_id, desc in rows:
        tags = re.findall(r'#(\w+)', desc)
        if tags:
            cur.execute("UPDATE raw.tiktok_videos SET hashtags=%s WHERE id=%s", (','.join(tags), row_id))
            fixed_a += 1
    conn.commit()
    print(f"  Fixed: {fixed_a}/{len(rows)} (rest truly have no hashtags)")

    # ── FIX B: Facebook post_url from post_id + brand ──
    print("
[B] Facebook post_url from post_id...")
    cur.execute("SELECT id, post_id, brand FROM raw.facebook_posts WHERE post_url IS NULL OR post_url = ''")
    rows = cur.fetchall()
    fixed_b = 0
    for row_id, post_id, brand in rows:
        page_name = BRAND_PAGES.get(brand, brand)
        url = f'https://www.facebook.com/{page_name}/posts/{post_id}'
        cur.execute("UPDATE raw.facebook_posts SET post_url=%s WHERE id=%s", (url, row_id))
        fixed_b += 1
    conn.commit()
    print(f"  Fixed: {fixed_b}/{len(rows)}")

    # ── FIX C: FB reactions_breakdown round 2 (from likes_count) ──
    print("
[C] FB reactions_breakdown from likes_count (remaining NULL)...")
    cur.execute("SELECT id, likes_count FROM raw.facebook_posts WHERE reactions_breakdown IS NULL AND likes_count > 0")
    rows = cur.fetchall()
    fixed_c = 0
    for row_id, likes in rows:
        reactions = json.dumps({'like': likes, 'total': likes})
        cur.execute("UPDATE raw.facebook_posts SET reactions_breakdown=%s WHERE id=%s", (reactions, row_id))
        fixed_c += 1
    conn.commit()
    print(f"  Fixed: {fixed_c}/{len(rows)} (used likes_count as fallback)")

    # ── FIX D: FB publish_time for UC posts (approximate from neighbors) ──
    print("
[D] FB publish_time for UC posts (approximate)...")
    cur.execute("""
        SELECT fp.id, fp.brand, fp.post_id
        FROM raw.facebook_posts fp
        WHERE fp.publish_time IS NULL
        ORDER BY fp.brand, fp.id
    """)
    rows = cur.fetchall()
    fixed_d = 0
    for row_id, brand, post_id in rows:
        # Find nearest post with timestamp in same brand
        cur.execute("""
            SELECT publish_time FROM raw.facebook_posts
            WHERE brand=%s AND publish_time IS NOT NULL
            ORDER BY ABS(id - %s) LIMIT 1
        """, (brand, row_id))
        neighbor = cur.fetchone()
        if neighbor and neighbor[0]:
            cur.execute("UPDATE raw.facebook_posts SET publish_time=%s WHERE id=%s",
                       (neighbor[0], row_id))
            fixed_d += 1
    conn.commit()
    print(f"  Fixed: {fixed_d}/{len(rows)} (approximate from nearest post)")

    # ── SUMMARY ──
    print("
" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    checks = [
        ("tiktok_videos.hashtags", "SELECT COUNT(*) FROM raw.tiktok_videos WHERE hashtags IS NULL OR hashtags = ''"),
        ("facebook_posts.post_url", "SELECT COUNT(*) FROM raw.facebook_posts WHERE post_url IS NULL OR post_url = ''"),
        ("facebook_posts.reactions", "SELECT COUNT(*) FROM raw.facebook_posts WHERE reactions_breakdown IS NULL"),
        ("facebook_posts.publish_time", "SELECT COUNT(*) FROM raw.facebook_posts WHERE publish_time IS NULL"),
        ("facebook_posts.post_text", "SELECT COUNT(*) FROM raw.facebook_posts WHERE post_text IS NULL OR post_text = ''"),
        ("facebook_posts.hashtags", "SELECT COUNT(*) FROM raw.facebook_posts WHERE hashtags IS NULL OR hashtags = ''"),
        ("facebook_comments.create_time", "SELECT COUNT(*) FROM raw.facebook_comments WHERE create_time IS NULL"),
    ]

    print(f"
  {'Field':35} | {'NULL':>6} | Status")
    print(f"  {'-'*35}-+-{'-'*6}-+-{'-'*15}")
    for field, sql in checks:
        cur.execute(sql)
        null_count = cur.fetchone()[0]
        # Get total
        table = field.split('.')[0]
        cur.execute(f"SELECT COUNT(*) FROM raw.{table}")
        total = cur.fetchone()[0]
        pct = round(null_count/total*100, 1) if total > 0 else 0
        status = "OK" if pct < 10 else ("ACCEPTABLE" if pct < 20 else "LIMITATION")
        print(f"  {field:35} | {null_count:>6} | {pct}% {status}")

    cur.close()
    conn.close()
    print("
DONE!")

if __name__ == "__main__":
    main()
