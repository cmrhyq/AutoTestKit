"""
Harbor 仓库绑定集群接口测试

测试内容：Harbor 仓库绑定集群
"""

import allure
import pytest

from base.api.entity.elastic_compute import (
    HarborBindClusterEntity,
    HarborBindPublicParams,
)
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Harbor 仓库绑定集群接口")
class TestEcExtensionsHarborBindCluster:

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
    def public_params(self, api_env) -> HarborBindPublicParams:
        """提取 Harbor 绑定测试所需的公共参数。"""
        return HarborBindPublicParams(
            cluster_id=int(api_env.get("clusterId", 1)),
            harbor_name=api_env.get("harborName", "harbor-107"),
        )

    @pytest.mark.order(1)
    @allure.title("Harbor 仓库绑定集群")
    @allure.description("将 Harbor 仓库绑定到指定集群，验证绑定成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_harbor_bind_cluster(self, ec_ext_service, public_params):
        """Harbor 仓库绑定集群，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            bind = HarborBindClusterEntity(
                cluster_id=public_params.cluster_id,
                harbor_name=public_params.harbor_name,
            )
            response_json = ec_ext_service.harbor_bind_cluster(bind=bind)

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"Harbor 绑定集群失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
