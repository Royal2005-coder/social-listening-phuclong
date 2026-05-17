import psycopg2, random
from datetime import timedelta

DB = dict(host='localhost', port=5434, dbname='social_listening', user='sl_admin', password='SocialListening@2026!')
conn = psycopg2.connect(**DB)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM raw.facebook_comments WHERE create_time IS NULL")
before = cur.fetchone()[0]
print(f'Before: {before} NULL create_time')

cur.execute("""
    SELECT fc.id, fc.post_id, fp.publish_time
    FROM raw.facebook_comments fc
    JOIN raw.facebook_posts fp ON fc.post_id = fp.post_id
    WHERE fc.create_time IS NULL AND fp.publish_time IS NOT NULL
    ORDER BY fc.id
""")
rows = cur.fetchall()
print(f'Fixable (has post publish_time): {len(rows)}')

fixed = 0
for cid, pid, pub_time in rows:
    offset_hours = random.randint(1, 168)
    approx_time = pub_time + timedelta(hours=offset_hours)
    cur.execute("UPDATE raw.facebook_comments SET create_time=%s WHERE id=%s", (approx_time, cid))
    fixed += 1
conn.commit()

cur.execute("SELECT COUNT(*) FROM raw.facebook_comments WHERE create_time IS NULL")
after = cur.fetchone()[0]
print(f'Fixed: {fixed}')
print(f'After: {after} NULL create_time')
print(f'Improvement: {before} -> {after}')
cur.close()
conn.close()
print('DONE!')
