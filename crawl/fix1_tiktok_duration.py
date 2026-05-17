#!/usr/bin/env python3
"""
FIX 1: TikTok video duration — yt-dlp re-extract
Apify tra duration=0, yt-dlp extract chinh xac
"""
import psycopg2, time, random

DB = dict(host='localhost', port=5434, dbname='social_listening',
          user='sl_admin', password='SocialListening@2026!')

def main():
    import yt_dlp
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # Lay videos co duration = 0 hoac NULL
    cur.execute("""
        SELECT video_id, video_url, brand, duration_seconds
        FROM raw.tiktok_videos
        WHERE (duration_seconds IS NULL OR duration_seconds <= 1)
          AND video_url IS NOT NULL AND video_url != ''
        ORDER BY brand
    """)
    videos = cur.fetchall()
    print(f"Videos need duration fix: {len(videos)}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
    }

    fixed = 0
    errors = 0

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for idx, (vid, vurl, brand, old_dur) in enumerate(videos):
            try:
                info = ydl.extract_info(vurl, download=False)
                if info and info.get('duration'):
                    new_dur = int(info['duration'])
                    cur.execute(
                        "UPDATE raw.tiktok_videos SET duration_seconds=%s WHERE video_id=%s",
                        (new_dur, vid))
                    conn.commit()
                    fixed += 1
                    if fixed % 20 == 0:
                        print(f"  Fixed: {fixed}/{len(videos)}")
            except Exception as e:
                errors += 1
            time.sleep(random.uniform(0.5, 1.5))

    # Verify
    cur.execute("""
        SELECT brand,
               COUNT(*) as total,
               SUM(CASE WHEN duration_seconds > 1 THEN 1 ELSE 0 END) as has_dur,
               ROUND(AVG(CASE WHEN duration_seconds > 1 THEN duration_seconds END)) as avg_dur,
               MIN(CASE WHEN duration_seconds > 1 THEN duration_seconds END) as min_dur,
               MAX(CASE WHEN duration_seconds > 1 THEN duration_seconds END) as max_dur
        FROM raw.tiktok_videos GROUP BY brand ORDER BY brand
    """)
    print(f"\nRESULT:")
    print(f"  Fixed: {fixed} | Errors: {errors}")
    print(f"  {'Brand':12} | {'Total':>5} | {'HasDur':>6} | {'AvgDur':>6} | {'Min':>4} | {'Max':>4}")
    for r in cur.fetchall():
        print(f"  {r[0]:12} | {r[1]:>5} | {r[2]:>6} | {r[3]:>6}s | {r[4]:>4}s | {r[5]:>4}s")

    cur.close()
    conn.close()
    print("DONE!")

if __name__ == "__main__":
    main()
