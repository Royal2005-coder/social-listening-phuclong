import json, time, sys
from datetime import datetime
from apify_client import ApifyClient
import psycopg2

APIFY_TOKEN = "apify_api_YOUR_TOKEN_HERE"

DB_CONFIG = {
    "host": "localhost", "port": 5434,
    "dbname": "social_listening", "user": "sl_admin",
    "password": "YOUR_DB_PASSWORD"
}

BRANDS = {
    "phuc_long": "https://www.tiktok.com/@phuclongofficial",
    "highlands": "https://www.tiktok.com/@highlandscoffeevietnam",
    "katinat": "https://www.tiktok.com/@katinat.coffee.tea",
}

def crawl_brand(client, brand, url, n=100):
    print(f"\n[CRAWL] {brand} - {url} (target: {n})")
    try:
        run = client.actor("clockworks/tiktok-scraper").call(
            run_input={"profiles": [url], "resultsPerPage": n, "shouldDownloadVideos": False, "shouldDownloadCovers": False}
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"  Got {len(items)} items from Apify")
        return items
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

def insert_videos(conn, brand, items):
    if not items:
        return 0
    cur = conn.cursor()
    inserted = 0
    for item in items:
        try:
            vid = str(item.get("id", item.get("videoId", "")))
            if not vid:
                continue
            views = item.get("playCount", item.get("views", 0)) or 0
            likes = item.get("diggCount", item.get("likes", 0)) or 0
            comments = item.get("commentCount", item.get("comments", 0)) or 0
            shares = item.get("shareCount", item.get("shares", 0)) or 0
            collects = item.get("collectCount", 0) or 0
            duration = item.get("duration", item.get("videoLength", 0)) or 0
            pub = item.get("createTime", item.get("publishTime", None))
            if pub and isinstance(pub, (int, float)):
                pub = datetime.fromtimestamp(pub)
            elif pub and isinstance(pub, str):
                try:
                    pub = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                except:
                    pub = None
            desc = item.get("text", item.get("desc", "")) or ""
            music = item.get("musicMeta", {})
            mname = music.get("musicName", "") if isinstance(music, dict) else str(music or "")
            ch = item.get("challenges", item.get("hashtags", []))
            hashtags = ",".join([c.get("title", str(c)) if isinstance(c, dict) else str(c) for c in ch]) if isinstance(ch, list) else ""
            author = item.get("authorMeta", {})
            aname = author.get("name", item.get("author", "")) if isinstance(author, dict) else ""
            vurl = item.get("webVideoUrl", item.get("url", f"https://www.tiktok.com/@/video/{vid}"))
            cur.execute("""INSERT INTO raw.tiktok_videos
                (video_id,brand,author_name,views_count,likes_count,comments_count,shares_count,collect_count,duration_seconds,publish_time,video_desc,music_used,hashtags,video_url,crawl_source)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'apify') ON CONFLICT(video_id) DO NOTHING""",
                (vid,brand,aname,views,likes,comments,shares,collects,duration,pub,desc,mname,hashtags,vurl))
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            pass
    conn.commit()
    cur.close()
    print(f"  Inserted: {inserted}/{len(items)}")
    return inserted

if __name__ == "__main__":
    print("="*60)
    print("  TIKTOK CRAWLER - 3 brands x 100 videos")
    print("="*60)
    client = ApifyClient(APIFY_TOKEN)
    conn = psycopg2.connect(**DB_CONFIG)
    total = 0
    for brand, url in BRANDS.items():
        items = crawl_brand(client, brand, url, 100)
        total += insert_videos(conn, brand, items)
        time.sleep(3)
    cur = conn.cursor()
    cur.execute("SELECT brand, COUNT(*) FROM raw.tiktok_videos GROUP BY brand ORDER BY brand")
    print(f"\n{'='*60}")
    print("  RESULT:")
    for r in cur.fetchall():
        print(f"    {r[0]}: {r[1]} videos")
    cur.execute("SELECT COUNT(*) FROM raw.tiktok_videos")
    print(f"  TOTAL: {cur.fetchone()[0]} videos")
    print("="*60)
    cur.close()
    conn.close()
