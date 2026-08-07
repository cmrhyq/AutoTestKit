"""
弹性计算 OpenAPI Node 节点接口测试脚本

覆盖 4 个 Node 接口：
- 查询指定 Node / 查询全集群 Node 列表 / 增量更新 Node / 全量更新 Node
"""
from typing import Dict

import allure
import pytest

from base.api.entity.elastic_compute.openapi import NodePublicParams
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import Tenant
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Node OpenAPI 接口")
class TestEcOpenapiNode:
    """
    Elastic Compute Node OpenAPI 测试（Bearer 鉴权）
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> NodePublicParams:
        """提取 Node 测试所需的公共参数。"""
        return NodePublicParams(
            cell_code=test_env.get("cellCode"),
            node_ip=test_env.get("nodeIp"),
        )

    @allure.title("查询指定 Node")
    @allure.description("按名称查询指定 Node 详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_node_detail(self, ec_service, public_params):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(
                f"查询 Node: cell={public_params.cell_code}, name={public_params.node_ip}"
            ):
                response_json = ec_service.get_node_detail(
                    cell_code=public_params.cell_code,
                    name=public_params.node_ip,
                )
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("查询全集群所有 Node 列表")
    @allure.description("查询指定单元下全集群的 Node 列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_nodes(self, ec_service, public_params):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(
                f"查询全集群 Node 列表: cell={public_params.cell_code}"
            ):
                response_json = ec_service.list_nodes(
                    cell_code=public_params.cell_code
                )
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("增量更新指定 Node")
    @allure.description("以 strategic merge 方式增量更新指定 Node")
    @allure.severity(allure.severity_level.NORMAL)
    def test_patch_node(self, ec_service, public_params):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(
                f"PATCH Node: cell={public_params.cell_code}, name={public_params.node_ip}"
            ):
                response_json = ec_service.patch_node(
                    cell_code=public_params.cell_code,
                    name=public_params.node_ip,
                    labels={"paas-test": "true"},
                )
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("全量更新指定 Node")
    @allure.description("以完整 Node 对象全量更新指定 Node")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_node(self, ec_service, public_params):
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(
                f"PUT Node: cell={public_params.cell_code}, name={public_params.node_ip}"
            ):
                response_json = ec_service.update_node(
                    cell_code=public_params.cell_code,
                    name=public_params.node_ip,
                    unschedulable=False,
                )
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"
