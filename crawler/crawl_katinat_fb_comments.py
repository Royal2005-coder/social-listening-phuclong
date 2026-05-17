from apify_client import ApifyClient
import psycopg2, time
from datetime import datetime

TOKEN = 'apify_api_YOUR_TOKEN_HERE'
DB = dict(host='localhost',port=5434,dbname='social_listening',user='sl_admin',password='YOUR_DB_PASSWORD')

client = ApifyClient(TOKEN)
conn = psycopg2.connect(**DB)
cur = conn.cursor()

# Katinat FB posts chua co comment (skip da crawl)
cur.execute("""
    SELECT fp.post_id, fp.post_url 
    FROM raw.facebook_posts fp
    LEFT JOIN (SELECT DISTINCT post_id FROM raw.facebook_comments WHERE brand='katinat') fc ON fp.post_id = fc.post_id
    WHERE fp.brand='katinat' AND fp.post_url IS NOT NULL AND fp.post_url != '' AND fc.post_id IS NULL
    ORDER BY (fp.likes_count+fp.comments_count+fp.shares_count) DESC
    LIMIT 20
""")
posts = cur.fetchall()
print(f'Katinat FB posts to crawl: {len(posts)}')

for pid, purl in posts:
    try:
        run = client.actor('apify/facebook-comments-scraper').call(run_input={'startUrls':[{'url':purl}],'resultsLimit':50})
        items = list(client.dataset(run['defaultDatasetId']).iterate_items())
        n = 0
        for item in items:
            txt = item.get('text',item.get('message','')) or ''
            if len(txt.strip())<2: continue
            cid = str(item.get('id',item.get('commentId','')))
            lk = item.get('likesCount',0) or 0
            rp = item.get('repliesCount',0) or 0
            ct = item.get('date',None)
            if ct and isinstance(ct,str):
                try: ct = datetime.fromisoformat(ct.replace('Z','+00:00'))
                except: ct = None
            usr = item.get('profileName','') or ''
            try:
                cur.execute('INSERT INTO raw.facebook_comments(comment_id,post_id,brand,comment_text,like_count,reply_count,create_time,user_name) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(cid,pid,'katinat',txt,lk,rp,ct,usr))
                n += 1
            except:
                conn.rollback()
        conn.commit()
        print(f'  {pid[:30]}: {n} cmt')
    except Exception as e:
        print(f'  {pid[:30]}: ERR {e}')
        if 'Monthly usage hard limit' in str(e):
            print('  QUOTA HET - DUNG LAI')
            break
    time.sleep(2)

# Final check
print('\n' + '='*60)
print('FINAL COMPLETE DATA CHECK:')
for tbl in ['raw.tiktok_videos','raw.facebook_posts','raw.tiktok_comments','raw.facebook_comments']:
    cur.execute(f'SELECT count(id) FROM {tbl}')
    print(f'  {tbl}: {cur.fetchone()[0]}')

print('\nCOMMENTS BY BRAND + PLATFORM:')
cur.execute("SELECT 'TikTok' as p, brand, count(id) FROM raw.tiktok_comments GROUP BY brand UNION ALL SELECT 'Facebook', brand, count(id) FROM raw.facebook_comments GROUP BY brand ORDER BY 1,2")
total = 0
for r in cur.fetchall():
    print(f'  {r[0]:10} | {r[1]:12}: {r[2]:>5}')
    total += r[2]
print(f'  {"TOTAL":10} | {"":12}: {total:>5}')

print('\nTIMESPAN CHECK:')
cur.execute("SELECT brand, min(publish_time)::date, max(publish_time)::date, max(publish_time)::date - min(publish_time)::date as days FROM raw.tiktok_videos WHERE publish_time IS NOT NULL GROUP BY brand ORDER BY brand")
print('  TikTok Videos:')
for r in cur.fetchall():
    print(f'    {r[0]:12}: {r[1]} -> {r[2]} ({r[3]} days)')

cur.execute("SELECT brand, min(publish_time)::date, max(publish_time)::date, max(publish_time)::date - min(publish_time)::date as days FROM raw.facebook_posts WHERE publish_time IS NOT NULL GROUP BY brand ORDER BY brand")
print('  Facebook Posts:')
for r in cur.fetchall():
    print(f'    {r[0]:12}: {r[1]} -> {r[2]} ({r[3]} days)')

cur.execute("SELECT min(publish_time)::date as start, max(publish_time)::date as end FROM (SELECT publish_time FROM raw.tiktok_videos WHERE publish_time IS NOT NULL UNION ALL SELECT publish_time FROM raw.facebook_posts WHERE publish_time IS NOT NULL) t")
r = cur.fetchone()
print(f'\n  OVERALL DATA TIMESPAN: {r[0]} -> {r[1]}')
print(f'  CRAWL DATE: {datetime.now().strftime("%Y-%m-%d")}')

cur.close()
conn.close()
print('\nDONE!')
