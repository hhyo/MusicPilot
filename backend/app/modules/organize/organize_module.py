"""Organize Module - 文件整理和元数据管理"""

import os
import re
import shutil

from app.chain import ChainBase


class OrganizeModule(ChainBase):
    """整理模块 - 管理下载完成后的文件整理"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.library_path = "/media/music"  # 可配置
        self.template = "{artist}/{album} [{year}]/{track}. {title}.{ext}"

    def _parse_template(self, template: str, metadata: dict) -> str:
        """解析模板生成目标路径"""
        result = template
        for key, value in metadata.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符（保留路径分隔符）"""
        # Windows/Unix 文件名非法字符（不包括路径分隔符 / 和 \）
        illegal_chars = r'[<>:"\|?*]'
        return re.sub(illegal_chars, "_", filename)

    def _get_target_path(self, source_path: str, metadata: dict) -> str:
        """根据元数据生成目标路径"""
        # 解析模板
        relative_path = self._parse_template(self.template, metadata)

        # 清理路径
        relative_path = self._sanitize_filename(relative_path)

        # 组合完整路径
        target_path = os.path.join(self.library_path, relative_path)

        return target_path

    async def organize_file(self, source_path: str, metadata: dict) -> bool:
        """整理单个文件"""
        try:
            # 生成目标路径
            target_path = self._get_target_path(source_path, metadata)

            # 创建目标目录
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)

            # 移动文件
            shutil.move(source_path, target_path)

            return True

        except Exception as e:
            self.logger.error(f"整理文件失败: {e}")
            return False
