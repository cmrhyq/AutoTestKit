"""
应用授权/解除授权接口测试

转换自 JMeter 脚本: app-grant.jmx
测试内容：应用授权、解除应用授权完整流程
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
@allure.story("应用授权/解除授权接口")
class TestEcExtensionsAppGrant:
    """
    对应 JMeter 脚本: app-grant.jmx
    线程组: Thread Group - app grant
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
        """提取应用授权测试所需的公共参数。"""
        return {
            "app_code": api_env.get("grantAppCode", "test-probe-deploy"),
            "grant_user": api_env.get("grantUser", "monitor-admin"),
            "end_time": "2035-12-31 23:59:59",
        }

    @staticmethod
    def _build_grant_payload(grant_user: str, end_time: str) -> dict:
        """构造应用授权请求体。"""
        return {
            "users": [grant_user],
            "endTime": end_time,
        }

    @staticmethod
    def _build_remove_grant_payload(grant_user: str) -> list:
        """构造解除授权请求体。"""
        return [grant_user]

    @pytest.mark.dependency(name="app_grant")
    @pytest.mark.order(1)
    @allure.title("应用授权")
    @allure.description("对指定应用进行用户授权，验证授权成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_grant_app(self, ec_ext_service, public_params):
        """应用授权，断言业务码为成功。"""
        app_code = public_params["app_code"]
        grant_user = public_params["grant_user"]
        end_time = public_params["end_time"]

        with AllureHelper.api_test(ec_ext_service):
            payload = self._build_grant_payload(grant_user, end_time)
            response_json = ec_ext_service.grant_app(
                app_code=app_code,
                payload=payload,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"应用授权失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="app_remove_grant", depends=["app_grant"])
    @pytest.mark.order(2)
    @allure.title("解除应用授权")
    @allure.description("解除指定应用的用户授权，验证解除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_remove_grant_app(self, ec_ext_service, public_params):
        """解除应用授权，断言业务码为成功。"""
        app_code = public_params["app_code"]
        grant_user = public_params["grant_user"]

        with AllureHelper.api_test(ec_ext_service):
            payload = self._build_remove_grant_payload(grant_user)
            response_json = ec_ext_service.remove_grant_app(
                app_code=app_code,
                payload=payload,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"解除应用授权失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
