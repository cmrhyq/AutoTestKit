"""
OIDC/Harbor 初始化 接口测试

转换自 JMeter 脚本: oidc-harborinit.jmx
测试内容：获取 OIDC 信息
"""
import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper

# 顶部常量抽取
BUSINESS_SUCCESS_CODE = 2000


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("OIDC/Harbor 初始化接口")
class TestEcOpenapiOidcHarborinit:
    """
    对应 JMeter 脚本: oidc-harborinit.jmx
    线程组: Thread Group - Oidc
    """

    TENANT = "monitor-group"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        """创建服务实例，base_url 从 yaml 显式传入。"""
        service = ElasticComputeOpenService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    # -------------------- 测试用例 --------------------

    @pytest.mark.order(1)
    @allure.title("获取 OIDC 信息")
    @allure.description("调用 OpenAPI 获取 OIDC 配置信息，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_oidc_info(self, ec_service):
        """获取 OIDC 信息，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_oidc_info()

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"获取 OIDC 信息失败, code: {resp.get('code')}, 响应: {resp}"
            )
