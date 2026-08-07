"""
Endpoints 管理接口测试

测试内容：查询全集群 Endpoints 列表
"""

import allure
import pytest

from base.api.entity.elastic_compute import EndpointsPublicParams
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Endpoints 管理接口")
class TestEcExtensionsEndpoints:

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, test_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=test_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> EndpointsPublicParams:
        """提取 Endpoints 测试所需的公共参数。"""
        return EndpointsPublicParams(
            cell_code=test_env.get("cellCode", "TEST"),
        )

    @pytest.mark.order(1)
    @allure.title("查询全集群 Endpoints 列表")
    @allure.description("查询指定单元下全集群的 Endpoints 列表信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_endpoints(self, ec_ext_service, public_params):
        """查询全集群 Endpoints 列表，断言业务码为 2000。"""
        cell_code = public_params.cell_code

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.list_endpoints(cell_code=cell_code)

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询 Endpoints 列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
