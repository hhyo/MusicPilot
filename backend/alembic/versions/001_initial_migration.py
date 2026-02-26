"""初始迁移

创建所有数据库表

Revision ID: 001
Revises:
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 artists 表
    op.create_table(
        'artists',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('musicbrainz_id', sa.String(length=100), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('name_pinyin', sa.String(length=255), nullable=True),
        sa.Column('sort_name', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('gender', sa.String(length=50), nullable=True),
        sa.Column('birth_date', sa.String(length=50), nullable=True),
        sa.Column('founded_date', sa.String(length=50), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('biography', sa.Text(), nullable=True),
        sa.Column('genres', postgresql.JSON(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artists_id'), 'artists', ['id'], unique=False)
    op.create_index(op.f('ix_artists_musicbrainz_id'), 'artists', ['musicbrainz_id'], unique=False)
    op.create_index(op.f('ix_artists_name'), 'artists', ['name'], unique=False)

    # 创建 albums 表
    op.create_table(
        'albums',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('musicbrainz_id', sa.String(length=100), nullable=True),
        sa.Column('artist_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('title_pinyin', sa.String(length=255), nullable=True),
        sa.Column('disambiguation', sa.String(length=255), nullable=True),
        sa.Column('release_date', sa.String(length=50), nullable=True),
        sa.Column('release_type', sa.String(length=50), nullable=True),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('catalog_number', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('cover_url', sa.String(length=500), nullable=True),
        sa.Column('cover_id', sa.String(length=100), nullable=True),
        sa.Column('genres', postgresql.JSON(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=True),
        sa.Column('track_count', sa.Integer(), nullable=True),
        sa.Column('total_duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['artist_id'], ['artists.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_albums_id'), 'albums', ['id'], unique=False)
    op.create_index(op.f('ix_albums_musicbrainz_id'), 'albums', ['musicbrainz_id'], unique=False)
    op.create_index(op.f('ix_albums_title'), 'albums', ['title'], unique=False)
    op.create_index(op.f('ix_albums_artist_id'), 'albums', ['artist_id'], unique=False)

    # 创建 tracks 表
    op.create_table(
        'tracks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('musicbrainz_id', sa.String(length=100), nullable=True),
        sa.Column('album_id', sa.Integer(), nullable=True),
        sa.Column('artist_id', sa.Integer(), nullable=True),
        sa.Column('featured_artist_ids', postgresql.JSON(), nullable=True),
        sa.Column('disc_number', sa.Integer(), nullable=True),
        sa.Column('track_number', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('title_pinyin', sa.String(length=255), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('path', sa.String(length=1000), nullable=True),
        sa.Column('file_format', sa.String(length=10), nullable=True),
        sa.Column('bitrate', sa.Integer(), nullable=True),
        sa.Column('sample_rate', sa.Integer(), nullable=True),
        sa.Column('channels', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('lyrics', sa.Text(), nullable=True),
        sa.Column('genres', postgresql.JSON(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('play_count', sa.Integer(), nullable=True),
        sa.Column('last_played', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ),
        sa.ForeignKeyConstraint(['artist_id'], ['artists.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tracks_id'), 'tracks', ['id'], unique=False)
    op.create_index(op.f('ix_tracks_musicbrainz_id'), 'tracks', ['musicbrainz_id'], unique=False)
    op.create_index(op.f('ix_tracks_title'), 'tracks', ['title'], unique=False)
    op.create_index(op.f('ix_tracks_path'), 'tracks', ['path'], unique=False)
    op.create_index(op.f('ix_tracks_album_id'), 'tracks', ['album_id'], unique=False)
    op.create_index(op.f('ix_tracks_artist_id'), 'tracks', ['artist_id'], unique=False)

    # 创建 playlists 表
    op.create_table(
        'playlists',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_url', sa.String(length=500), nullable=True),
        sa.Column('smart_query', postgresql.JSON(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_playlists_id'), 'playlists', ['id'], unique=False)

    # 创建 playlist_tracks 表
    op.create_table(
        'playlist_tracks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('playlist_id', sa.Integer(), nullable=False),
        sa.Column('track_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['playlist_id'], ['playlists.id'], ),
        sa.ForeignKeyConstraint(['track_id'], ['tracks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_playlist_tracks_id'), 'playlist_tracks', ['id'], unique=False)
    op.create_index(op.f('ix_playlist_tracks_playlist_id'), 'playlist_tracks', ['playlist_id'], unique=False)
    op.create_index(op.f('ix_playlist_tracks_track_id'), 'playlist_tracks', ['track_id'], unique=False)

    # 创建 libraries 表
    op.create_table(
        'libraries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=1000), nullable=False),
        sa.Column('scan_interval', sa.Integer(), nullable=True),
        sa.Column('last_scan_time', sa.String(length=50), nullable=True),
        sa.Column('auto_scan', sa.Boolean(), nullable=False),
        sa.Column('scan_recursive', sa.Boolean(), nullable=False),
        sa.Column('track_count', sa.Integer(), nullable=True),
        sa.Column('album_count', sa.Integer(), nullable=True),
        sa.Column('artist_count', sa.Integer(), nullable=True),
        sa.Column('total_size', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_libraries_id'), 'libraries', ['id'], unique=False)

    # 创建 download_history 表
    op.create_table(
        'download_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('artist', sa.String(length=255), nullable=True),
        sa.Column('album', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=True),
        sa.Column('quality', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=1000), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_format', sa.String(length=10), nullable=True),
        sa.Column('completed_at', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_download_history_id'), 'download_history', ['id'], unique=False)

    # 创建 subscribes 表
    op.create_table(
        'subscribes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('musicbrainz_id', sa.String(length=100), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('auto_download', sa.Boolean(), nullable=False),
        sa.Column('download_format', sa.String(length=50), nullable=True),
        sa.Column('last_check', sa.String(length=50), nullable=True),
        sa.Column('last_release', sa.String(length=50), nullable=True),
        sa.Column('release_count', sa.Integer(), nullable=True),
        sa.Column('state', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscribes_id'), 'subscribes', ['id'], unique=False)
    op.create_index(op.f('ix_subscribes_musicbrainz_id'), 'subscribes', ['musicbrainz_id'], unique=False)

    # 创建 media_servers 表
    op.create_table(
        'media_servers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('token', sa.String(length=255), nullable=True),
        sa.Column('library_id', sa.String(length=100), nullable=True),
        sa.Column('library_name', sa.String(length=255), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_media_servers_id'), 'media_servers', ['id'], unique=False)

    # 创建 system_config 表
    op.create_table(
        'system_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_config_id'), 'system_config', ['id'], unique=False)
    op.create_index(op.f('ix_system_config_key'), 'system_config', ['key'], unique=True)


def downgrade() -> None:
    op.drop_table('system_config')
    op.drop_table('media_servers')
    op.drop_table('subscribes')
    op.drop_table('download_history')
    op.drop_table('libraries')
    op.drop_table('playlist_tracks')
    op.drop_table('playlists')
    op.drop_table('tracks')
    op.drop_table('albums')
    op.drop_table('artists')