"""
配额管理（租户管理员视角）接口测试

转换自 JMeter 脚本: quota-manager-tenant.jmx
测试内容：租户管理员审批系统资源配额分配和系统资源配额扩缩容
"""
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper

# 顶部常量抽取

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("配额管理接口（租户管理员视角）")
class TestEcOpenapiQuotaManagerTenant:
    """
    对应 JMeter 脚本: quota-manager-tenant.jmx
    线程组: Thread Group - quota-manager-tenant
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc
    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取配额管理（租户）测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "PROD_PLANE1_CELL3"),
            "sys_code": api_env.get("sysCode", "test"),
            "tenant_code": api_env.get("tenantCode", "lzm"),
            "username": api_env.get("user", "lzm-admin"),
        }

    # -------------------- 测试用例 --------------------

    @pytest.mark.order(1)
    @allure.title("租户管理员审批系统资源配额分配")
    @allure.description("租户管理员审批通过系统资源申请时调用配额分配接口，验证返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_allocate_system_quota(self, ec_service, public_params):
        """租户管理员审批系统资源配额分配。"""
        cell_code = public_params["cell_code"]
        tenant_code = public_params["tenant_code"]
        sys_code = public_params["sys_code"]
        username = public_params["username"]

        with AllureHelper.api_test(ec_service):
            payload: Dict[str, Any] = {"username": username}
            resp = ec_service.allocate_system_quota(
                cell_code=cell_code, tenant_code=tenant_code,
                sys_code=sys_code, payload=payload,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"系统配额分配失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(2)
    @allure.title("系统资源配额扩缩容")
    @allure.description("针对系统资源配额进行扩缩容操作，验证返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_scale_system_quota(self, ec_service, public_params):
        """针对系统资源配额进行扩缩容。"""
        cell_code = public_params["cell_code"]
        tenant_code = public_params["tenant_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.scale_system_quota(
                cell_code=cell_code, tenant_code=tenant_code,
                sys_code=sys_code, payload={},
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"系统配额扩缩容失败, code: {resp.get('code')}, 响应: {resp}"
            )
