"""
模块导入测试
"""

import pytest


class TestModuleImports:
    """模块导入测试"""

    def test_import_chain_metadata(self):
        """测试导入 metadata chain"""
        from app.chain import metadata
        assert metadata is not None

    def test_import_chain_download(self):
        """测试导入 download chain"""
        from app.chain import download
        assert download is not None

    def test_import_chain_downloader(self):
        """测试导入 downloader chain"""
        from app.chain import downloader
        assert downloader is not None

    def test_import_chain_musicbrainz(self):
        """测试导入 musicbrainz chain"""
        from app.chain import musicbrainz
        assert musicbrainz is not None

    def test_import_chain_subscribe(self):
        """测试导入 subscribe chain"""
        from app.chain import subscribe
        assert subscribe is not None

    def test_import_chain_torrents(self):
        """测试导入 torrents chain"""
        from app.chain import torrents
        assert torrents is not None

    def test_import_chain_transfer(self):
        """测试导入 transfer chain"""
        from app.chain import transfer
        assert transfer is not None

    def test_import_chain_playback(self):
        """测试导入 playback chain"""
        from app.chain import playback
        assert playback is not None

    def test_import_chain_playlist(self):
        """测试导入 playlist chain"""
        from app.chain import playlist
        assert playlist is not None

    def test_import_chain_media(self):
        """测试导入 media chain"""
        from app.chain import media
        assert media is not None


class TestCoreImports:
    """核心模块导入测试"""

    def test_import_core_config(self):
        """测试导入 config"""
        from app.core import config
        assert config is not None

    def test_import_core_event(self):
        """测试导入 event"""
        from app.core import event
        assert event is not None

    def test_import_core_log(self):
        """测试导入 log"""
        from app.core import log
        assert log is not None

    def test_import_core_cache(self):
        """测试导入 cache"""
        from app.core import cache
        assert cache is not None

    def test_import_core_context(self):
        """测试导入 context"""
        from app.core import context
        assert context is not None


class TestDbImports:
    """数据库模块导入测试"""

    def test_import_db_manager(self):
        """测试导入 db_manager"""
        from app.db import db_manager
        assert db_manager is not None

    def test_import_db_models(self):
        """测试导入 models"""
        from app.db import models
        assert models is not None
