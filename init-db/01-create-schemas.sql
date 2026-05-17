CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS clean;
CREATE SCHEMA IF NOT EXISTS features;
CREATE SCHEMA IF NOT EXISTS sentiment;
CREATE SCHEMA IF NOT EXISTS ml;

CREATE TABLE raw.tiktok_videos (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(64) UNIQUE NOT NULL,
    brand VARCHAR(32) NOT NULL,
    author_name VARCHAR(128),
    views_count BIGINT DEFAULT 0,
    likes_count BIGINT DEFAULT 0,
    comments_count BIGINT DEFAULT 0,
    shares_count BIGINT DEFAULT 0,
    collect_count BIGINT DEFAULT 0,
    duration_seconds FLOAT,
    publish_time TIMESTAMP,
    video_desc TEXT,
    music_used VARCHAR(512),
    hashtags TEXT,
    video_url VARCHAR(512),
    crawl_source VARCHAR(32) DEFAULT 'apify',
    crawl_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE raw.facebook_posts (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(128) UNIQUE NOT NULL,
    brand VARCHAR(32) NOT NULL,
    post_text TEXT,
    post_type VARCHAR(32),
    publish_time TIMESTAMP,
    likes_count BIGINT DEFAULT 0,
    shares_count BIGINT DEFAULT 0,
    comments_count BIGINT DEFAULT 0,
    reactions_breakdown JSONB,
    hashtags TEXT,
    post_url VARCHAR(512),
    crawl_source VARCHAR(32) DEFAULT 'apify',
    crawl_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE raw.tiktok_comments (
    id SERIAL PRIMARY KEY,
    comment_id VARCHAR(64),
    video_id VARCHAR(64),
    brand VARCHAR(32) NOT NULL,
    comment_text TEXT NOT NULL,
    like_count INT DEFAULT 0,
    reply_count INT DEFAULT 0,
    create_time TIMESTAMP,
    user_nickname VARCHAR(128),
    crawl_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE raw.facebook_comments (
    id SERIAL PRIMARY KEY,
    comment_id VARCHAR(128),
    post_id VARCHAR(128),
    brand VARCHAR(32) NOT NULL,
    comment_text TEXT NOT NULL,
    like_count INT DEFAULT 0,
    reply_count INT DEFAULT 0,
    create_time TIMESTAMP,
    user_name VARCHAR(128),
    crawl_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE clean.tiktok (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(64) UNIQUE NOT NULL,
    brand VARCHAR(32) NOT NULL,
    views_count BIGINT,
    likes_count BIGINT,
    comments_count BIGINT,
    shares_count BIGINT,
    collect_count BIGINT,
    duration_seconds FLOAT,
    publish_time TIMESTAMP,
    video_desc TEXT,
    music_used VARCHAR(512),
    hashtags TEXT,
    is_outlier BOOLEAN DEFAULT FALSE,
    clean_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE clean.facebook (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(128) UNIQUE NOT NULL,
    brand VARCHAR(32) NOT NULL,
    post_text TEXT,
    post_type VARCHAR(32),
    publish_time TIMESTAMP,
    likes_count BIGINT,
    shares_count BIGINT,
    comments_count BIGINT,
    reactions_breakdown JSONB,
    hashtags TEXT,
    is_outlier BOOLEAN DEFAULT FALSE,
    clean_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE clean.comments (
    id SERIAL PRIMARY KEY,
    comment_id VARCHAR(128),
    content_id VARCHAR(128),
    platform VARCHAR(16) NOT NULL,
    brand VARCHAR(32) NOT NULL,
    comment_text TEXT NOT NULL,
    text_cleaned TEXT,
    word_count INT,
    is_vietnamese BOOLEAN DEFAULT TRUE,
    like_count INT DEFAULT 0,
    reply_count INT DEFAULT 0,
    create_time TIMESTAMP,
    clean_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE features.engineered (
    id SERIAL PRIMARY KEY,
    content_id VARCHAR(128) NOT NULL,
    platform VARCHAR(16) NOT NULL,
    brand VARCHAR(32) NOT NULL,
    engagement_rate FLOAT,
    total_engagement BIGINT,
    posting_hour INT,
    time_category VARCHAR(16),
    day_of_week VARCHAR(16),
    hashtag_count INT,
    content_type VARCHAR(32),
    has_music BOOLEAN,
    caption_length INT,
    days_since_published INT,
    views_count BIGINT,
    duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sentiment.results (
    id SERIAL PRIMARY KEY,
    comment_id VARCHAR(128),
    content_id VARCHAR(128),
    platform VARCHAR(16),
    brand VARCHAR(32),
    comment_text TEXT,
    sentiment_label VARCHAR(16),
    sentiment_score FLOAT,
    model_version VARCHAR(64) DEFAULT 'wonrax/phobert-base-vietnamese-sentiment',
    inference_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sentiment.validation (
    id SERIAL PRIMARY KEY,
    comment_id VARCHAR(128),
    comment_text TEXT,
    manual_label_1 VARCHAR(16),
    manual_label_2 VARCHAR(16),
    phobert_label VARCHAR(16),
    phobert_score FLOAT,
    is_agree BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ml.model_results (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(64),
    metric_name VARCHAR(64),
    metric_value FLOAT,
    train_date TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE ml.feature_importance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(64),
    feature_name VARCHAR(64),
    importance_score FLOAT,
    rank INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ml.clusters (
    id SERIAL PRIMARY KEY,
    content_id VARCHAR(128),
    platform VARCHAR(16),
    brand VARCHAR(32),
    cluster_label VARCHAR(16),
    cluster_id INT,
    distance_to_center FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_raw_tt_brand ON raw.tiktok_videos(brand);
CREATE INDEX idx_raw_fb_brand ON raw.facebook_posts(brand);
CREATE INDEX idx_raw_ttc_video ON raw.tiktok_comments(video_id);
CREATE INDEX idx_raw_fbc_post ON raw.facebook_comments(post_id);
CREATE INDEX idx_clean_comments_brand ON clean.comments(brand, platform);
CREATE INDEX idx_features_brand ON features.engineered(brand, platform);
CREATE INDEX idx_sentiment_brand ON sentiment.results(brand, platform);

CREATE USER sl_reader WITH PASSWORD 'SLReader@2026!';
GRANT CONNECT ON DATABASE social_listening TO sl_reader;
GRANT USAGE ON SCHEMA raw, clean, features, sentiment, ml TO sl_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO sl_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA clean TO sl_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA features TO sl_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA sentiment TO sl_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA ml TO sl_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO sl_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA clean GRANT SELECT ON TABLES TO sl_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA features GRANT SELECT ON TABLES TO sl_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA sentiment GRANT SELECT ON TABLES TO sl_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA ml GRANT SELECT ON TABLES TO sl_reader;
