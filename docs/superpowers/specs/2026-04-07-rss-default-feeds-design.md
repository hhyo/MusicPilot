# RSS Default Feeds Design

## Goal
Provide a built-in default RSS discovery feed set for fresh installs so RSS discovery is usable without requiring immediate manual settings entry.

## Scope
Add five default RSS feeds used only as the final fallback when neither persisted project settings nor environment configuration provides `chart_rss_feeds`.

Default feeds:
1. 网易云热歌榜
2. 网易云新歌榜
3. 网易云原创榜
4. YouTube 热门歌曲榜
5. YouTube 热门歌手榜

## Behavior
Resolution order for `chart_rss_feeds` becomes:
1. persisted project settings
2. environment-configured feeds
3. built-in default feed set

Persisted project settings must continue to win over defaults. Environment settings must continue to win when provided.

## Non-goals
- No new settings UI behavior
- No additional RSS families
- No automatic migration or persistence of defaults into `app_settings`
