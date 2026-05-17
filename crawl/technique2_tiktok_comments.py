#!/usr/bin/env python3
"""
TECHNIQUE 2 — TikTok Comments Crawler
Engine: curl_cffi (TLS fingerprint) goi TikTok Comments API truc tiep
KHONG can browser, KHONG can cookies, KHONG can yt-dlp

API endpoint: https://www.tiktok.com/api/comment/list/
curl_cffi impersonate Chrome TLS → bypass bot detection o tang API

Chay:
  python crawl\technique2_tiktok_comments.py --brands all --top-n 80
  python crawl\technique2_tiktok_comments.py --brands phuc_long --top-n 30
"""
import json, time, random, re, argparse
from datetime import datetime
from curl_cffi import requests as cffi_requests
import psycopg2

DB = dict(host='localhost', port=5434, dbname='social_listening',
          user='sl_admin', password='YOUR_DB_PASSWORD')

BRAND_USERNAMES = {
    "phuc_long": "phuclongofficial",
    "highlands": "highlandscoffeevietnam",
    "katinat": "katinatvn",
}

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
    "Referer": "https://www.tiktok.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

# Rotate impersonation targets
IMPERSONATE_TARGETS = ["chrome", "chrome110", "chrome116", "chrome120", "safari"]


def get_videos_needing_comments(conn, brand, top_n=80, min_existing=10):
    """Lay videos can crawl them comments."""
    cur = conn.cursor()
    cur.execute("""
        SELECT tv.video_id, tv.video_url, tv.author_name,
               tv.likes_count + tv.comments_count + tv.shares_count as engagement,
               tv.comments_count as expected_comments,
               COALESCE(tc.cnt, 0) as existing_comments
        FROM raw.tiktok_videos tv
        LEFT JOIN (
            SELECT video_id, COUNT(*) as cnt
            FROM raw.tiktok_comments WHERE brand = %s
            GROUP BY video_id
        ) tc ON tv.video_id = tc.video_id
        WHERE tv.brand = %s
          AND tv.comments_count > 0
          AND COALESCE(tc.cnt, 0) < %s
        ORDER BY tv.comments_count DESC, 
                 (tv.likes_count + tv.comments_count + tv.shares_count) DESC
        LIMIT %s
    """, (brand, brand, min_existing, top_n))
    rows = cur.fetchall()
    cur.close()
    return rows


def crawl_comments_api(video_id, brand, max_comments=150):
    """Crawl comments bang curl_cffi goi TikTok API truc tiep."""
    comments = []
    seen = set()
    cursor = 0
    imp_idx = 0

    for page in range(10):  # max 10 pages x 50 = 500 comments
        if len(comments) >= max_comments:
            break

        imp = IMPERSONATE_TARGETS[imp_idx % len(IMPERSONATE_TARGETS)]
        imp_idx += 1

        params = {
            "aweme_id": str(video_id),
            "count": "50",
            "cursor": str(cursor),
            "aid": "1988",
            "app_language": "vi-VN",
            "app_name": "tiktok_web",
        }

        try:
            resp = cffi_requests.get(
                "https://www.tiktok.com/api/comment/list/",
                params=params,
                headers=HEADERS,
                impersonate=imp,
                timeout=15,
            )

            if resp.status_code != 200:
                # Try different impersonation
                for alt_imp in IMPERSONATE_TARGETS:
                    if alt_imp == imp:
                        continue
                    try:
                        resp = cffi_requests.get(
                            "https://www.tiktok.com/api/comment/list/",
                            params=params,
                            headers=HEADERS,
                            impersonate=alt_imp,
                            timeout=15,
                        )
                        if resp.status_code == 200:
                            break
                    except:
                        continue

            if resp.status_code != 200:
                break

            data = resp.json()
            cmt_list = data.get("comments", [])

            if not cmt_list:
                break

            for item in cmt_list:
                txt = item.get("text", "") or ""
                if len(txt.strip()) < 2:
                    continue

                cid = str(item.get("cid", item.get("id", "")))
                if not cid or cid in seen:
                    continue
                seen.add(cid)

                ct = None
                ts = item.get("create_time", None)
                if ts and isinstance(ts, (int, float)):
                    try:
                        ct = datetime.fromtimestamp(int(ts))
                    except:
                        pass

                user = item.get("user", {})
                usr = ""
                if isinstance(user, dict):
                    usr = user.get("unique_id", user.get("uniqueId",
                          user.get("nickname", ""))) or ""

                lk = int(item.get("digg_count", item.get("diggCount", 0)) or 0)
                rp = int(item.get("reply_comment_total",
                         item.get("replyCommentTotal", 0)) or 0)

                comments.append({
                    "comment_id": cid,
                    "video_id": str(video_id),
                    "brand": brand,
                    "comment_text": txt[:2000],
                    "like_count": lk,
                    "reply_count": rp,
                    "create_time": ct,
                    "user_nickname": usr[:100],
                })

            has_more = data.get("has_more", 0)
            cursor = data.get("cursor", cursor + 50)

            if not has_more:
                break

        except Exception as e:
            err = str(e)
            if "timeout" not in err.lower():
                pass  # silent
            break

        time.sleep(random.uniform(0.8, 2.0))

    return comments


