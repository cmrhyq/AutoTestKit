"""
文件操作工具模块

该模块提供文件和目录操作的实用工具函数，包括文件读写、路径管理、
文件查找等功能。
"""

import json
import shutil
from pathlib import Path
from typing import Optional, Union, List, Any
from datetime import datetime

from core.config import Settings


class FileHelper:
    """
    文件操作辅助类
    
    提供常用的文件和目录操作方法，包括：
    - 文件读写操作
    - 目录管理
    - 路径处理
    - 文件查找和过滤
    """
    
    @staticmethod
    def read_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码，默认为 utf-8
            
        Returns:
            str: 文件内容
            
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取文件失败
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}")
    
    @staticmethod
    def write_file(
        file_path: Union[str, Path],
        content: str,
        encoding: str = 'utf-8',
        create_dirs: bool = True
    ) -> None:
        """
        写入内容到文件
        
        Args:
            file_path: 文件路径
            content: 要写入的内容
            encoding: 文件编码，默认为 utf-8
            create_dirs: 是否自动创建父目录，默认为 True
            
        Raises:
            IOError: 写入文件失败
        """
        file_path = Path(file_path)
        
        # 创建父目录
        if create_dirs and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to write file {file_path}: {e}")
    
    @staticmethod
    def append_file(
        file_path: Union[str, Path],
        content: str,
        encoding: str = 'utf-8',
        create_dirs: bool = True
    ) -> None:
        """
        追加内容到文件末尾
        
        Args:
            file_path: 文件路径
            content: 要追加的内容
            encoding: 文件编码，默认为 utf-8
            create_dirs: 是否自动创建父目录，默认为 True
            
        Raises:
            IOError: 追加文件失败
        """
        file_path = Path(file_path)
        
        # 创建父目录
        if create_dirs and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to append to file {file_path}: {e}")
    
    @staticmethod
    def read_json(file_path: Union[str, Path]) -> Any:
        """
        读取 JSON 文件
        
        Args:
            file_path: JSON 文件路径
            
        Returns:
            Any: 解析后的 JSON 数据
            
        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON 解析失败
        """
        content = FileHelper.read_file(file_path)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Failed to parse JSON from {file_path}: {e.msg}",
                e.doc,
                e.pos
            )
    
    @staticmethod
    def write_json(
        file_path: Union[str, Path],
        data: Any,
        indent: int = 2,
        create_dirs: bool = True
    ) -> None:
        """
        写入数据到 JSON 文件
        
        Args:
            file_path: JSON 文件路径
            data: 要写入的数据
            indent: JSON 缩进空格数，默认为 2
            create_dirs: 是否自动创建父目录，默认为 True
            
        Raises:
            IOError: 写入文件失败
        """
        try:
            json_content = json.dumps(data, indent=indent, ensure_ascii=False)
            FileHelper.write_file(file_path, json_content, create_dirs=create_dirs)
        except Exception as e:
            raise IOError(f"Failed to write JSON to {file_path}: {e}")
    
    @staticmethod
    def file_exists(file_path: Union[str, Path]) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 文件存在返回 True，否则返回 False
        """
        return Path(file_path).is_file()
    
    @staticmethod
    def dir_exists(dir_path: Union[str, Path]) -> bool:
        """
        检查目录是否存在
        
        Args:
            dir_path: 目录路径
            
        Returns:
            bool: 目录存在返回 True，否则返回 False
        """
        return Path(dir_path).is_dir()
    
    @staticmethod
    def create_dir(dir_path: Union[str, Path], exist_ok: bool = True) -> None:
        """
        创建目录
        
        Args:
            dir_path: 目录路径
            exist_ok: 如果目录已存在是否报错，默认为 True（不报错）
            
        Raises:
            OSError: 创建目录失败
        """
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=exist_ok)
        except Exception as e:
            raise OSError(f"Failed to create directory {dir_path}: {e}")
    
    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> None:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Raises:
            FileNotFoundError: 文件不存在
            OSError: 删除文件失败
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            file_path.unlink()
        except Exception as e:
            raise OSError(f"Failed to delete file {file_path}: {e}")
    
    @staticmethod
    def delete_dir(dir_path: Union[str, Path], recursive: bool = False) -> None:
        """
        删除目录
        
        Args:
            dir_path: 目录路径
            recursive: 是否递归删除非空目录，默认为 False
            
        Raises:
            FileNotFoundError: 目录不存在
            OSError: 删除目录失败
        """
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        try:
            if recursive:
                shutil.rmtree(dir_path)
            else:
                dir_path.rmdir()
        except Exception as e:
            raise OSError(f"Failed to delete directory {dir_path}: {e}")
    
    @staticmethod
    def copy_file(
        src_path: Union[str, Path],
        dst_path: Union[str, Path],
        create_dirs: bool = True
    ) -> None:
        """
        复制文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            create_dirs: 是否自动创建目标目录，默认为 True
            
        Raises:
            FileNotFoundError: 源文件不存在
            IOError: 复制文件失败
        """
        src_path = Path(src_path)
        dst_path = Path(dst_path)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")
        
        # 创建目标目录
        if create_dirs and not dst_path.parent.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(src_path, dst_path)
        except Exception as e:
            raise IOError(f"Failed to copy file from {src_path} to {dst_path}: {e}")
    
    @staticmethod
    def move_file(
        src_path: Union[str, Path],
        dst_path: Union[str, Path],
        create_dirs: bool = True
    ) -> None:
        """
        移动文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            create_dirs: 是否自动创建目标目录，默认为 True
            
        Raises:
            FileNotFoundError: 源文件不存在
            IOError: 移动文件失败
        """
        src_path = Path(src_path)
        dst_path = Path(dst_path)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")
        
        # 创建目标目录
        if create_dirs and not dst_path.parent.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.move(str(src_path), str(dst_path))
        except Exception as e:
            raise IOError(f"Failed to move file from {src_path} to {dst_path}: {e}")
    
    @staticmethod
    def list_files(
        dir_path: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """
        列出目录中的文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件名模式（支持通配符），默认为 "*"（所有文件）
            recursive: 是否递归搜索子目录，默认为 False
            
        Returns:
            List[Path]: 匹配的文件路径列表
            
        Raises:
            FileNotFoundError: 目录不存在
        """
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if recursive:
            return [f for f in dir_path.rglob(pattern) if f.is_file()]
        else:
            return [f for f in dir_path.glob(pattern) if f.is_file()]
    
    @staticmethod
    def list_dirs(
        dir_path: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """
        列出目录中的子目录
        
        Args:
            dir_path: 目录路径
            pattern: 目录名模式（支持通配符），默认为 "*"（所有目录）
            recursive: 是否递归搜索子目录，默认为 False
            
        Returns:
            List[Path]: 匹配的目录路径列表
            
        Raises:
            FileNotFoundError: 目录不存在
        """
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if recursive:
            return [d for d in dir_path.rglob(pattern) if d.is_dir()]
        else:
            return [d for d in dir_path.glob(pattern) if d.is_dir()]
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """
        获取文件大小（字节）
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 文件大小（字节）
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return file_path.stat().st_size
    
    @staticmethod
    def get_file_modified_time(file_path: Union[str, Path]) -> datetime:
        """
        获取文件最后修改时间
        
        Args:
            file_path: 文件路径
            
        Returns:
            datetime: 文件最后修改时间
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        timestamp = file_path.stat().st_mtime
        return datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def get_absolute_path(file_path: Union[str, Path]) -> Path:
        """
        获取文件的绝对路径
        
        Args:
            file_path: 文件路径（可以是相对路径或绝对路径）
            
        Returns:
            Path: 文件的绝对路径
        """
        return Path(file_path).resolve()
    
    @staticmethod
    def get_relative_path(
        file_path: Union[str, Path],
        base_path: Union[str, Path] = None
    ) -> Path:
        """
        获取文件相对于基准路径的相对路径
        
        Args:
            file_path: 文件路径
            base_path: 基准路径，默认为项目根目录
            
        Returns:
            Path: 相对路径
        """
        file_path = Path(file_path).resolve()
        
        if base_path is None:
            base_path = Settings.PROJECT_ROOT
        else:
            base_path = Path(base_path).resolve()
        
        try:
            return file_path.relative_to(base_path)
        except ValueError:
            # 如果无法计算相对路径，返回绝对路径
            return file_path
    
    @staticmethod
    def join_path(*paths: Union[str, Path]) -> Path:
        """
        连接多个路径部分
        
        Args:
            *paths: 要连接的路径部分
            
        Returns:
            Path: 连接后的路径
        """
        if not paths:
            return Path()
        
        result = Path(paths[0])
        for path in paths[1:]:
            result = result / path
        
        return result
    
    @staticmethod
    def get_project_path(*paths: Union[str, Path]) -> Path:
        """
        获取项目根目录下的路径
        
        Args:
            *paths: 相对于项目根目录的路径部分
            
        Returns:
            Path: 完整路径
        """
        return FileHelper.join_path(Settings.PROJECT_ROOT, *paths)
    
    @staticmethod
    def get_test_data_path(*paths: Union[str, Path]) -> Path:
        """
        获取测试数据目录下的路径
        
        Args:
            *paths: 相对于测试数据目录的路径部分
            
        Returns:
            Path: 完整路径
        """
        return FileHelper.join_path(Settings.PROJECT_CONFIG_DIR, *paths)
    
    @staticmethod
    def get_log_path(*paths: Union[str, Path]) -> Path:
        """
        获取日志目录下的路径
        
        Args:
            *paths: 相对于日志目录的路径部分
            
        Returns:
            Path: 完整路径
        """
        return FileHelper.join_path(Settings.LOG_DIR, *paths)
    
    @staticmethod
    def get_screenshot_path(*paths: Union[str, Path]) -> Path:
        """
        获取截图目录下的路径
        
        Args:
            *paths: 相对于截图目录的路径部分
            
        Returns:
            Path: 完整路径
        """
        return FileHelper.join_path(Settings.SCREENSHOT_DIR, *paths)
    
    @staticmethod
    def clean_directory(
        dir_path: Union[str, Path],
        pattern: str = "*",
        older_than_days: Optional[int] = None
    ) -> int:
        """
        清理目录中的文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件名模式（支持通配符），默认为 "*"（所有文件）
            older_than_days: 只删除超过指定天数的文件，None 表示删除所有匹配的文件
            
        Returns:
            int: 删除的文件数量
            
        Raises:
            FileNotFoundError: 目录不存在
        """
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        deleted_count = 0
        current_time = datetime.now()
        
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                # 检查文件年龄
                if older_than_days is not None:
                    file_time = FileHelper.get_file_modified_time(file_path)
                    age_days = (current_time - file_time).days
                    
                    if age_days < older_than_days:
                        continue
                
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception:
                    # 忽略删除失败的文件
                    pass
        
        return deleted_count


# 便捷函数
def read_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """读取文件内容的便捷函数"""
    return FileHelper.read_file(file_path, encoding)


def write_file(
    file_path: Union[str, Path],
    content: str,
    encoding: str = 'utf-8',
    create_dirs: bool = True
) -> None:
    """写入文件内容的便捷函数"""
    FileHelper.write_file(file_path, content, encoding, create_dirs)


def read_json(file_path: Union[str, Path]) -> Any:
    """读取 JSON 文件的便捷函数"""
    return FileHelper.read_json(file_path)


def write_json(
    file_path: Union[str, Path],
    data: Any,
    indent: int = 2,
    create_dirs: bool = True
) -> None:
    """写入 JSON 文件的便捷函数"""
    FileHelper.write_json(file_path, data, indent, create_dirs)

