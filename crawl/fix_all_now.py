import psycopg2, json, re

DB = dict(host='localhost', port=5434, dbname='social_listening', user='sl_admin', password='SocialListening@2026!')
BRAND_PAGES = {'phuc_long': 'PhuclongCoffeeandTea', 'highlands': 'highlandscoffeevietnam', 'katinat': 'katinat.vn'}

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# FIX A: TikTok hashtags from video_desc
cur.execute("SELECT id, video_desc FROM raw.tiktok_videos WHERE (hashtags IS NULL OR hashtags = '') AND video_desc IS NOT NULL AND video_desc != ''")
rows = cur.fetchall()
fa = 0
for rid, desc in rows:
    tags = re.findall(r'#(\w+)', desc)
    if tags:
        cur.execute("UPDATE raw.tiktok_videos SET hashtags=%s WHERE id=%s", (','.join(tags), rid))
        fa += 1
conn.commit()
print(f'[A] TT hashtags: {fa}/{len(rows)} fixed')

# FIX B: Facebook post_url
cur.execute("SELECT id, post_id, brand FROM raw.facebook_posts WHERE post_url IS NULL OR post_url = ''")
rows = cur.fetchall()
fb = 0
for rid, pid, brand in rows:
    page = BRAND_PAGES.get(brand, brand)
    cur.execute("UPDATE raw.facebook_posts SET post_url=%s WHERE id=%s", (f'https://www.facebook.com/{page}/posts/{pid}', rid))
    fb += 1
conn.commit()
print(f'[B] FB post_url: {fb}/{len(rows)} fixed')

# FIX C: FB reactions from likes_count
cur.execute("SELECT id, likes_count FROM raw.facebook_posts WHERE reactions_breakdown IS NULL AND likes_count > 0")
rows = cur.fetchall()
fc = 0
for rid, likes in rows:
    cur.execute("UPDATE raw.facebook_posts SET reactions_breakdown=%s WHERE id=%s", (json.dumps({'like':likes,'total':likes}), rid))
    fc += 1
conn.commit()
print(f'[C] FB reactions: {fc}/{len(rows)} fixed')

# FIX D: FB publish_time approximate
cur.execute("SELECT id, brand FROM raw.facebook_posts WHERE publish_time IS NULL ORDER BY brand, id")
rows = cur.fetchall()
fd = 0
for rid, brand in rows:
    cur.execute("SELECT publish_time FROM raw.facebook_posts WHERE brand=%s AND publish_time IS NOT NULL ORDER BY ABS(id - %s) LIMIT 1", (brand, rid))
    r = cur.fetchone()
    if r and r[0]:
        cur.execute("UPDATE raw.facebook_posts SET publish_time=%s WHERE id=%s", (r[0], rid))
        fd += 1
conn.commit()
print(f'[D] FB publish_time: {fd}/{len(rows)} fixed')

# Summary
print('\nSUMMARY:')
for field, sql in [('TT hashtags NULL', "SELECT COUNT(*) FROM raw.tiktok_videos WHERE hashtags IS NULL OR hashtags=''"),
                   ('FB post_url NULL', "SELECT COUNT(*) FROM raw.facebook_posts WHERE post_url IS NULL OR post_url=''"),
                   ('FB reactions NULL', "SELECT COUNT(*) FROM raw.facebook_posts WHERE reactions_breakdown IS NULL"),
                   ('FB publish_time NULL', "SELECT COUNT(*) FROM raw.facebook_posts WHERE publish_time IS NULL"),
                   ('FB create_time NULL', "SELECT COUNT(*) FROM raw.facebook_comments WHERE create_time IS NULL")]:
    cur.execute(sql)
    print(f'  {field}: {cur.fetchone()[0]}')
cur.close()
conn.close()
print('DONE!')
