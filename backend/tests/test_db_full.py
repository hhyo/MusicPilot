"""
数据库层完整测试
"""


class TestDatabaseManagerFull:
    """DatabaseManager 完整测试"""

    def test_database_manager_imports(self):
        from app.db import DatabaseManager

        assert DatabaseManager is not None

    def test_oper_base_imports(self):
        from app.db import OperBase

        assert OperBase is not None

    def test_base_imports(self):
        from app.db import Base

        assert Base is not None


class TestDbInitFull:
    """Db Init 完整测试"""

    def test_db_module_imports(self):
        from app import db

        assert db is not None

    def test_get_db_function(self):
        from app.db import get_db

        assert get_db is not None


class TestOperationsInitFull:
    """Operations Init 完整测试"""

    def test_operations_module_imports(self):
        from app.db import operations

        assert operations is not None


class TestModelsInitFull:
    """Models Init 完整测试"""

    def test_models_module_imports(self):
        from app.db import models

        assert models is not None


class TestTimestampMixin:
    """TimestampMixin 测试"""

    def test_timestamp_mixin_imports(self):
        from app.db import TimestampMixin

        assert TimestampMixin is not None
