"""
弹性计算 OpenAPI Harbor-Init 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/harbor-init.jmx
线程组: Thread Group - harbor_init
测试内容：Harbor 版本信息刷新接口
"""
import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper

# 业务码 / 常量（顶部集中定义，禁止方法内魔法数字）
BUSINESS_SUCCESS_CODE = 2000


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

    TENANT = "monitor-group"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        """创建服务实例，base_url 从 yaml 显式传入（camelCase key）。"""
        service = ElasticComputeOpenService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Harbor-Init 测试所需的公共参数。"""
        return {
            "harbor_id": api_env.get("harborId"),
        }

    @allure.title("刷新 Harbor 版本信息")
    @allure.description("调用 refreshHarborVersion 接口刷新指定 harbor 的版本信息")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.order(1)
    def test_refresh_harbor_version(self, ec_service, public_params):
        """调用 refreshHarborVersion 接口，断言业务码为成功。"""
        harbor_id = public_params["harbor_id"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.refresh_harbor_version(harbor_id=harbor_id)

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"刷新 Harbor 版本信息失败, code: {resp.get('code')}, 响应: {resp}"
            )
