"""
线程安全测试

测试框架在并行执行时的线程安全性，包括：
- DataCache 的并发访问（读、写、混合操作）
- Logger 的并发写入和实例获取
- 混合场景的并发测试（Cache + Logger）
- 压力测试（高并发场景）

本测试套件验证了以下线程安全机制：
1. DataCache 使用 threading.Lock 保护数据字典的并发访问
2. TestLogger 使用 threading.Lock 保护日志系统初始化和 logger 字典访问
3. Python logging 模块的 FileHandler 本身是线程安全的
4. 文件读取操作使用额外的锁保护
"""

import threading
import time
import pytest
from pathlib import Path
from core.cache.data_cache import DataCache
from core.log import get_logger


class TestThreadSafety:
    """线程安全综合测试"""
    
    def setup_method(self):
        """每个测试前重置状态"""
        DataCache.get_instance().clear()
        TestLogger.reset()
        TestLogger.setup_logger()
    
    def test_data_cache_concurrent_writes(self):
        """测试 DataCache 的并发写入"""
        cache = DataCache.get_instance()
        cache.clear()
        
        num_threads = 20
        operations_per_thread = 100
        errors = []
        
        def worker(thread_id):
            """每个线程执行写入操作"""
            try:
                for i in range(operations_per_thread):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"
                    cache.set(key, value)
                    
                    # 立即读取验证
                    retrieved = cache.get(key)
                    if retrieved != value:
                        errors.append(f"Thread {thread_id}: Expected {value}, got {retrieved}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
        
        # 创建并启动多个线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # 验证所有数据都正确存储
        expected_size = num_threads * operations_per_thread
        assert cache.size() == expected_size
    
    def test_data_cache_concurrent_reads(self):
        """测试 DataCache 的并发读取"""
        cache = DataCache.get_instance()
        cache.clear()
        
        # 预先填充数据
        test_data = {}
        for i in range(100):
            key = f"key_{i}"
            value = f"value_{i}"
            cache.set(key, value)
            test_data[key] = value
        
        num_threads = 20
        reads_per_thread = 100
        errors = []
        
        def reader(thread_id):
            """每个线程执行读取操作"""
            try:
                for i in range(reads_per_thread):
                    key = f"key_{i % 100}"
                    expected = test_data[key]
                    actual = cache.get(key)
                    
                    if actual != expected:
                        errors.append(f"Thread {thread_id}: Key {key} - Expected {expected}, got {actual}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
        
        # 创建并启动多个线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=reader, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0, f"Errors occurred: {errors}"
    
    def test_data_cache_concurrent_mixed_operations(self):
        """测试 DataCache 的并发混合操作（读写混合）"""
        cache = DataCache.get_instance()
        cache.clear()
        
        # 预先填充一些数据
        for i in range(50):
            cache.set(f"initial_key_{i}", f"initial_value_{i}")
        
        num_threads = 15
        operations_per_thread = 100
        errors = []
        
        def mixed_worker(thread_id):
            """每个线程执行混合操作"""
            try:
                for i in range(operations_per_thread):
                    if i % 3 == 0:
                        # 写入操作
                        key = f"thread_{thread_id}_key_{i}"
                        value = f"thread_{thread_id}_value_{i}"
                        cache.set(key, value)
                    elif i % 3 == 1:
                        # 读取操作
                        key = f"initial_key_{i % 50}"
                        cache.get(key)
                    else:
                        # 检查操作
                        key = f"thread_{thread_id}_key_{i - 1}"
                        cache.has(key)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
        
        # 创建并启动多个线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=mixed_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0, f"Errors occurred: {errors}"
    
    def test_logger_concurrent_writes(self):
        """测试 Logger 的并发写入"""
        num_threads = 20
        logs_per_thread = 50
        errors = []
        
        def log_worker(thread_id):
            """每个线程执行日志写入"""
            try:
                logger = get_logger(f"test_thread_{thread_id}")
                for i in range(logs_per_thread):
                    logger.info(f"Thread {thread_id} - Log message {i}")
                    logger.debug(f"Thread {thread_id} - Debug message {i}")
                    logger.warning(f"Thread {thread_id} - Warning message {i}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
        
        # 创建并启动多个线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=log_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # 验证日志文件存在且包含内容
        log_file = TestLogger.get_log_file_path()
        assert log_file is not None
        assert Path(log_file).exists()
        
        # 读取日志文件验证内容
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
            # 验证至少有一些日志内容
            assert len(log_content) > 0
    
    def test_logger_concurrent_get_logger(self):
        """测试并发获取 Logger 实例"""
        num_threads = 30
        errors = []
        loggers = {}
        lock = threading.Lock()
        
        def get_logger_worker(thread_id):
            """每个线程获取 logger 实例"""
            try:
                logger_name = f"test_logger_{thread_id % 10}"  # 10个不同的logger名称
                logger = get_logger(logger_name)
                
                with lock:
                    if logger_name not in loggers:
                        loggers[logger_name] = logger
                    else:
                        # 验证返回的是同一个实例
                        if loggers[logger_name] is not logger:
                            errors.append(f"Thread {thread_id}: Different logger instance for {logger_name}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
        
        # 创建并启动多个线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=get_logger_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # 验证创建了正确数量的 logger
        assert len(loggers) == 10
    
    def test_mixed_cache_and_logger_concurrent_access(self):
        """测试 Cache 和 Logger 的混合并发访问"""
        cache = DataCache.get_instance()
        cache.clear()
        
        num_threads = 15
        operations_per_thread = 50
        errors = []
        
        def mixed_worker(thread_id):
            """每个线程执行混合操作"""
            try:
                logger = get_logger(f"mixed_thread_{thread_id}")
                
                for i in range(operations_per_thread):
                    # 写入缓存
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"
                    cache.set(key, value)
                    
                    # 记录日志
                    logger.info(f"Set cache: {key} = {value}")
                    
                    # 读取缓存
                    retrieved = cache.get(key)
                    
                    # 验证并记录
                    if retrieved != value:
                        error_msg = f"Cache mismatch: expected {value}, got {retrieved}"
                        logger.error(error_msg)
                        errors.append(f"Thread {thread_id}: {error_msg}")
                    else:
                        logger.debug(f"Cache verified: {key}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
        
        # 创建并启动多个线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=mixed_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # 验证缓存大小
        expected_size = num_threads * operations_per_thread
        assert cache.size() == expected_size
    
    def test_stress_concurrent_access(self):
        """压力测试：高并发场景"""
        cache = DataCache.get_instance()
        cache.clear()
        
        num_threads = 50
        operations_per_thread = 100
        errors = []
        
        def stress_worker(thread_id):
            """每个线程执行大量操作"""
            try:
                logger = get_logger(f"stress_thread_{thread_id}")
                
                for i in range(operations_per_thread):
                    # 快速的读写操作
                    key = f"stress_{thread_id}_{i}"
                    value = i * thread_id
                    
                    cache.set(key, value)
                    retrieved = cache.get(key)
                    
                    if retrieved != value:
                        errors.append(f"Thread {thread_id}: Value mismatch at iteration {i}")
                    
                    # 每10次操作记录一次日志
                    if i % 10 == 0:
                        logger.debug(f"Completed {i} operations")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
        
        # 创建并启动多个线程
        threads = []
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=stress_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证没有错误
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # 验证缓存大小
        expected_size = num_threads * operations_per_thread
        assert cache.size() == expected_size
        
        # 输出性能信息
        print(f"\nStress test completed in {duration:.2f} seconds")
        print(f"Total operations: {num_threads * operations_per_thread * 2}")  # 2 = set + get
        print(f"Operations per second: {(num_threads * operations_per_thread * 2) / duration:.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
