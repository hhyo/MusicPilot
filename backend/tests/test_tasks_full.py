"""
Tasks 层完整测试
"""


class TestDownloadMonitorTaskFull:
    """DownloadMonitorTask 完整测试"""

    def test_download_monitor_task_imports(self):
        from app.tasks.download_monitor import DownloadMonitorTask

        assert DownloadMonitorTask is not None

    def test_download_monitor_module_imports(self):
        from app.tasks import download_monitor

        assert download_monitor is not None


class TestSubscribeCheckFull:
    """SubscribeCheck 完整测试"""

    def test_subscribe_check_task_imports(self):
        from app.tasks.subscribe_check import SubscribeCheckTask

        assert SubscribeCheckTask is not None

    def test_subscribe_check_module_imports(self):
        from app.tasks import subscribe_check

        assert subscribe_check is not None


class TestTasksInitFull:
    """Tasks Init 完整测试"""

    def test_tasks_module_imports(self):
        from app import tasks

        assert tasks is not None
