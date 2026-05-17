import json, time
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
    "phuc_long": "https://www.facebook.com/PhuclongCoffeeandTea",
    "highlands": "https://www.facebook.com/highlandscoffeevietnam",
    "katinat": "https://www.facebook.com/katinat.vn",
}

def crawl_fb(client, brand, url, n=100):
    print(f"\n[CRAWL] FB {brand} - {url}")
    try:
        run = client.actor("apify/facebook-posts-scraper").call(
            run_input={"startUrls": [{"url": url}], "resultsLimit": n}
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"  Got {len(items)} posts")
        return items
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

def insert_posts(conn, brand, items):
    if not items:
        return 0
    cur = conn.cursor()
    inserted = 0
    for item in items:
        try:
            pid = str(item.get("postId", item.get("id", item.get("url", "")[:128])))
            if not pid:
                continue
            text = item.get("text", item.get("message", "")) or ""
            ptype = item.get("type", "unknown") or "unknown"
            pub = item.get("time", item.get("timestamp", None))
            if pub and isinstance(pub, str):
                try:
                    pub = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                except:
                    pub = None
            likes = item.get("likes", item.get("likesCount", 0)) or 0
            shares = item.get("shares", item.get("sharesCount", 0)) or 0
            comments = item.get("comments", item.get("commentsCount", 0)) or 0
            reactions = item.get("reactionsBreakdown", item.get("reactions", None))
            rjson = json.dumps(reactions) if reactions else None
            ht = item.get("hashtags", [])
            hashtags = ",".join(ht) if isinstance(ht, list) else str(ht or "")
            purl = item.get("url", item.get("postUrl", "")) or ""
            cur.execute("""INSERT INTO raw.facebook_posts
                (post_id,brand,post_text,post_type,publish_time,likes_count,shares_count,comments_count,reactions_breakdown,hashtags,post_url,crawl_source)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'apify') ON CONFLICT(post_id) DO NOTHING""",
                (pid,brand,text,ptype,pub,likes,shares,comments,rjson,hashtags,purl))
            if cur.rowcount > 0:
                inserted += 1
        except:
            pass
    conn.commit()
    cur.close()
    print(f"  Inserted: {inserted}/{len(items)}")
    return inserted

if __name__ == "__main__":
    print("="*60)
    print("  FACEBOOK CRAWLER - 3 brands x 100 posts")
    print("="*60)
    client = ApifyClient(APIFY_TOKEN)
    conn = psycopg2.connect(**DB_CONFIG)
    total = 0
    for brand, url in BRANDS.items():
        items = crawl_fb(client, brand, url, 100)
        total += insert_posts(conn, brand, items)
        time.sleep(3)
    cur = conn.cursor()
    cur.execute("SELECT brand, COUNT(*) FROM raw.facebook_posts GROUP BY brand ORDER BY brand")
    print(f"\n{'='*60}")
    print("  RESULT:")
    for r in cur.fetchall():
        print(f"    {r[0]}: {r[1]} posts")
    cur.execute("SELECT COUNT(*) FROM raw.facebook_posts")
    print(f"  TOTAL: {cur.fetchone()[0]} posts")
    print("="*60)
    cur.close()
    conn.close()
