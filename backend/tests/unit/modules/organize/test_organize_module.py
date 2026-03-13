"""Organize Module 测试"""
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
from app.modules.organize.organize_module import OrganizeModule
from app.modules.organize.models import OrganizeTask, OrganizeStatus


class TestOrganizeModule:
    """测试 OrganizeModule"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        module1 = OrganizeModule()
        module2 = OrganizeModule()
        
        assert module1 is module2
    
    def test_parse_template(self):
        """测试模板解析"""
        module = OrganizeModule()
        
        metadata = {
            "artist": "Test Artist",
            "album": "Test Album",
            "year": "2024",
            "track": "01",
            "title": "Test Song",
            "ext": "flac"
        }
        
        template = "{artist}/{album} [{year}]/{track}. {title}.{ext}"
        result = module._parse_template(template, metadata)
        
        assert result == "Test Artist/Test Album [2024]/01. Test Song.flac"
    
    def test_sanitize_filename(self):
        """测试文件名清理"""
        module = OrganizeModule()
        
        # 测试非法字符清理（文件名中的非法字符，不包括路径分隔符）
        # 每个非法字符替换为一个下划线
        assert module._sanitize_filename("Test:Song") == "Test_Song"
        assert module._sanitize_filename("Test*Song") == "Test_Song"
        assert module._sanitize_filename("Test|Song") == "Test_Song"
        assert module._sanitize_filename("Test?Song") == "Test_Song"
        assert module._sanitize_filename("Test<>Song") == "Test__Song"  # < 和 > 分别替换
        assert module._sanitize_filename("Test\"Song") == "Test_Song"
    
    def test_get_target_path(self):
        """测试获取目标路径"""
        module = OrganizeModule()
        module.library_path = "/media/music"
        
        metadata = {
            "artist": "Test Artist",
            "album": "Test Album",
            "year": "2024",
            "track": "01",
            "title": "Test Song",
            "ext": "flac"
        }
        
        source_path = "/downloads/test.flac"
        target_path = module._get_target_path(source_path, metadata)
        
        assert target_path == "/media/music/Test Artist/Test Album [2024]/01. Test Song.flac"
    
    @pytest.mark.asyncio
    async def test_organize_file(self):
        """测试整理文件"""
        module = OrganizeModule()
        
        # Mock 文件操作
        with patch('shutil.move') as mock_move, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=False):
            
            source_path = "/downloads/test.flac"
            metadata = {
                "artist": "Test Artist",
                "album": "Test Album",
                "year": "2024",
                "track": "01",
                "title": "Test Song",
                "ext": "flac"
            }
            
            result = await module.organize_file(source_path, metadata)
            
            assert result is True
            mock_makedirs.assert_called_once()
            mock_move.assert_called_once()


class TestOrganizeTask:
    """测试 OrganizeTask 模型"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = OrganizeTask(
            id=1,
            download_task_id=100,
            source_path="/downloads/test.flac",
            target_path="/media/music/test.flac",
            status=OrganizeStatus.PENDING,
            created_at=datetime.now()
        )
        
        assert task.id == 1
        assert task.download_task_id == 100
        assert task.status == OrganizeStatus.PENDING