import psycopg2, json, re, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DB = dict(host='localhost',port=5434,dbname='social_listening',user='sl_admin',password='SocialListening@2026!')
STATE_FILE = Path('crawl/.cookies/fb_state.json')

conn = psycopg2.connect(**DB)
cur = conn.cursor()

cur.execute("SELECT post_id, post_url, brand, likes_count FROM raw.facebook_posts WHERE reactions_breakdown IS NULL AND post_url IS NOT NULL AND post_url != '' ORDER BY likes_count DESC")
posts = cur.fetchall()
print(f'Posts to fix: {len(posts)}')

fixed = 0
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    ctx = browser.new_context(storage_state=str(STATE_FILE),
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
        viewport={'width':390,'height':844}, locale='vi-VN')
    ctx.route('**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2}', lambda r: r.abort())
    page = ctx.new_page()

    for idx, (pid, purl, brand, likes) in enumerate(posts):
        url = purl.replace('www.facebook.com','m.facebook.com').split('?')[0]
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=12000)
            time.sleep(1.5)
            html = page.content()
            m = re.search(r'(\d[\d,.]*[KMB]?)\s*(ng.{1,5}i|people|person)', html)
            if not m:
                m = re.search(r'aria-label="[^"]*?(\d[\d,.]*[KMB]?)[^"]*?(c.{1,3}m x.{1,3}c|reaction)', html)
            if m:
                raw = m.group(1).replace(',','.').upper()
                val = float(re.sub(r'[KMB]','',raw))
                if 'K' in raw: val *= 1000
                elif 'M' in raw: val *= 1000000
                reactions = json.dumps({'total':int(val),'like':likes})
                cur.execute('UPDATE raw.facebook_posts SET reactions_breakdown=%s WHERE post_id=%s',(reactions,pid))
                conn.commit()
                fixed += 1
        except:
            pass
        time.sleep(0.5)
        if (idx+1) % 20 == 0:
            print(f'  {idx+1}/{len(posts)} | fixed={fixed}')

    ctx.close()
    browser.close()

cur.execute("SELECT COUNT(*) FROM raw.facebook_posts WHERE reactions_breakdown IS NOT NULL")
has = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM raw.facebook_posts")
total = cur.fetchone()[0]
print(f'Fixed: {fixed} | Total with reactions: {has}/{total}')
cur.close()
conn.close()
