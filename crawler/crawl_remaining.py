from apify_client import ApifyClient
import psycopg2, time
from datetime import datetime

TOKEN = 'apify_api_YOUR_TOKEN_HERE'
DB = dict(host='localhost',port=5434,dbname='social_listening',user='sl_admin',password='YOUR_DB_PASSWORD')

client = ApifyClient(TOKEN)
conn = psycopg2.connect(**DB)
cur = conn.cursor()

for brand in ['highlands','katinat']:
    print(f'\n=== {brand} TikTok Comments ===')
    cur.execute('SELECT video_id, video_url FROM raw.tiktok_videos WHERE brand=%s ORDER BY (likes_count+comments_count+shares_count) DESC LIMIT 20', (brand,))
    rows = cur.fetchall()
    for vid, vurl in rows:
        if not vurl: vurl = f'https://www.tiktok.com/@/video/{vid}'
        try:
            run = client.actor('clockworks/tiktok-comments-scraper').call(run_input={'postURLs':[vurl],'maxComments':50})
            items = list(client.dataset(run['defaultDatasetId']).iterate_items())
            n = 0
            for item in items:
                txt = item.get('text',item.get('comment','')) or ''
                if len(txt.strip())<2: continue
                cid = str(item.get('cid',item.get('id','')))
                lk = item.get('diggCount',0) or 0
                rp = item.get('replyCommentTotal',0) or 0
                ct = item.get('createTime',None)
                if ct and isinstance(ct,(int,float)): ct = datetime.fromtimestamp(ct)
                usr = item.get('uniqueId','') or ''
                try:
                    cur.execute('INSERT INTO raw.tiktok_comments(comment_id,video_id,brand,comment_text,like_count,reply_count,create_time,user_nickname) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(cid,vid,brand,txt,lk,rp,ct,usr))
                    n += 1
                except:
                    conn.rollback()
            conn.commit()
            print(f'  {vid[:20]}: {n} comments')
        except Exception as e:
            print(f'  {vid[:20]}: ERR {e}')
        time.sleep(2)

    print(f'\n=== {brand} Facebook Comments ===')
    cur.execute('SELECT post_id, post_url FROM raw.facebook_posts WHERE brand=%s ORDER BY (likes_count+comments_count+shares_count) DESC LIMIT 20', (brand,))
    rows = cur.fetchall()
    for pid, purl in rows:
        if not purl: continue
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
                    cur.execute('INSERT INTO raw.facebook_comments(comment_id,post_id,brand,comment_text,like_count,reply_count,create_time,user_name) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(cid,pid,brand,txt,lk,rp,ct,usr))
                    n += 1
                except:
                    conn.rollback()
            conn.commit()
            print(f'  {pid[:25]}: {n} cmt')
        except Exception as e:
            print(f'  {pid[:25]}: ERR {e}')
        time.sleep(2)

# Final check
print('\n' + '='*50)
print('FINAL DATA CHECK:')
for tbl in ['raw.tiktok_videos','raw.facebook_posts','raw.tiktok_comments','raw.facebook_comments']:
    cur.execute(f'SELECT COUNT(*) FROM {tbl}')
    print(f'  {tbl}: {cur.fetchone()[0]}')

print('\nCOMMENTS BY BRAND:')
cur.execute("SELECT 'TikTok' as p, brand, count(id) FROM raw.tiktok_comments GROUP BY brand UNION ALL SELECT 'Facebook', brand, count(id) FROM raw.facebook_comments GROUP BY brand ORDER BY 1,2")
total = 0
for r in cur.fetchall():
    print(f'  {r[0]} | {r[1]}: {r[2]}')
    total += r[2]
print(f'  TOTAL COMMENTS: {total}')

cur.close()
conn.close()
