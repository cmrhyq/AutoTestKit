"""
UI 测试专用的 conftest 配置

该文件仅在运行 UI 测试时加载 UI fixtures，
避免在 API 测试时初始化浏览器。

同时在此定义 `pytest_runtest_makereport` hook，将测试各阶段结果
（rep_setup / rep_call / rep_teardown）挂载到 test item 上，
供 base/ui/fixtures.py 中的 fixture 判断测试是否失败以触发截图。
"""
import pytest

from base.ui.fixtures import *  # noqa: F401,F403


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook: 在测试报告生成时捕获测试结果

    在 setup / call / teardown 三个阶段分别把 report 对象挂载到 test item 上，
    命名为 rep_setup / rep_call / rep_teardown，供 fixture teardown 阶段读取。

    Args:
        item: 测试项
        call: 测试调用信息
    """
    outcome = yield
    rep = outcome.get_result()

    setattr(item, f"rep_{rep.when}", rep)
