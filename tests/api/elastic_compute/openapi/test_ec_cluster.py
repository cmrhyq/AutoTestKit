"""
弹性计算 OpenAPI 集群信息接口测试脚本

基于 JMeter auto_test_pro/auto-test/files/elastic-compute/openapi/cluster.jmx 转换。
覆盖 elastic-compute 集群相关 2 个用例：
- v1 查询集群列表
- v2 查询集群列表
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
@allure.story("Elastic Compute Cluster OpenAPI 接口测试")
class TestEcOpenapiCluster:
    """
    Elastic Compute Cluster OpenAPI 测试（Bearer 鉴权）
    """

    TENANT = "monitor-group"

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

    @allure.title("v1 查询集群列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_cluster_info_v1(self, ec_service):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询 v1 集群列表"):
                response_json = ec_service.list_cluster_info_v1()
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("v2 查询集群列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_cluster_info_v2(self, ec_service):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询 v2 集群列表"):
                response_json = ec_service.list_cluster_info_v2()
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"
