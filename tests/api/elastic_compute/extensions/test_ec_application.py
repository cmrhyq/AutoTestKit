"""
弹性计算 extensions/applications 接口测试脚本

基于 JMeter auto_test_pro/auto-test/files/elastic-compute/extensions/applications.jmx 转换。
覆盖 elastic-compute 应用搜索 1 个用例：
- searchApp by kinds

extensions 类走 apikey 鉴权（不走 Bearer token），因此本类不需要 _login。
"""
from typing import Dict

import allure
import pytest

from base.api.services.elastic_compute_ext_service import (
    PanJiElasticComputeExtService,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基弹性计算 Extensions 服务")
@allure.story("Elastic Compute Extensions Application 接口测试")
class TestEcExtensionsApplication:
    """
    Elastic Compute Extensions Application 测试

    使用 apikey / username / tenantCode 请求头鉴权，故本测试类：
    - TENANT = None
    - 不定义 autouse _login fixture
    """

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, api_env, api_logger):
        service = PanJiElasticComputeExtService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    @allure.title("按 kinds 搜索应用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_app(self, ec_ext_service, api_env):
        with AllureHelper.api_test(ec_ext_service):
            with AllureHelper.step("发送 GET 请求按 kinds 搜索应用"):
                kinds = api_env.get("nginxImageName") or "nginx"
                response_json = ec_ext_service.search_app(kinds)
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"
