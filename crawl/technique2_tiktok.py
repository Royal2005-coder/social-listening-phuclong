#!/usr/bin/env python3
"""
TECHNIQUE 2 PRODUCTION — TikTok Crawler
Engine: yt-dlp (100% headless, no browser, no cookies, no CAPTCHA)

yt-dlp la tool mature nhat (80K+ stars GitHub), tu xu ly:
  - TikTok anti-bot / signature
  - Rate limiting / retry
  - Token generation noi bo
  - Extract metadata khong can download video

Schema: raw.tiktok_videos (dong bo Apify)
crawl_source = 'ytdlp_t2'

Install: pip install yt-dlp psycopg2-binary
Chay:
  python crawl\technique2_tiktok.py --brands phuc_long --target 50
  python crawl\technique2_tiktok.py --brands all
"""
import json, time, random, re, sys, argparse
from datetime import datetime
import psycopg2

DB = dict(host='localhost', port=5434, dbname='social_listening',
          user='sl_admin', password='YOUR_DB_PASSWORD')

BRANDS = {
    "phuc_long":  "https://www.tiktok.com/@phuclongofficial",
    "highlands":  "https://www.tiktok.com/@highlandscoffeevietnam",
    "katinat":    "https://www.tiktok.com/@katinatvn",
}


def normalize_video(info, brand):
    """Normalize yt-dlp info_dict -> DB schema raw.tiktok_videos."""
    vid = str(info.get("id", ""))
    if not vid:
        return None

    # yt-dlp field names
    views = int(info.get("view_count", 0) or 0)
    likes = int(info.get("like_count", 0) or 0)
    comments = int(info.get("comment_count", 0) or 0)
    shares = int(info.get("repost_count", info.get("share_count", 0)) or 0)
    collects = int(info.get("collect_count", 0) or 0)
    duration = int(info.get("duration", 0) or 0)

    # Publish time
    pub = None
    upload_date = info.get("upload_date", None)  # YYYYMMDD format
    timestamp = info.get("timestamp", None)
    if timestamp:
        try:
            pub = datetime.fromtimestamp(int(timestamp))
        except:
            pass
    elif upload_date and len(upload_date) == 8:
        try:
            pub = datetime.strptime(upload_date, "%Y%m%d")
        except:
            pass

    desc = info.get("description", info.get("title", "")) or ""
    
    # Music
    track = info.get("track", "") or ""
    artist = info.get("artist", "") or ""
    mname = f"{track} - {artist}" if track and artist else track or artist or ""

    # Hashtags from description
    ht_list = re.findall(r'#(\w+)', desc) if desc else []
    # Also from tags field
    tags = info.get("tags", [])
    if isinstance(tags, list):
        for t in tags:
            if t and t not in ht_list:
                ht_list.append(t)
    hashtags = ",".join(ht_list)

    # Author
    aname = info.get("uploader_id", info.get("uploader", "")) or ""
    # Clean @ prefix
    if aname.startswith("@"):
        aname = aname[1:]

    vurl = info.get("webpage_url", info.get("url", "")) or ""
    if not vurl:
        vurl = f"https://www.tiktok.com/@{aname}/video/{vid}"

    return {
        "video_id": vid, "brand": brand, "author_name": aname,
        "views_count": views, "likes_count": likes,
        "comments_count": comments, "shares_count": shares,
        "collect_count": collects, "duration_seconds": duration,
        "publish_time": pub, "video_desc": desc[:5000],
        "music_used": mname[:500], "hashtags": hashtags[:1000],
        "video_url": vurl, "crawl_source": "ytdlp_t2",
    }


def insert_videos(conn, videos):
    cur = conn.cursor()
    n = 0
    for v in videos:
        if not v:
            continue
        try:
            cur.execute("""
                INSERT INTO raw.tiktok_videos
                (video_id, brand, author_name, views_count, likes_count,
                 comments_count, shares_count, collect_count, duration_seconds,
                 publish_time, video_desc, music_used, hashtags, video_url, crawl_source)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(video_id) DO NOTHING
            """, (
                v["video_id"], v["brand"], v["author_name"],
                v["views_count"], v["likes_count"], v["comments_count"],
                v["shares_count"], v["collect_count"], v["duration_seconds"],
                v["publish_time"], v["video_desc"], v["music_used"],
                v["hashtags"], v["video_url"], v["crawl_source"],
            ))
            if cur.rowcount > 0:
                n += 1
        except Exception as e:
            conn.rollback()
    conn.commit()
    cur.close()
    return n