def insert_comments(conn, comments):
    cur = conn.cursor()
    n = 0
    for c in comments:
        if not c:
            continue
        try:
            cur.execute("""
                INSERT INTO raw.tiktok_comments
                (comment_id, video_id, brand, comment_text,
                 like_count, reply_count, create_time, user_nickname)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """, (
                c["comment_id"], c["video_id"], c["brand"],
                c["comment_text"], c["like_count"], c["reply_count"],
                c["create_time"], c["user_nickname"],
            ))
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
    print("  CURRENT COMMENTS STATUS:")
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
    print(f"    Target: 12,000+ | Need: {max(0, 12000 - total):>5} more")
    cur.close()
    return total


def main():
    parser = argparse.ArgumentParser(
        description="T2: TikTok Comments (curl_cffi API)")
    parser.add_argument("--brands", nargs="+",
                        choices=list(BRAND_USERNAMES.keys()) + ["all"],
                        default=["all"])
    parser.add_argument("--top-n", type=int, default=80,
                        help="Top N videos per brand")
    parser.add_argument("--max-comments", type=int, default=150,
                        help="Max comments per video")
    parser.add_argument("--min-existing", type=int, default=10,
                        help="Skip videos with >= N existing comments")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    brands = (list(BRAND_USERNAMES.keys()) if "all" in args.brands
              else [b for b in args.brands if b in BRAND_USERNAMES])

    print("=" * 60)
    print("  TECHNIQUE 2 — TikTok Comments (curl_cffi API)")
    print("  TLS fingerprint | No browser | No cookies")
    print(f"  Brands: {brands}")
    print(f"  Top-N: {args.top_n} | Max cmt/video: {args.max_comments}")
    print(f"  DB: {'DRY RUN' if args.dry_run else 'LIVE INSERT'}")
    print("=" * 60)

    conn = psycopg2.connect(**DB)
    current_total = print_status(conn)
    grand_total_new = 0

    for brand in brands:
        username = BRAND_USERNAMES[brand]
        print(f"\n{'─'*60}")
        print(f"  [{brand}] @{username}")
        print(f"{'─'*60}")

        videos = get_videos_needing_comments(
            conn, brand, args.top_n, args.min_existing)
        print(f"  Videos to crawl: {len(videos)}")

        brand_new = 0
        consecutive_zero = 0

        for idx, (vid, vurl, author, engagement, expected, existing) in enumerate(videos):
            comments = crawl_comments_api(vid, brand, max_comments=args.max_comments)

            if comments and not args.dry_run:
                n = insert_comments(conn, comments)
                brand_new += n
                grand_total_new += n
                consecutive_zero = 0
                print(f"    [{idx+1}/{len(videos)}] {vid[:18]}: "
                      f"+{n} new ({len(comments)} got, "
                      f"{existing} had, ~{expected} expected)")
            elif comments:
                consecutive_zero = 0
                print(f"    [{idx+1}/{len(videos)}] {vid[:18]}: "
                      f"{len(comments)} collected (dry-run)")
            else:
                consecutive_zero += 1
                if consecutive_zero <= 3:
                    print(f"    [{idx+1}/{len(videos)}] {vid[:18]}: "
                          f"0 collected (API may block)")

            # If 5 consecutive zeros, API is blocking → stop brand
            if consecutive_zero >= 5:
                print(f"    API blocking detected after {idx+1} videos. "
                      f"Stopping {brand}.")
                break

            time.sleep(random.uniform(1.0, 2.5))

        print(f"  [{brand}] New comments: {brand_new}")

    final_total = print_status(conn)
    print(f"\n  SESSION SUMMARY:")
    print(f"    New comments: {grand_total_new}")
    print(f"    Before: {current_total} -> After: {final_total}")

    conn.close()
    print(f"\n{'='*60}")
    print("  DONE!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
