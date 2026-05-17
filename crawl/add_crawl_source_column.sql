-- ============================================================
-- ADD crawl_source COLUMN (if not exists)
-- Phan biet du lieu Apify (technique 1) vs self-hosted (technique 2)
-- Chay: psql -h localhost -p 5434 -U sl_admin -d social_listening -f crawl/add_crawl_source_column.sql
-- ============================================================

DO $$
BEGIN
    -- tiktok_videos
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='raw' AND table_name='tiktok_videos' AND column_name='crawl_source'
    ) THEN
        ALTER TABLE raw.tiktok_videos ADD COLUMN crawl_source VARCHAR(50) DEFAULT 'apify';
        RAISE NOTICE 'Added crawl_source to raw.tiktok_videos';
    ELSE
        RAISE NOTICE 'crawl_source already exists in raw.tiktok_videos';
    END IF;

    -- facebook_posts
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='raw' AND table_name='facebook_posts' AND column_name='crawl_source'
    ) THEN
        ALTER TABLE raw.facebook_posts ADD COLUMN crawl_source VARCHAR(50) DEFAULT 'apify';
        RAISE NOTICE 'Added crawl_source to raw.facebook_posts';
    ELSE
        RAISE NOTICE 'crawl_source already exists in raw.facebook_posts';
    END IF;
END
$$;

-- Mark existing data as apify
UPDATE raw.tiktok_videos SET crawl_source = 'apify' WHERE crawl_source IS NULL;
UPDATE raw.facebook_posts SET crawl_source = 'apify' WHERE crawl_source IS NULL;

-- Verify
SELECT 'tiktok_videos' as tbl, crawl_source, COUNT(*) FROM raw.tiktok_videos GROUP BY crawl_source
UNION ALL
SELECT 'facebook_posts', crawl_source, COUNT(*) FROM raw.facebook_posts GROUP BY crawl_source
ORDER BY 1, 2;
