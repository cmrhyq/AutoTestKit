import multiprocessing
import os
import shutil
from pathlib import Path
from datetime import datetime

import pytest

from core.config import Settings
from core import TestLogger, DataCache

# 建议使用 threading.Lock 或 multiprocessing.Manager 来保护`
TEST_RESULTS = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}


# ==================== Pytest Hooks for Parallel Execution ====================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    收集每个用例的执行结果
    
    此 hook 同时完成两个功能：
    1. 统计测试结果（passed/failed/skipped/error）
    2. 将测试结果附加到测试项，以便 fixture 可以访问（用于 UI 测试失败截图等）
    """
    outcome = yield
    report = outcome.get_result()
    
    # 将测试结果附加到测试项，以便 fixture 可以访问
    # 这对于 UI 测试的失败截图功能是必需的
    setattr(item, f"rep_{report.when}", report)

    # 只统计用例执行阶段（call）的结果，跳过 setup/teardown
    if report.when == "call":
        if report.outcome == "passed":
            TEST_RESULTS["passed"] += 1
        elif report.outcome == "failed":
            TEST_RESULTS["failed"] += 1
        elif report.outcome == "skipped":
            TEST_RESULTS["skipped"] += 1
    # 捕获用例执行中的错误（如setup失败）
    elif report.when == "setup" and report.outcome == "failed":
        TEST_RESULTS["error"] += 1

def pytest_configure(config):
    """
    Pytest hook 在命令行选项解析完毕、所有插件和初始 conftest 文件加载完成后调用。

    此 hook 配置以下内容：
    - 用于并行执行的 CPU 核心检测
    - 创建目录结构
    - 配置验证
    - 清理 Trace/视频录制文件
    - Allure 的环境信息
    """
    logger = TestLogger.get_logger("PytestConfigure")
    
    # 清理 trace_videos 目录
    trace_dir = os.path.join(str(Settings.PROJECT_ROOT), "trace_videos")
    if os.path.exists(trace_dir):
        try:
            for filename in os.listdir(trace_dir):
                file_path = os.path.join(trace_dir, filename)
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            logger.info(f"Cleaned trace_videos directory")
        except Exception as e:
            logger.warning(f"Failed to clean trace_videos: {e}")
    
    # 创建必要的目录
    Settings.create_directories()
    logger.info("Created necessary directories")
    
    # 验证配置
    is_valid, errors = Settings.validate()
    if not is_valid:
        logger.warning("Configuration validation errors found:")
        for error in errors:
            logger.warning(f"  - {error}")
    
    # 记录配置摘要
    config_summary = Settings.get_config_summary()
    logger.info("Configuration Summary:")
    for category, values in config_summary.items():
        logger.info(f"  {category}: {values}")
    
    # 检测并记录 CPU 核心以进行并行执行
    cpu_count = multiprocessing.cpu_count()
    logger.info(f"Detected {cpu_count} CPU cores")
    
    # 检查是否正在使用 xdist
    if hasattr(config, 'workerinput'):
        worker_id = config.workerinput.get('workerid', 'unknown')
        logger.info(f"Running as xdist worker: {worker_id}")
    else:
        # 检查是否提供了 -n 选项
        numprocesses = config.getoption('numprocesses', default=None)
        if numprocesses:
            if numprocesses == 'auto':
                actual_workers = cpu_count
                logger.info(f"Parallel execution enabled with 'auto' - will use {actual_workers} workers")
            else:
                logger.info(f"Parallel execution enabled with {numprocesses} workers")
        else:
            logger.info("Parallel execution not enabled (use -n auto or -n <number>)")
    
    # 存储测试结果以便汇总
    if not hasattr(config, '_test_results'):
        config._test_results = []
    
    logger.info("Pytest configuration completed")


def _create_allure_environment_properties():
    """
    为 Allure 报告创建 environment.properties 文件

    此文件提供将在 Allure 报告中显示的环境信息，有助于识别测试执行环境。
    """
    import platform
    import sys
    
    allure_results_dir = Path(Settings.ALLURE_RESULTS_DIR)
    env_file = allure_results_dir / "environment.properties"
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"Test.Environment={Settings.TEST_ENV}\n")
            f.write(f"Browser.Type={Settings.BROWSER_TYPE}\n")
            f.write(f"Browser.Headless={Settings.HEADLESS}\n")
            f.write(f"Python.Version={sys.version.split()[0]}\n")
            f.write(f"Platform={platform.system()} {platform.release()}\n")
            f.write(f"Platform.Architecture={platform.machine()}\n")
            f.write(f"Parallel.Workers={Settings.PARALLEL_WORKERS}\n")
            f.write(f"Log.Level={Settings.LOG_LEVEL}\n")
            
            if Settings.API_BASE_URL:
                f.write(f"API.Base.URL={Settings.API_BASE_URL}\n")
    except Exception as e:
        import logging
        logging.warning(f"Failed to create Allure environment properties: {e}")


def pytest_sessionstart(session):
    """
    在创建 Session 对象之后、执行数据收集之前调用，并进入运行测试循环。
    由于此时 allure-results 目录已被清理，因此在此处创建 environment.properties 文件是合适的。
    """
    logger = TestLogger.get_logger("SessionStart")
    logger.info("Test Session Starting")
    logger.info(f"Session ID: {session.sessionid if hasattr(session, 'sessionid') else 'N/A'}")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create Allure environment properties file after directory is cleaned
    _create_allure_environment_properties()
    logger.info("Allure environment properties created")


def pytest_sessionfinish(session, exitstatus):
    """
    在整个测试运行结束后，返回退出状态之前调用。

    此钩子执行以下操作：
    - 汇总所有工作进程的测试结果
    - 清理会话级缓存
    - 最终日志记录和报告
    """
    logger = TestLogger.get_logger("SessionFinish")

    logger.info("Test Session Finishing")
    logger.info(f"Exit Status: {exitstatus}")
    logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Aggregate test results
    total = sum(TEST_RESULTS.values())
        
    logger.info("Test Results Summary:")
    logger.info(f"  Total: {total}")
    logger.info(f"  Passed: {TEST_RESULTS['passed']}")
    logger.info(f"  Failed: {TEST_RESULTS['failed']}")
    logger.info(f"  Skipped: {TEST_RESULTS['skipped']}")
    logger.info(f"  Error: {TEST_RESULTS['error']}")
        
    if total > 0:
        pass_rate = (TEST_RESULTS['passed'] / total) * 100
        logger.info(f"  Pass Rate: {pass_rate:.2f}%")
    
    # Clear data cache at session end
    cache = DataCache.get_instance()
    cache.clear()
    logger.info("Data cache cleared at session end")



def pytest_runtest_logreport(report):
    """
    在生成测试报告后调用。

    此钩子收集测试结果，以便在并行工作进程中进行汇总，
    并确保与 Allure 正确集成。
    """
    if report.when == 'call' and hasattr(report, 'config'):
        # Store test result for aggregation
        if hasattr(report.config, '_test_results'):
            result = {
                'nodeid': report.nodeid,
                'outcome': report.outcome,
                'duration': report.duration,
                'when': report.when,
            }
            report.config._test_results.append(result)
        
        # Log test result details
        logger = TestLogger.get_logger("TestReport")
        logger.info(f"Test: {report.nodeid}")
        logger.info(f"Status: {report.outcome}")
        logger.info(f"Duration: {report.duration:.2f}s")


def pytest_collection_finish(session):
    """
    在收集和修改完成后调用。
    """
    logger = TestLogger.get_logger("Collection")
    logger.info(f"Collected {len(session.items)} test items")
    
    # Log test distribution information if using xdist
    if hasattr(session.config, 'workerinput'):
        worker_id = session.config.workerinput.get('workerid', 'unknown')
        logger.info(f"Worker {worker_id} will execute {len(session.items)} tests")


# ==================== Session-Level Fixtures ====================
@pytest.fixture(scope="session", autouse=True)
def session_setup_teardown():
    """
    会话级设置和清理

    在测试会话开始时初始化测试框架，并在会话结束时执行清理工作。

    此测试装置确保：
    - 正确初始化测试环境
    - 所有测试完成后清理会话级缓存
    - 记录会话生命周期事件
    """
    logger = TestLogger.get_logger("SessionFixture")
    logger.info("Session fixture setup starting")
    
    yield
    
    # Session teardown
    logger.info("Session fixture teardown starting")
    
    # Clear data cache to prevent data leakage between test sessions
    cache = DataCache.get_instance()
    cache.clear()
    logger.info("Data cache cleared in session fixture")


@pytest.fixture(scope="session")
def worker_id(request):
    """
    提供并行执行的工作进程 ID。
    
    Returns:
        str: Worker ID (e.g., 'gw0', 'gw1') or 'master' if not running in parallel
    """
    if hasattr(request.config, 'workerinput'):
        return request.config.workerinput['workerid']
    return 'master'


@pytest.fixture(scope="session")
def cpu_cores():
    """
    提供系统上可用的 CPU 核心数。
    
    Returns:
        int: Number of CPU cores
    """
    return multiprocessing.cpu_count()


# ==================== Function-Level Fixtures ====================

@pytest.fixture(scope="function", autouse=True)
def test_logger(request):
    """
    功能级日志记录器

    为每个测试提供日志记录器，并记录测试的开始/结束信息。
    测试完成后，日志会自动附加到 Allure 报告中。

    """
    logger = TestLogger.get_logger(f"Test.{request.node.name}")

    logger.info(f"Test started: {request.node.name}")
    logger.info(f"Test location: {request.node.nodeid}")
    
    yield logger

    logger.info(f"Test finished: {request.node.name}")
    
    # Attach test log to Allure report
    try:
        from core.reporting.allure_helper import AllureHelper
        import logging
        
        # Get the log file path for this test
        log_dir = Path(Settings.LOG_DIR)
        if log_dir.exists():
            # Find the most recent log file
            log_files = sorted(log_dir.glob("test_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if log_files:
                log_file = log_files[0]
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                AllureHelper.attach_log(log_content, f"Test Log: {request.node.name}")
    except Exception as e:
        logger.warning(f"Failed to attach log to Allure: {e}")


@pytest.fixture(scope="function")
def test_context(request, worker_id):
    """
    提供测试上下文信息，包括工作进程 ID 和测试元数据。
    
    Returns:
        dict: Test context with worker_id, test_name, and test_id
    """
    return {
        'worker_id': worker_id,
        'test_name': request.node.name,
        'test_id': request.node.nodeid,
        'test_location': str(request.fspath),
    }
