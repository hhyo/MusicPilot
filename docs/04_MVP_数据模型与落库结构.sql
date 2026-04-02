-- 04. MVP 数据模型与落库结构
-- Dialect: PostgreSQL 15+
-- 约定：
-- 1) 所有表使用 music_ 前缀
-- 2) created_at / updated_at 统一使用 timestamptz
-- 3) V1 以 JSONB 承载可演进规则字段，减少过早拆表

create extension if not exists "pgcrypto";

create table if not exists music_provider (
    id uuid primary key default gen_random_uuid(),
    provider_key varchar(64) not null unique,
    provider_type varchar(16) not null check (provider_type in ('chart','metadata','pt')),
    name varchar(128) not null,
    enabled boolean not null default true,
    priority int not null default 100,
    config_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists music_artist (
    id uuid primary key default gen_random_uuid(),
    canonical_key varchar(128) not null unique,
    mbid varchar(64),
    platform_source varchar(64),
    platform_id varchar(128),
    name varchar(256) not null,
    aliases jsonb not null default '[]'::jsonb,
    country varchar(32),
    active_years varchar(64),
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_music_artist_name on music_artist(name);
create index if not exists idx_music_artist_platform on music_artist(platform_source, platform_id);

create table if not exists music_album (
    id uuid primary key default gen_random_uuid(),
    canonical_key varchar(128) not null unique,
    upc varchar(64),
    mbid varchar(64),
    platform_source varchar(64),
    platform_id varchar(128),
    title varchar(256) not null,
    aliases jsonb not null default '[]'::jsonb,
    year int,
    release_date date,
    release_type varchar(16) not null default 'album'
        check (release_type in ('single','ep','album','compilation','live','remaster','deluxe')),
    audio_profile_pref jsonb not null default '[]'::jsonb,
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_music_album_title on music_album(title);
create index if not exists idx_music_album_year on music_album(year);
create index if not exists idx_music_album_platform on music_album(platform_source, platform_id);

create table if not exists music_track (
    id uuid primary key default gen_random_uuid(),
    canonical_key varchar(128) not null unique,
    isrc varchar(64),
    mbid varchar(64),
    platform_source varchar(64),
    platform_id varchar(128),
    title varchar(256) not null,
    aliases jsonb not null default '[]'::jsonb,
    album_id uuid references music_album(id) on delete set null,
    track_no int,
    disc_no int,
    version varchar(64),
    duration_seconds int,
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_music_track_title on music_track(title);
create index if not exists idx_music_track_album on music_track(album_id);
create index if not exists idx_music_track_platform on music_track(platform_source, platform_id);

create table if not exists music_artist_album (
    artist_id uuid not null references music_artist(id) on delete cascade,
    album_id uuid not null references music_album(id) on delete cascade,
    role varchar(32) not null default 'primary',
    primary key (artist_id, album_id)
);

create table if not exists music_artist_track (
    artist_id uuid not null references music_artist(id) on delete cascade,
    track_id uuid not null references music_track(id) on delete cascade,
    role varchar(32) not null default 'primary',
    primary key (artist_id, track_id)
);

create table if not exists music_chart (
    id uuid primary key default gen_random_uuid(),
    provider_id uuid not null references music_provider(id) on delete restrict,
    chart_key varchar(128) not null,
    name varchar(256) not null,
    chart_type varchar(16) not null check (chart_type in ('track','album','artist')),
    region varchar(64),
    category varchar(64),
    refresh_cron varchar(64),
    enabled boolean not null default true,
    unique (provider_id, chart_key)
);

create table if not exists music_chart_snapshot (
    id uuid primary key default gen_random_uuid(),
    chart_id uuid not null references music_chart(id) on delete cascade,
    snapshot_at timestamptz not null,
    items_json jsonb not null,
    created_at timestamptz not null default now(),
    unique (chart_id, snapshot_at)
);

create index if not exists idx_music_chart_snapshot_chart_time on music_chart_snapshot(chart_id, snapshot_at desc);

create table if not exists music_rule_profile (
    id uuid primary key default gen_random_uuid(),
    profile_key varchar(64) not null unique,
    name varchar(128) not null,
    allow_live boolean not null default false,
    allow_remaster boolean not null default true,
    audio_profiles jsonb not null default '["flac"]'::jsonb,
    auto_download_threshold numeric(5,2) not null default 90.00,
    manual_confirm_threshold numeric(5,2) not null default 70.00,
    rule_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists music_subscription (
    id uuid primary key default gen_random_uuid(),
    target_type varchar(16) not null check (target_type in ('chart','artist','album','track')),
    target_id uuid not null,
    profile_id uuid not null references music_rule_profile(id) on delete restrict,
    status varchar(16) not null default 'enabled'
        check (status in ('draft','enabled','paused','disabled')),
    trigger_mode varchar(16) not null default 'scheduled'
        check (trigger_mode in ('manual','scheduled','event')),
    cooldown_seconds int not null default 0,
    rule_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_music_subscription_target on music_subscription(target_type, target_id);
create index if not exists idx_music_subscription_status on music_subscription(status);

create table if not exists music_subscription_hit (
    id uuid primary key default gen_random_uuid(),
    subscription_id uuid not null references music_subscription(id) on delete cascade,
    hit_key varchar(128) not null,
    target_type varchar(16) not null check (target_type in ('artist','album','track')),
    target_id uuid,
    source_type varchar(32) not null check (source_type in ('chart','artist_watch','manual')),
    payload_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (subscription_id, hit_key)
);

create table if not exists music_search_job (
    id uuid primary key default gen_random_uuid(),
    target_type varchar(16) not null check (target_type in ('chart','artist','album','track')),
    target_id uuid not null,
    trigger_source varchar(32) not null
        check (trigger_source in ('manual','chart','subscription','artist_watch')),
    profile_id uuid not null references music_rule_profile(id) on delete restrict,
    status varchar(32) not null default 'queued'
        check (status in ('queued','running','matched','manual_pending','dispatched','completed','no_result','failed')),
    query_payload jsonb not null default '{}'::jsonb,
    started_at timestamptz,
    finished_at timestamptz,
    error_message text,
    created_at timestamptz not null default now()
);

create index if not exists idx_music_search_job_status on music_search_job(status);
create index if not exists idx_music_search_job_target on music_search_job(target_type, target_id);

create table if not exists music_search_result (
    id uuid primary key default gen_random_uuid(),
    job_id uuid not null references music_search_job(id) on delete cascade,
    site_id varchar(64) not null,
    site_resource_id varchar(128),
    raw_title text not null,
    normalized_title text,
    size_bytes bigint,
    seeders int,
    leechers int,
    publish_at timestamptz,
    free_status varchar(16),
    audio_profile varchar(16)
        check (audio_profile in ('mp3','aac','flac','ape','wav','hires')),
    score_total numeric(6,2) not null default 0,
    score_breakdown jsonb not null default '{}'::jsonb,
    decision varchar(16) not null default 'pending'
        check (decision in ('auto_download','manual_confirm','reject','pending')),
    reason_codes jsonb not null default '[]'::jsonb,
    raw_payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_music_search_result_job on music_search_result(job_id);
create index if not exists idx_music_search_result_decision on music_search_result(decision);
create index if not exists idx_music_search_result_score on music_search_result(score_total desc);

create table if not exists music_match_record (
    id uuid primary key default gen_random_uuid(),
    subscription_id uuid references music_subscription(id) on delete set null,
    job_id uuid not null references music_search_job(id) on delete cascade,
    result_id uuid not null references music_search_result(id) on delete cascade,
    decision varchar(16) not null
        check (decision in ('auto_download','manual_confirm','reject')),
    reason text,
    match_score numeric(6,2) not null,
    created_at timestamptz not null default now()
);

create table if not exists music_download_binding (
    id uuid primary key default gen_random_uuid(),
    result_id uuid not null references music_search_result(id) on delete cascade,
    downloader_id varchar(64) not null,
    downloader_task_id varchar(128),
    save_path text,
    status varchar(16) not null default 'submitted'
        check (status in ('submitted','downloading','completed','failed','cancelled')),
    dispatched_at timestamptz not null default now(),
    completed_at timestamptz
);

create index if not exists idx_music_download_binding_result on music_download_binding(result_id);
create index if not exists idx_music_download_binding_status on music_download_binding(status);

create table if not exists music_library_item (
    id uuid primary key default gen_random_uuid(),
    target_type varchar(16) not null check (target_type in ('artist','album','track')),
    target_id uuid,
    source_binding_id uuid references music_download_binding(id) on delete set null,
    source_path text not null,
    target_path text,
    tags_state varchar(16) not null default 'pending'
        check (tags_state in ('pending','written','failed')),
    library_state varchar(16) not null default 'pending'
        check (library_state in ('pending','moved','refreshed','failed')),
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists music_organize_job (
    id uuid primary key default gen_random_uuid(),
    library_item_id uuid not null references music_library_item(id) on delete cascade,
    rule_version varchar(32) not null,
    status varchar(16) not null default 'queued'
        check (status in ('queued','running','completed','failed','ignored')),
    log_json jsonb not null default '[]'::jsonb,
    started_at timestamptz,
    finished_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists idx_music_organize_job_status on music_organize_job(status);

-- 建议的初始 profile
insert into music_rule_profile (profile_key, name, allow_live, allow_remaster, audio_profiles, auto_download_threshold, manual_confirm_threshold)
values ('default-lossless', '默认无损', false, true, '["flac","ape","wav"]'::jsonb, 90.00, 70.00)
on conflict (profile_key) do nothing;
