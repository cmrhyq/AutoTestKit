"""
System Bind 系统绑定接口测试（Extensions - apikey 鉴权）

测试内容：
    1) 查询系统是否有配额信息
    2) 用户与系统绑定接口
    3) 解除用户与系统绑定接口（若 bind 成功才执行，否则跳过）

依赖：
    - config/env_*.yaml 需提供：apiInnerBaseUrl / tenantCode / sysCode / systemBindUsername
"""

import allure
import pytest

from base.api.entity.elastic_compute import SystemBindPublicParams
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("System Bind 系统绑定接口")
class TestEcExtensionsSystemBind:
    """
        check_quota → bind_user → unbind_user（bind code==2000 时执行，否则 skip）
    """

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
    def public_params(self, test_env) -> SystemBindPublicParams:
        """提取 System Bind 测试所需的公共参数。"""
        return SystemBindPublicParams(
            tenant_code=test_env.get("tenantCode", "monitor-group"),
            sys_code=test_env.get("sysCode", "test-sys"),
            username=test_env.get("user", "lzm-admin"),
        )

    # ==================== 1) 查询系统是否有配额信息 ====================

    @pytest.mark.dependency(name="system_bind_check_quota")
    @pytest.mark.order(1)
    @allure.title("查询系统是否有配额信息")
    @allure.description("绑定用户前置检查：确认目标系统在指定租户下已分配配额，断言业务码为 2000")
    @allure.severity(allure.severity_level.NORMAL)
    def test_check_system_quota(self, ec_ext_service, public_params):
        """查询系统配额，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.check_system_quota(
                tenant_code=public_params.tenant_code,
                sys_code=public_params.sys_code,
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询系统配额失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 2) 用户与系统绑定 ====================

    @pytest.mark.dependency(name="system_bind_bind_user", depends=["system_bind_check_quota"])
    @pytest.mark.order(2)
    @allure.title("用户与系统绑定接口")
    @allure.description("断言业务码为 2000；绑定结果 code 存入 api_cache 供 unbind 判断使用")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bind_system_user(self, ec_ext_service, public_params, api_cache):
        """用户与系统绑定，断言业务码为 2000；bind code 缓存到 api_cache。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.bind_system_user(
                sys_code=public_params.sys_code,
                username=public_params.username,
            )
            bind_code = response_json.get("code")
            api_cache.set("system_bind_code", bind_code)

            assert bind_code == ApiCode.SUCCESS, f"用户与系统绑定失败, code: {bind_code}, 响应: {response_json}"

    # ==================== 3) 解除用户与系统绑定 ====================

    @pytest.mark.dependency(name="system_bind_unbind_user", depends=["system_bind_bind_user"])
    @pytest.mark.order(3)
    @allure.title("解除用户与系统绑定接口")
    @allure.description("解除用户与系统的绑定关系；仅在上一步 bind 成功（api_cache 中 bind_code=2000）时执行，断言业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_unbind_system_user(self, ec_ext_service, public_params, api_cache):
        """解除用户与系统绑定；仅在 bind 成功时执行。"""
        bind_code = api_cache.get("system_bind_code")
        if bind_code != ApiCode.SUCCESS:
            pytest.skip(f"上一步 bind 未成功 (code={bind_code})，跳过 unbind")

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.unbind_system_user(
                sys_code=public_params.sys_code,
                username=public_params.username,
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"解除用户与系统绑定失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
