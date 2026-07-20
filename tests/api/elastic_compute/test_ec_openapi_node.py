"""
弹性计算 OpenAPI Node 节点接口测试脚本

基于 JMeter auto_test_pro/auto-test/files/elastic-compute/openapi/Node.jmx 转换。
覆盖 4 个 Node 接口：
- 查询指定 Node / 查询全集群 Node 列表 / 增量更新 Node / 全量更新 Node
"""
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    PanJiElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基弹性计算 OpenAPI 服务")
@allure.story("Elastic Compute Node OpenAPI 接口测试")
class TestEcOpenapiNode:
    """
    Elastic Compute Node OpenAPI 测试（Bearer 鉴权）
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        service = PanJiElasticComputeOpenService(
            base_url=api_env.get("api_base_url"),
            logger=api_logger,
        )
        yield service
        service.close()

    @staticmethod
    def _minimal_node_body(name: str) -> Dict[str, Any]:
        """构造 Node 最小对象（更新用），来源 JMX Node.jmx body 精简"""
        return {
            "apiVersion": "v1",
            "kind": "Node",
            "metadata": {"name": name},
            "spec": {"unschedulable": False},
        }

    @allure.title("查询指定 Node")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_node_detail(self, ec_service, api_env):
        cell_code = api_env.get("ec_cell_code")
        name = api_env.get("ec_node_name")
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(f"查询 Node: cell={cell_code}, name={name}"):
                response_json = ec_service.get_node_detail(
                    cell_code=cell_code, name=name
                )
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("查询全集群所有 Node 列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_nodes(self, ec_service, api_env):
        cell_code = api_env.get("ec_cell_code")
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(f"查询全集群 Node 列表: cell={cell_code}"):
                response_json = ec_service.list_nodes(cell_code=cell_code)
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("增量更新指定 Node")
    @allure.severity(allure.severity_level.NORMAL)
    def test_patch_node(self, ec_service, api_env):
        cell_code = api_env.get("ec_cell_code")
        name = api_env.get("ec_node_name")
        payload = {"metadata": {"labels": {"paas-test": "true"}}}
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(f"PATCH Node: cell={cell_code}, name={name}"):
                response_json = ec_service.patch_node(
                    cell_code=cell_code, name=name, payload=payload
                )
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("全量更新指定 Node")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_node(self, ec_service, api_env):
        cell_code = api_env.get("ec_cell_code")
        name = api_env.get("ec_node_name")
        payload = self._minimal_node_body(name)
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(f"PUT Node: cell={cell_code}, name={name}"):
                response_json = ec_service.update_node(
                    cell_code=cell_code, name=name, payload=payload
                )
            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"
