"""
日志管理器模块

该模块提供统一的日志记录接口，支持多级别日志记录、双输出（控制台和文件）、
日志格式化、日志轮转、彩色终端输出以及 Allure 报告集成。
"""

import logging
import logging.handlers
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import allure
    HAS_ALLURE = True
except ImportError:
    HAS_ALLURE = False

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

from core.config import Settings


class TestLogger:
    """
    测试日志记录器类
    
    提供统一的日志记录接口，支持：
    - 多级别日志记录（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    - 同时输出到控制台和文件
    - 彩色终端输出（需安装 colorlog，自动降级）
    - 统一的日志格式（包含时间戳、级别和消息）
    - 日志轮转（按大小和数量限制）
    - Allure 报告集成
    - 线程安全的文件写入
    
    使用示例：
        # 获取日志记录器
        logger = TestLogger.get_logger("MyModule")
        logger.info("This is an info message")
        logger.error("This is an error message")
        
        # 手动初始化（通常自动完成）
        TestLogger.setup_logger("DEBUG")
        
        # 重置日志系统（测试用）
        TestLogger.reset()
    """
    
    _loggers = {}
    _log_file_path: Optional[str] = None
    _session_start_time: Optional[str] = None
    _setup_lock = threading.Lock()  # 保护日志系统初始化
    _file_lock = threading.Lock()  # 保护文件操作
    
    # 日志轮转配置
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 单个日志文件最大 10MB
    LOG_BACKUP_COUNT = 5  # 保留最近 5 个备份文件
    
    # 彩色日志配置
    COLOR_LOG_COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
    
    @classmethod
    def setup_logger(cls, log_level: str = None) -> None:
        """
        设置日志系统的全局配置（线程安全）
        
        支持彩色终端输出（安装 colorlog 后自动启用）和日志文件轮转。
        
        Args:
            log_level: 日志级别，如果为 None 则使用配置文件中的设置
            
        使用示例：
            TestLogger.setup_logger("DEBUG")
            TestLogger.setup_logger()  # 使用配置文件中的级别
        """
        with cls._setup_lock:
            if log_level is None:
                log_level = Settings.LOG_LEVEL
            
            # 创建日志目录
            log_dir = Path(Settings.LOG_DIR)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成日志文件名（使用会话开始时间）
            if cls._session_start_time is None:
                cls._session_start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            log_filename = Settings.LOG_FILE_FORMAT.replace("{timestamp}", cls._session_start_time)
            cls._log_file_path = str(log_dir / log_filename)
            
            # 设置根日志记录器
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, log_level))
            
            # 清除现有的处理器
            root_logger.handlers.clear()
            
            # 创建文件格式化器（不带颜色）
            file_formatter = logging.Formatter(
                fmt=Settings.LOG_FORMAT,
                datefmt=Settings.LOG_DATE_FORMAT
            )
            
            # 添加控制台处理器（支持彩色输出）
            if Settings.LOG_TO_CONSOLE:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(getattr(logging, log_level))
                
                if HAS_COLORLOG:
                    color_formatter = colorlog.ColoredFormatter(
                        fmt="%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        datefmt=Settings.LOG_DATE_FORMAT,
                        log_colors=cls.COLOR_LOG_COLORS
                    )
                    console_handler.setFormatter(color_formatter)
                else:
                    console_handler.setFormatter(file_formatter)
                
                root_logger.addHandler(console_handler)
            
            # 添加文件处理器（使用 RotatingFileHandler 实现日志轮转）
            if Settings.LOG_TO_FILE:
                max_bytes = getattr(Settings, 'LOG_MAX_BYTES', cls.LOG_MAX_BYTES)
                backup_count = getattr(Settings, 'LOG_BACKUP_COUNT', cls.LOG_BACKUP_COUNT)
                
                file_handler = logging.handlers.RotatingFileHandler(
                    cls._log_file_path,
                    mode='a',
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, log_level))
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器（线程安全）
        
        Args:
            name: 日志记录器名称，通常使用模块名或类名
            
        Returns:
            logging.Logger: 配置好的日志记录器实例
            
        使用示例：
            logger = TestLogger.get_logger("LoginPage")
            logger.info("Login successful")
        """
        if cls._log_file_path is None:
            cls.setup_logger()
        
        with cls._setup_lock:
            if name not in cls._loggers:
                logger = logging.getLogger(name)
                cls._loggers[name] = logger
            
            return cls._loggers[name]
    
    @classmethod
    def attach_log_to_allure(cls, log_file_path: str = None) -> None:
        """
        将日志文件附加到 Allure 报告（线程安全）
        
        Args:
            log_file_path: 日志文件路径，如果为 None 则使用当前会话的日志文件
        """
        if log_file_path is None:
            log_file_path = cls._log_file_path
        
        if log_file_path and os.path.exists(log_file_path):
            if not HAS_ALLURE:
                return
            try:
                with cls._file_lock:
                    with open(log_file_path, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                
                allure.attach(
                    log_content,
                    name="Test Execution Log",
                    attachment_type=allure.attachment_type.TEXT
                )
            except Exception as e:
                logging.warning(f"Failed to attach log to Allure: {e}")
    
    @classmethod
    def get_log_file_path(cls) -> Optional[str]:
        """
        获取当前会话的日志文件路径
        
        Returns:
            Optional[str]: 日志文件路径，如果未初始化则返回 None
        """
        return cls._log_file_path
    
    @classmethod
    def reset(cls) -> None:
        """
        重置日志系统（主要用于测试，线程安全）
        """
        with cls._setup_lock:
            cls._loggers.clear()
            cls._log_file_path = None
            cls._session_start_time = None
            
            root_logger = logging.getLogger()
            root_logger.handlers.clear()


# 便捷函数：获取日志记录器
def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 配置好的日志记录器实例
    """
    return TestLogger.get_logger(name)
