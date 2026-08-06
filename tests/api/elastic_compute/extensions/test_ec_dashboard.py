"""
Dashboard 资源面板接口测试

转换自 JMeter 脚本: Dashboard.jmx
测试内容：资源信息统计、工作负载和应用服务统计
"""

import allure
import pytest

from base.api.entity.elastic_compute import DashboardPublicParams
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Dashboard 资源面板接口")
class TestEcExtensionsDashboard:
    """
    对应 JMeter 脚本: Dashboard.jmx
    线程组: Dashboard API
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
    def public_params(self, api_env) -> DashboardPublicParams:
        """提取 Dashboard 测试所需的公共参数。"""
        return DashboardPublicParams(
            tenant_code=api_env.get("tenantCode", "tenant_admin"),
            start_time="1715759823000",
            end_time="1715759823000",
        )

    @pytest.mark.dependency(name="dashboard_resource")
    @pytest.mark.order(1)
    @allure.title("查询资源信息统计")
    @allure.description("查询集群、主机、namespace、CPU、内存和PVC等资源统计信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_resource_dashboard(self, ec_ext_service, public_params):
        """查询资源信息统计接口，断言业务码为 2000。"""
        tenant_code = public_params.tenant_code

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_resource_dashboard(
                tenant_code=tenant_code,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询资源统计失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="dashboard_app")
    @pytest.mark.order(2)
    @allure.title("查询工作负载和应用服务统计")
    @allure.description("查询指定时间范围内的工作负载和应用服务统计数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_app_dashboard(self, ec_ext_service, public_params):
        """查询工作负载和应用服务统计接口，断言业务码为 2000。"""
        tenant_code = public_params.tenant_code
        start_time = public_params.start_time
        end_time = public_params.end_time

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_app_dashboard(
                tenant_code=tenant_code,
                start_time=start_time,
                end_time=end_time,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询工作负载统计失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
