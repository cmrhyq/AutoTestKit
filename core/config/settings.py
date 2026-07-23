"""
全局配置模块

该模块定义了测试框架的所有配置项，支持从环境变量加载配置。
配置项包括浏览器设置、API设置、日志设置、并行执行设置等。
"""

import os
from typing import Optional, Literal
from pathlib import Path

from core.config.env_config import env_manager
from core.config.system_config import system_manager


class Settings:
    """
    测试框架全局配置类
    
    所有配置项都可以通过环境变量覆盖，环境变量名称为配置项名称的大写形式。
    例如：browser_type 系统变量会覆盖 browser_type 配置。
    """
    env = env_manager.get_config()
    system = system_manager.get_config()

    # ==================== 测试环境配置 ====================
    # 测试环境：dev, test, staging, prod
    TEST_ENV: str = system.get("test_env", "test")
    # 项目根目录
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    # 项目配置目录
    PROJECT_CONFIG_DIR: Path = Path(__file__).parent.parent.parent / "config"
    
    # ==================== 浏览器配置 ====================
    # 浏览器类型：chromium, firefox, webkit
    BROWSER_TYPE: Literal["chromium", "firefox", "webkit"] = system.get("browser_type", "chromium")
    # 是否使用无头模式运行浏览器
    HEADLESS: bool = system.get("headless", "false") == "true"
    # 浏览器操作超时时间（毫秒）
    BROWSER_TIMEOUT: int = int(system.get("browser_timeout", 30000))
    # 页面加载超时时间（毫秒）
    PAGE_LOAD_TIMEOUT: int = int(system.get("page_load_timeout", 30000))
    # 浏览器启动参数
    BROWSER_ARGS: list = system.get("browser_args", "").split(",") if system.get("browser_args") else []
    # 视口大小
    VIEWPORT_WIDTH: int = int(system.get("viewport_width", 1920))
    VIEWPORT_HEIGHT: int = int(system.get("viewport_height", 1080))
    # 是否启用浏览器开发者工具
    DEVTOOLS: bool = system.get("devtools", "false") == "true"

    # ==================== API 配置 ====================
    API_BASE_URL: str = env.get("apiBaseUrl", "http://localhost:8000")
    # API 请求超时时间（秒）
    API_TIMEOUT: int = int(system.get("api_timeout", 30))
    # API 连接超时时间（秒）
    API_CONNECT_TIMEOUT: int = int(system.get("api_connect_timeout", 10))
    # API 读取超时时间（秒）
    API_READ_TIMEOUT: int = int(system.get("api_read_timeout", 30))
    # 是否验证 SSL 证书
    VERIFY_SSL: bool = system.get("api_verify_ssl", "true") == "true"

    # ==================== 日志配置 ====================
    # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = system.get(
        "log_level", "INFO"
    )
    # 日志目录
    LOG_DIR: str = system.get("log_dir", "logs")
    # 日志文件名格式
    LOG_FILE_FORMAT: str = system.get("log_file_format", "test_{timestamp}.log")
    # 是否在控制台输出日志
    LOG_TO_CONSOLE: bool = system.get("log_to_console", "true") == "true"
    # 是否输出日志到文件
    LOG_TO_FILE: bool = system.get("log_to_file", "true") == "true"
    # 日志格式
    LOG_FORMAT: str = system.get(
        "log_format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # 日志时间格式
    LOG_DATE_FORMAT: str = system.get("log_date_format", "%Y-%m-%d %H:%M:%S")
    
    # 单个日志文件最大大小（字节），默认 10MB
    # 环境变量：LOG_MAX_BYTES
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    
    # 日志备份文件数量，默认保留 5 个
    # 环境变量：LOG_BACKUP_COUNT
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # ==================== 并行执行配置 ====================
    # 并行 worker 数量：auto 表示自动检测 CPU 核心数，或指定具体数字
    PARALLEL_WORKERS: str = system.get("parallel_workers", "auto")
    # 是否启用并行执行
    ENABLE_PARALLEL: bool = system.get("enable_parallel", "true") == "true"
    # 并行执行分发策略：loadscope, loadfile, loadgroup, load
    PARALLEL_DIST_MODE: Literal["loadscope", "loadfile", "loadgroup", "load"] = system.get(
        "parallel_dist_mode", "loadscope"
    )
    
    # ==================== Allure 报告配置 ====================
    # Allure 结果目录
    ALLURE_RESULTS_DIR: str = system.get("allure_results_dir", "report/allure-results")
    # Allure 报告目录
    ALLURE_REPORT_DIR: str = system.get("allure_report_dir", "report/allure-report")
    # 是否清理旧的 Allure 结果
    ALLURE_CLEAN_RESULTS: bool = system.get("allure_clean_results", "true") == "true"
    
    # ==================== 截图配置 ====================
    # 截图保存目录
    SCREENSHOT_DIR: str = system.get("screenshot_dir", "screenshots")
    # 是否在失败时自动截图
    SCREENSHOT_ON_FAILURE: bool = system.get("screenshot_on_failure", "true") == "true"
    # 截图格式：png, jpeg
    SCREENSHOT_FORMAT: Literal["png", "jpeg"] = system.get("screenshot_format", "png")
    # 截图质量（仅对 jpeg 有效，1-100）
    SCREENSHOT_QUALITY: int = int(system.get("screenshot_quality", 80))
    
    # ==================== 配置验证方法 ====================
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        验证配置的有效性
        
        Returns:
            tuple[bool, list[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        # 验证浏览器类型
        if cls.BROWSER_TYPE not in ["chromium", "firefox", "webkit"]:
            errors.append(f"Invalid BROWSER_TYPE: {cls.BROWSER_TYPE}. Must be one of: chromium, firefox, webkit")
        
        # 验证超时时间
        if cls.BROWSER_TIMEOUT <= 0:
            errors.append(f"BROWSER_TIMEOUT must be positive, got: {cls.BROWSER_TIMEOUT}")
        
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL not in valid_log_levels:
            errors.append(f"Invalid LOG_LEVEL: {cls.LOG_LEVEL}. Must be one of: {', '.join(valid_log_levels)}")
        
        # 验证并行 worker 配置
        if cls.PARALLEL_WORKERS != "auto":
            try:
                workers = int(cls.PARALLEL_WORKERS)
                if workers <= 0:
                    errors.append(f"PARALLEL_WORKERS must be 'auto' or a positive integer, got: {cls.PARALLEL_WORKERS}")
            except ValueError:
                errors.append(f"PARALLEL_WORKERS must be 'auto' or a valid integer, got: {cls.PARALLEL_WORKERS}")
        
        # 验证截图质量
        if not (1 <= cls.SCREENSHOT_QUALITY <= 100):
            errors.append(f"SCREENSHOT_QUALITY must be between 1 and 100, got: {cls.SCREENSHOT_QUALITY}")
        
        # 验证视口大小
        if cls.VIEWPORT_WIDTH <= 0 or cls.VIEWPORT_HEIGHT <= 0:
            errors.append(f"Viewport dimensions must be positive, got: {cls.VIEWPORT_WIDTH}x{cls.VIEWPORT_HEIGHT}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """
        获取配置摘要（用于日志记录和调试）
        
        Returns:
            dict: 配置摘要字典（敏感信息已脱敏）
        """
        return {
            "browser": {
                "type": cls.BROWSER_TYPE,
                "headless": cls.HEADLESS,
                "timeout": cls.BROWSER_TIMEOUT,
                "viewport": f"{cls.VIEWPORT_WIDTH}x{cls.VIEWPORT_HEIGHT}",
            },
            "logging": {
                "level": cls.LOG_LEVEL,
                "directory": cls.LOG_DIR,
                "console": cls.LOG_TO_CONSOLE,
                "file": cls.LOG_TO_FILE,
            },
            "parallel": {
                "enabled": cls.ENABLE_PARALLEL,
                "workers": cls.PARALLEL_WORKERS,
                "dist_mode": cls.PARALLEL_DIST_MODE,
            },
            "allure": {
                "results_dir": cls.ALLURE_RESULTS_DIR,
                "report_dir": cls.ALLURE_REPORT_DIR,
            },
            "environment": cls.TEST_ENV,
        }
    
    @classmethod
    def create_directories(cls) -> None:
        """
        创建必要的目录结构
        """
        directories = [
            cls.LOG_DIR,
            cls.ALLURE_RESULTS_DIR,
            cls.ALLURE_REPORT_DIR,
            cls.SCREENSHOT_DIR,
            cls.PROJECT_CONFIG_DIR,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


# 创建全局配置实例
settings = Settings()

# 在模块加载时验证配置
is_valid, validation_errors = settings.validate()
if not is_valid:
    import warnings
    for error in validation_errors:
        warnings.warn(f"Configuration validation error: {error}")
