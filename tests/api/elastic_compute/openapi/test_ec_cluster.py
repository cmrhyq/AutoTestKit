"""
弹性计算 OpenAPI 集群信息接口测试脚本

覆盖 elastic-compute 集群相关 2 个用例：
- v1 查询集群列表
- v2 查询集群列表
"""
from typing import Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper
from core.constants import Tenant

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Cluster OpenAPI 接口")
class TestEcOpenapiCluster:
    """
    Elastic Compute Cluster OpenAPI 测试（Bearer 鉴权）
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @allure.title("v1 查询集群列表")
    @allure.description("使用 v1 接口查询 paas 系统下的集群列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_cluster_info_v1(self, ec_service):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询 v1 集群列表"):
                response_json = ec_service.list_cluster_info_v1()
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("v2 查询集群列表")
    @allure.description("使用 v2 接口查询运行面集群信息列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_cluster_info_v2(self, ec_service):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 GET 请求查询 v2 集群列表"):
                response_json = ec_service.list_cluster_info_v2()
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"
