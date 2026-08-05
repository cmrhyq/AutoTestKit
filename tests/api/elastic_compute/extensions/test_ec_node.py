"""
Node 节点污点查询接口测试（Extensions - apikey 鉴权）

转换自 JMeter 脚本: Node.jmx
测试内容：查询节点污点列表

依赖：
    - config/env_*.yaml 需提供：apiInnerBaseUrl / cellCode / nodeName
"""

import allure
import pytest

from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Node 节点污点查询接口")
class TestEcExtensionsNode:
    """
    对应 JMeter 脚本: Node.jmx
    线程组: Thread Group - Node
    """

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, api_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=api_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Node 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "test"),
            "node_name": api_env.get("nodeIp", "100.10.30.113"),
        }

    # ==================== 查询节点污点列表 ====================

    @pytest.mark.order(1)
    @allure.title("查询节点污点列表")
    @allure.description(
        "通过 nodeName query 参数查询指定节点污点列表，断言业务码为成功。"
        "对应 JMX：GET /elastic-compute/v2/cells/{cellCode}/nodes/taints?nodeName=..."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_node_taints(self, ec_ext_service, public_params):
        """查询节点污点列表，断言业务码为成功。"""
        cell_code = public_params["cell_code"]
        node_name = public_params["node_name"]

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.list_node_taints(
                cell_code=cell_code,
                node_name=node_name,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询节点污点列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
