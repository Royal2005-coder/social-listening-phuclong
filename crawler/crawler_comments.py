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

TOP_N = 20

def get_top_tt(conn, brand):
    cur = conn.cursor()
    cur.execute("SELECT video_id, video_url FROM raw.tiktok_videos WHERE brand=%s ORDER BY (likes_count+comments_count+shares_count) DESC LIMIT %s", (brand, TOP_N))
    r = cur.fetchall(); cur.close(); return r

def get_top_fb(conn, brand):
    cur = conn.cursor()
    cur.execute("SELECT post_id, post_url FROM raw.facebook_posts WHERE brand=%s ORDER BY (likes_count+comments_count+shares_count) DESC LIMIT %s", (brand, TOP_N))
    r = cur.fetchall(); cur.close(); return r

def crawl_tt_comments(client, url):
    try:
        run = client.actor("clockworks/tiktok-comments-scraper").call(run_input={"postURLs": [url], "maxComments": 50})
        return list(client.dataset(run["defaultDatasetId"]).iterate_items())
    except Exception as e:
        print(f"    warn: {e}"); return []

def crawl_fb_comments(client, url):
    try:
        run = client.actor("apify/facebook-comments-scraper").call(run_input={"startUrls": [{"url": url}], "resultsLimit": 50})
        return list(client.dataset(run["defaultDatasetId"]).iterate_items())
    except Exception as e:
        print(f"    warn: {e}"); return []

def insert_tt_cmt(conn, brand, vid, items):
    cur = conn.cursor(); n = 0
    for item in items:
        txt = item.get("text", item.get("comment", "")) or ""
        if len(txt.strip()) < 2: continue
        cid = str(item.get("cid", item.get("id", "")))
        lk = item.get("diggCount", item.get("likes", 0)) or 0
        rp = item.get("replyCommentTotal", 0) or 0
        ct = item.get("createTime", None)
        if ct and isinstance(ct, (int,float)): ct = datetime.fromtimestamp(ct)
        usr = item.get("uniqueId", item.get("nickname", "")) or ""
        try:
            cur.execute("INSERT INTO raw.tiktok_comments(comment_id,video_id,brand,comment_text,like_count,reply_count,create_time,user_nickname) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                (cid,vid,brand,txt,lk,rp,ct,usr)); n += 1
        except: pass
    conn.commit(); cur.close(); return n

def insert_fb_cmt(conn, brand, pid, items):
    cur = conn.cursor(); n = 0
    for item in items:
        txt = item.get("text", item.get("message", "")) or ""
        if len(txt.strip()) < 2: continue
        cid = str(item.get("id", item.get("commentId", "")))
        lk = item.get("likesCount", item.get("likes", 0)) or 0
        rp = item.get("repliesCount", 0) or 0
        ct = item.get("date", item.get("timestamp", None))
        if ct and isinstance(ct, str):
            try: ct = datetime.fromisoformat(ct.replace("Z","+00:00"))
            except: ct = None
        usr = item.get("profileName", item.get("author", "")) or ""
        try:
            cur.execute("INSERT INTO raw.facebook_comments(comment_id,post_id,brand,comment_text,like_count,reply_count,create_time,user_name) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                (cid,pid,brand,txt,lk,rp,ct,usr)); n += 1
        except: pass
    conn.commit(); cur.close(); return n

if __name__ == "__main__":
    print("="*60)
    print("  COMMENTS CRAWLER - top 20 per brand")
    print("="*60)
    client = ApifyClient(APIFY_TOKEN)
    conn = psycopg2.connect(**DB_CONFIG)
    brands = ["phuc_long", "highlands", "katinat"]
    for brand in brands:
        print(f"\n--- {brand} TikTok ---")
        for vid, vurl in get_top_tt(conn, brand):
            if not vurl: vurl = f"https://www.tiktok.com/@/video/{vid}"
            items = crawl_tt_comments(client, vurl)
            n = insert_tt_cmt(conn, brand, vid, items)
            print(f"  {vid[:20]}: {n} comments")
            time.sleep(2)
        print(f"\n--- {brand} Facebook ---")
        for pid, purl in get_top_fb(conn, brand):
            if not purl: continue
            items = crawl_fb_comments(client, purl)
            n = insert_fb_cmt(conn, brand, pid, items)
            print(f"  {pid[:25]}: {n} comments")
            time.sleep(2)
    cur = conn.cursor()
    cur.execute("SELECT 'tiktok' as p, COUNT(*) FROM raw.tiktok_comments UNION ALL SELECT 'facebook', COUNT(*) FROM raw.facebook_comments")
    print(f"\n{'='*60}")
    print("  COMMENTS TOTAL:")
    for r in cur.fetchall(): print(f"    {r[0]}: {r[1]}")
    cur.close(); conn.close()
