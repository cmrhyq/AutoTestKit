"""
弹性计算 OpenAPI Namespace 接口测试脚本

基于 JMeter auto_test_pro/auto-test/files/elastic-compute/openapi/namespace-api.jmx 转换。
覆盖 elastic-compute namespace 相关 2 个用例：
- 查询 Namespace 列表
- 查询 Namespace 详情
"""
from typing import Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    PanJiElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基弹性计算 OpenAPI 服务")
@allure.story("Elastic Compute Namespace OpenAPI 接口测试")
class TestEcOpenapiNamespace:
    """
    Elastic Compute Namespace OpenAPI 测试（Bearer 鉴权）

    数据流：查询 Namespace 列表 → 提取第一个 sysCode → 查询 Namespace 详情
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        service = PanJiElasticComputeOpenService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    @allure.title("查询 Namespace 列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_namespaces(self, ec_service, api_env, api_cache):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询 Namespace 列表"):
                cell_code = api_env.get("cellCode")
                response_json = ec_service.list_namespaces(cell_code)
            with AllureHelper.step("验证响应并缓存第一条 sysCode"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"
                if response_json.get("code") == 0:
                    data = response_json.get("data") or []
                    if isinstance(data, list) and data:
                        first_sys_code = data[0].get("sysCode") or data[0].get("code")
                        if first_sys_code:
                            api_cache.set("ec_first_sys_code", first_sys_code)

    @allure.title("查询 Namespace 详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_namespace_detail(self, ec_service, api_env, api_cache):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("确定 sys_code：优先取缓存 ec_first_sys_code，否则用 env sysCode"):
                cell_code = api_env.get("cellCode")
                sys_code = (
                    api_cache.get("ec_first_sys_code")
                    if api_cache.has("ec_first_sys_code")
                    else api_env.get("sysCode")
                )
                if not sys_code:
                    pytest.skip("缺少 upstream 依赖：无法解析 sys_code")

            with AllureHelper.step(f"发送 GET 请求查询 Namespace 详情：cell={cell_code}, sys={sys_code}"):
                response_json = ec_service.get_namespace_detail(cell_code, sys_code)

            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"
