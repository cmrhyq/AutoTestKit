"""
弹性计算 OpenAPI 资源采集接口测试脚本

基于 JMeter auto_test_pro/auto-test/files/elastic-compute/openapi/elastic-computer-resource-collection.jmx 转换。
覆盖 5 个采集类只读接口：
- 集群配额信息 / 租户配额信息 / 集群资源信息 / 中间件信息 / 应用组件系统配额信息
"""
from typing import Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    PanJiElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Resource Collection OpenAPI 接口")
class TestEcOpenapiResourceCollection:
    """
    Elastic Compute Resource Collection OpenAPI 测试（Bearer 鉴权）
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

    @allure.title("查询集群配额信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_cluster_quota(self, ec_service):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询集群配额信息"):
                response_json = ec_service.list_cluster_quota()
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("查询租户配额信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_tenant_quota(self, ec_service):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询租户配额信息"):
                response_json = ec_service.list_tenant_quota()
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("查询集群资源信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_cluster_resource(self, ec_service):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询集群资源信息"):
                response_json = ec_service.list_cluster_resource()
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("查询中间件信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_middleware_info(self, ec_service):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询中间件信息"):
                response_json = ec_service.list_middleware_info()
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("查询应用/组件系统配额信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_system_quota(self, ec_service):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询系统配额信息"):
                response_json = ec_service.list_system_quota()
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"
