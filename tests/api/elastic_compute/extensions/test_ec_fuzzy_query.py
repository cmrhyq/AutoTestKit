"""
模糊查询（持续交付定制接口）测试

测试内容：Helm 应用模糊查询、应用模糊查询
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
@allure.story("模糊查询（持续交付定制）接口")
class TestEcExtensionsFuzzyQuery:

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, api_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=api_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.mark.order(1)
    @allure.title("Helm 应用模糊查询")
    @allure.description("调用 Helm 应用模糊查询服务接口，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_helm_app(self, ec_ext_service):
        """Helm 应用模糊查询，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.search_helm_app()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"Helm 应用模糊查询失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(2)
    @allure.title("应用模糊查询")
    @allure.description("调用应用模糊查询接口，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_app_fuzzy(self, ec_ext_service):
        """应用模糊查询，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.search_app_fuzzy()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"应用模糊查询失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
