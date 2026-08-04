"""
弹性计算 Native Node 接口测试

转换自 JMeter 脚本: node-api.jmx
测试内容：Node 原生接口只读测试（查询列表 + 查询指定 Node）

注意：Node 是 cluster-scoped 资源。JMX 只覆盖了只读接口（list + get by name）,
      name 从 list 结果的第一项 metadata.name 提取。
"""
import allure
import pytest

from base.api.services.elastic_compute_native_service import (
    ElasticComputeNativeService,
)
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper

logger = get_logger(__name__)

HTTP_OK = 200


@pytest.mark.api
@pytest.mark.native
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Native接口")
@allure.story("Node 原生接口")
class TestEcNativeNode:
    """
    对应 JMeter 脚本: node-api.jmx
    线程组: Thread Group - Node API
    """

    TENANT = "tenant_admin"

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Node 测试所需的公共参数。"""
        return {
            "cluster_id": str(api_env.get("clusterId", "1")),
        }

    # ==================== 只读测试（每接口一函数）====================

    @pytest.mark.dependency(name="node_list")
    @pytest.mark.order(1)
    @allure.title("查询 Node 列表")
    @allure.description("查询集群 Node 列表，验证返回 200 且提取首项 name")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_nodes(self, native_service, public_params, api_cache):
        """
        查询 Node 列表，断言成功并从响应中提取 items[0].metadata.name。

        对应 JMX：弹性计算_native_node-api_查询node list + JSON 提取器 name=$.items[0].metadata.name
        """
        cluster_id = public_params["cluster_id"]

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_nodes(cluster_id=cluster_id)

            assert native_service.last_response.status_code == HTTP_OK, (
                f"查询 Node 列表失败,"
                f" status={native_service.last_response.status_code}"
            )
            items = list_resp.get("items", [])
            assert items, f"Node 列表为空, 响应: {list_resp}"

            first_node_name = items[0].get("metadata", {}).get("name")
            assert first_node_name, (
                f"未能从 Node 列表首项提取 metadata.name, 响应: {list_resp}"
            )
            api_cache.set("ec_node_first_name", first_node_name)
            logger.info(f"Cached first node name: {first_node_name}")

    @pytest.mark.dependency(name="node_get", depends=["node_list"])
    @pytest.mark.order(2)
    @allure.title("查询指定 Node")
    @allure.description("使用列表首项 name 查询指定 Node，验证返回 200 且包含 spec/metadata")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_node(self, native_service, public_params, api_cache):
        """
        查询指定 Node，断言成功并验证响应结构。

        对应 JMX：弹性计算_native_node-api_查询node + JSON 提取器 spec/metadata
        """
        cluster_id = public_params["cluster_id"]
        name = api_cache.get("ec_node_first_name")
        assert name, "缓存中未找到 node_first_name，请检查 list 用例是否成功执行"

        with AllureHelper.api_test(native_service):
            get_resp = native_service.get_node(cluster_id=cluster_id, name=name)

            assert native_service.last_response.status_code == HTTP_OK, (
                f"查询指定 Node 失败,"
                f" status={native_service.last_response.status_code}"
            )
            assert "spec" in get_resp, (
                f"Node 响应缺少 spec 字段, 响应: {get_resp}"
            )
            assert "metadata" in get_resp, (
                f"Node 响应缺少 metadata 字段, 响应: {get_resp}"
            )
