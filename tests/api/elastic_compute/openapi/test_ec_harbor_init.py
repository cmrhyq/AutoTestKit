"""
弹性计算 OpenAPI Harbor-Init 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/harbor-init.jmx
线程组: Thread Group - harbor_init
测试内容：Harbor 版本信息刷新接口
"""
import allure
import pytest

from base.api.entity.elastic_compute_openapi import HarborInitPublicParams
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Harbor-Init 接口")
class TestEcOpenapiHarborInit:
    """
    对应 JMeter 脚本: harbor-init.jmx
    线程组: Thread Group - harbor_init

    单接口：更新 harbor 版本信息（refreshHarborVersion），需 admin 权限。
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> HarborInitPublicParams:
        """提取 Harbor-Init 测试所需的公共参数。"""
        return HarborInitPublicParams(harbor_id=api_env.get("harborId"))

    @allure.title("刷新 Harbor 版本信息")
    @allure.description("调用 refreshHarborVersion 接口刷新指定 harbor 的版本信息")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(1)
    def test_refresh_harbor_version(self, ec_service, public_params):
        """调用 refreshHarborVersion 接口，断言业务码为成功。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.refresh_harbor_version(
                harbor_id=public_params.harbor_id
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"刷新 Harbor 版本信息失败, code: {resp.get('code')}, 响应: {resp}"
            )
