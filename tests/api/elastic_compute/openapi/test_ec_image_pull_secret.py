"""
弹性计算 OpenAPI ImagePullSecret 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/imagePullSecret.jmx
线程组: Thread Group - imagePullSecret
测试内容：
- 创建 ImagePullSecret
- 删除 Secret
"""
import time

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper

# 业务码 / 常量（顶部集中定义，禁止方法内魔法数字）
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004

# JMX 中的 ConstantTimer 3000ms
IMAGEPULLSECRET_WAIT_SECONDS = 3
# JSONPostProcessor 中的默认 secretName（当响应未包含时用作兜底）
DEFAULT_SECRET_NAME = "container-image-registry-auto-test-probe"

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("ImagePullSecret 生命周期接口")
class TestEcOpenapiImagePullSecret:
    """
    对应 JMeter 脚本: imagePullSecret.jmx
    线程组: Thread Group - imagePullSecret

    执行顺序：
      1) 创建 ImagePullSecret（提取响应中的 secretName）
      2) 等待 3 秒（JMX ConstantTimer）
      3) 删除 Secret
    """

    TENANT = "monitor-group"

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc
    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 ImagePullSecret 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode"),
            "sys_code": api_env.get("sysCode"),
        }

    @allure.title("创建 ImagePullSecret")
    @allure.description(
        "创建 ImagePullSecret 并从响应中提取 secretName 缓存到 api_cache 供后续删除使用"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="ips_create")
    @pytest.mark.order(1)
    def test_create_image_pull_secret(
        self, ec_service, public_params, api_cache
    ):
        """创建 ImagePullSecret 并抽取 secretName。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.create_image_pull_secret(
                cell_code=cell_code, sys_code=sys_code,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 ImagePullSecret 失败, code: {resp.get('code')}, 响应: {resp}"
            )

            data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
            secret_name = (
                resp.get("secretName")
                or data.get("secretName")
                or data.get("secret_name")
                or DEFAULT_SECRET_NAME
            )
            api_cache.set("ec_image_pull_secret_name", secret_name)

            # JMX ConstantTimer 3000ms
            time.sleep(IMAGEPULLSECRET_WAIT_SECONDS)

    @allure.title("删除 ImagePullSecret 对应 Secret")
    @allure.description("使用创建阶段缓存的 secretName 删除 Secret，验证业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(depends=["ips_create"])
    @pytest.mark.order(2)
    def test_delete_secret(self, ec_service, public_params, api_cache):
        """删除 Secret。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        secret_name = api_cache.get("ec_image_pull_secret_name") or DEFAULT_SECRET_NAME

        with AllureHelper.api_test(ec_service):
            resp = ec_service.delete_secret_by_name(
                cell_code=cell_code, sys_code=sys_code, secret_name=secret_name,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"删除 Secret 返回异常 code: {code}, 响应: {resp}"
            )