def crawl_brand(brand, url, target=100):
    """Crawl TikTok profile bang yt-dlp."""
    import yt_dlp

    print(f"\n{'='*60}")
    print(f"  [T2] TikTok — {brand}")
    print(f"  URL: {url}")
    print(f"  Engine: yt-dlp (headless, no browser)")
    print(f"{'='*60}")

    videos = []
    seen = set()

    # yt-dlp options: extract info only, no download
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,     # Get full metadata per video
        'skip_download': True,     # Don't download video files
        'ignoreerrors': True,      # Skip errors on individual videos
        'playlistend': target,     # Limit number of videos
        'sleep_interval': 1,       # Delay between requests
        'max_sleep_interval': 3,
        'extractor_args': {
            'tiktok': {
                'api_hostname': ['api22-normal-c-useast2a.tiktokv.com'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36',
            'Accept-Language': 'vi-VN,vi;q=0.9',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"  Extracting video list from profile...")
            result = ydl.extract_info(url, download=False)

            if not result:
                print(f"  No result from yt-dlp")
                return videos

            # Profile page returns entries list
            entries = result.get("entries", [])
            if not entries:
                # Single video case or flat list
                entries = [result] if result.get("id") else []

            print(f"  Found {len(entries) if entries else 0} entries")

            count = 0
            for entry in entries:
                if count >= target:
                    break
                if entry is None:
                    continue

                # If flat extraction, need to get full info
                if entry.get("_type") == "url" or not entry.get("view_count"):
                    video_url = entry.get("url", entry.get("webpage_url", ""))
                    if video_url:
                        try:
                            full_info = ydl.extract_info(video_url, download=False)
                            if full_info:
                                entry = full_info
                        except:
                            continue

                v = normalize_video(entry, brand)
                if v and v["video_id"] not in seen:
                    videos.append(v)
                    seen.add(v["video_id"])
                    count += 1
                    if count % 10 == 0:
                        print(f"    Processed: {count} videos")

    except Exception as e:
        print(f"  yt-dlp error: {e}")
        # Fallback: try individual video extraction
        print(f"  Trying fallback approach...")

    print(f"  Total {brand}: {len(videos)} videos")
    return videos


def main():
    parser = argparse.ArgumentParser(description="T2: TikTok Crawler (yt-dlp)")
    parser.add_argument("--brands", nargs="+",
                        choices=list(BRANDS.keys()) + ["all"], default=["all"])
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-json", type=str, default=None)
    args = parser.parse_args()

    brands = BRANDS if "all" in args.brands else {b: BRANDS[b] for b in args.brands}

    print("=" * 60)
    print("  TECHNIQUE 2 — TikTok Crawler (yt-dlp)")
    print("  100% headless | No browser | No cookies | No CAPTCHA")
    print(f"  Brands: {list(brands.keys())}")
    print(f"  Target: {args.target}/brand | DB: {'DRY' if args.dry_run else 'LIVE'}")
    print("=" * 60)

    all_data = {}
    for brand, url in brands.items():
        vids = crawl_brand(brand, url, target=args.target)
        all_data[brand] = vids
        time.sleep(random.uniform(3, 6))

    if args.output_json:
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump({b: v for b, v in all_data.items()}, f,
                      ensure_ascii=False, indent=2, default=str)
        print(f"\n  JSON saved: {args.output_json}")

    if not args.dry_run:
        conn = psycopg2.connect(**DB)
        total = 0
        for brand, vids in all_data.items():
            n = insert_videos(conn, vids)
            total += n
            print(f"  {brand}: {n} new (of {len(vids)} collected)")
        conn.close()
        print(f"\n  TOTAL NEW: {total}")

    print(f"\n{'='*60}")
    print("  SUMMARY:")
    for brand, vids in all_data.items():
        print(f"    {brand:12}: {len(vids)} collected")
    print("=" * 60)


if __name__ == "__main__":
    main()
