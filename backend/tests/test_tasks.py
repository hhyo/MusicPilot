"""
Tasks 测试
"""


class TestTasks:
    """Tasks 测试"""

    def test_tasks_imports(self):
        """测试 tasks 模块可导入"""
        from app import tasks

        assert tasks is not None

    def test_download_monitor_module_imports(self):
        """测试 download_monitor 模块可导入"""
        from app.tasks import download_monitor

        assert download_monitor is not None

    def test_subscribe_check_module_imports(self):
        """测试 subscribe_check 模块可导入"""
        from app.tasks import subscribe_check

        assert subscribe_check is not None
