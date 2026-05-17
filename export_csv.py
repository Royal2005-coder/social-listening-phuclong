import psycopg2, pandas as pd, os
conn = psycopg2.connect(host='localhost',port=5434,dbname='social_listening',user='sl_admin',password='SocialListening@2026!')
os.makedirs('data/raw', exist_ok=True)
for tbl in ['tiktok_videos','facebook_posts','tiktok_comments','facebook_comments']:
    df = pd.read_sql(f'SELECT * FROM raw.{tbl}', conn)
    df.to_csv(f'data/raw/{tbl}.csv', index=False, encoding='utf-8-sig')
    print(f'{tbl}: {len(df)} rows')
conn.close()
