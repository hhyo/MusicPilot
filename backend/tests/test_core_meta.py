"""
Core Meta 测试
"""

import pytest


class TestCoreMeta:
    """Core Meta 测试"""

    def test_metadata_parser_imports(self):
        """测试 MetadataParser 可导入"""
        from app.core.meta import MetadataParser
        assert MetadataParser is not None

    def test_filename_parser_imports(self):
        """测试 FilenameParser 可导入"""
        from app.core.meta import FilenameParser
        assert FilenameParser is not None


class TestMetaHelpers:
    """Meta 辅助方法测试"""

    def test_meta_module_imports(self):
        """测试 Meta 模块可导入"""
        from app.core import meta
        assert meta is not None
