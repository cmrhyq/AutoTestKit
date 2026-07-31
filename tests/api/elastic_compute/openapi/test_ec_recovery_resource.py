"""
弹性计算 OpenAPI 容灾组件资源接口测试

转换自 JMeter 脚本: elastic-compute/openapi/recovery-resource.jmx
线程组: Thread Group - 容灾组件能力接口完整生命周期
测试内容：容灾组件资源生命周期（查询+清理 → 创建 → 查询验证 → Apply）
"""
import json
from typing import Any, Dict, List

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper

# 业务码 / 常量（顶部集中定义，禁止方法内魔法数字）
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("容灾组件资源生命周期接口")
class TestEcOpenapiRecoveryResource:
    """
    对应 JMeter 脚本: recovery-resource.jmx
    线程组: Thread Group - 容灾组件能力接口完整生命周期

    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：查询+清理 → 创建 → 查询验证 → Apply
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
        """提取容灾组件测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "PROD_PLANE1_CELL3"),
            "sys_code": api_env.get("sysCode", "test"),
            "resource_name": "test-resource-deploy-001",
            "app_name": "app-nginx-test",
            "kind": "Deployment",
            "image": api_env.get("nginxImageName", "hpe_containers/nginx:latest"),
            "tenant_code": api_env.get("paasTenantCode", "monitor-group"),
            "app_code": api_env.get("grantAppCode", "probe-deploy"),
            "plane_code": api_env.get("planeCode", "PLANE"),
            "unit_code": api_env.get("unitCode", "test"),
            "env_code": api_env.get("paasEnvCode", "PROD"),
            "user": api_env.get("user", "PROD"),
        }

    # ---------------- Body helpers ----------------

    @staticmethod
    def _build_create_payload(params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        构造创建容灾组件资源请求体（数组形式）。

        源自 JMX recovery-resource.jmx 中"创建资源"sampler 的 postBodyRaw。
        """
        return [
            {
                "name": params["resource_name"],
                "appName": params["app_name"],
                "kind": params["kind"],
                "image": params["image"],
                "tenantCode": params["tenant_code"],
                "appCode": params["app_code"],
                "planeCode": params["plane_code"],
                "unitCode": params["unit_code"],
                "envCode": params["env_code"],
                "username": params["user"],
            },
        ]

    @staticmethod
    def _build_delete_payload(resource_name: str) -> List[str]:
        """
        构造删除容灾组件资源请求体（名称数组）。

        源自 JMX recovery-resource.jmx 中"删除资源"sampler 的 postBodyRaw。
        """
        return [resource_name]

    @staticmethod
    def _build_apply_payload(params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        构造 Apply 容灾组件资源请求体。

        源自 JMX recovery-resource.jmx 中"Apply资源"sampler 的 postBodyRaw。
        """
        return [
            {
                "name": params["resource_name"],
                "appName": params["app_name"],
                "kind": params["kind"],
                "image": params["image"],
                "tenantCode": params["tenant_code"],
                "appCode": params["app_code"],
                "planeCode": params["plane_code"],
                "unitCode": params["unit_code"],
                "envCode": params["env_code"],
                "username": params["user"],
            },
        ]

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询容灾组件资源列表")
    @allure.description("查询容灾组件资源列表确认当前状态，若目标资源存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="recovery_resource_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_recovery_resource_and_cleanup(self, ec_service, public_params):
        """查询容灾组件资源，若目标资源已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        resource_name = public_params["resource_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_recovery_resources(
                sys_code=sys_code, cell_code=cell_code,
            )
            ec_code = list_resp.get("code")

            assert ec_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询容灾组件资源返回异常 code: {ec_code}, 响应: {list_resp}"
            )

            # 若目标资源存在，先删除
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            if ec_code == BUSINESS_SUCCESS_CODE and resource_name in resp_str:
                del_payload = self._build_delete_payload(resource_name)
                del_resp = ec_service.delete_recovery_resources(
                    cell_code=cell_code, sys_code=sys_code, payload=del_payload,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除已存在的容灾资源失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

    @allure.title("创建容灾组件资源")
    @allure.description("创建容灾组件资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="recovery_resource_create", depends=["recovery_resource_query_and_cleanup"],
    )
    @pytest.mark.order(2)
    def test_create_recovery_resource(self, ec_service, public_params):
        """创建容灾组件资源，断言创建成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_create_payload(public_params)
            create_resp = ec_service.create_recovery_resources(
                cell_code=cell_code, sys_code=sys_code, payload=create_payload,
            )

            assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建容灾组件资源失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )

    @allure.title("查询验证容灾组件资源已创建")
    @allure.description("创建后再次查询容灾组件资源列表，验证目标资源存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="recovery_resource_verify", depends=["recovery_resource_create"],
    )
    @pytest.mark.order(3)
    def test_verify_recovery_resource_created(self, ec_service, public_params):
        """创建后查询验证容灾组件资源已存在。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        resource_name = public_params["resource_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_recovery_resources(
                sys_code=sys_code, cell_code=cell_code,
            )

            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询容灾组件资源列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert resource_name in resp_str, (
                f"容灾组件资源列表中未找到 {resource_name}, 响应: {list_resp}"
            )

    @allure.title("Apply 容灾组件资源")
    @allure.description("Apply 容灾组件资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="recovery_resource_apply", depends=["recovery_resource_verify"],
    )
    @pytest.mark.order(4)
    def test_apply_recovery_resource(self, ec_service, public_params):
        """Apply 容灾组件资源，断言操作成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            apply_payload = self._build_apply_payload(public_params)
            apply_resp = ec_service.apply_recovery_resources(
                cell_code=cell_code, sys_code=sys_code, payload=apply_payload,
            )

            assert apply_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Apply 容灾组件资源失败, code: {apply_resp.get('code')}, 响应: {apply_resp}"
            )
