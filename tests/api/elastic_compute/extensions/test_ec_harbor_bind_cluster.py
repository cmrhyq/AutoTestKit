"""
Harbor 仓库绑定集群接口测试

转换自 JMeter 脚本: harbor-bindcluster.jmx
测试内容：Harbor 仓库绑定集群
"""

import allure
import pytest

from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.reporting.allure_helper import AllureHelper

BUSINESS_SUCCESS_CODE = 2000


@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Harbor 仓库绑定集群接口")
class TestEcExtensionsHarborBindCluster:
    """
    对应 JMeter 脚本: harbor-bindcluster.jmx
    线程组: Thread Group - harbor仓库绑定
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
        """提取 Harbor 绑定测试所需的公共参数。"""
        return {
            "cluster_id": int(api_env.get("clusterId", 1)),
            "harbor_name": api_env.get("harborName", "harbor-107"),
        }

    @staticmethod
    def _build_bind_payload(cluster_id: int, harbor_name: str) -> dict:
        """构造 Harbor 绑定集群请求体。"""
        return {
            "clusterId": cluster_id,
            "harborName": harbor_name,
        }

    @pytest.mark.order(1)
    @allure.title("Harbor 仓库绑定集群")
    @allure.description("将 Harbor 仓库绑定到指定集群，验证绑定成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_harbor_bind_cluster(self, ec_ext_service, public_params):
        """Harbor 仓库绑定集群，断言业务码为成功。"""
        cluster_id = public_params["cluster_id"]
        harbor_name = public_params["harbor_name"]

        with AllureHelper.api_test(ec_ext_service):
            payload = self._build_bind_payload(cluster_id, harbor_name)
            response_json = ec_ext_service.harbor_bind_cluster(payload=payload)

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Harbor 绑定集群失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
