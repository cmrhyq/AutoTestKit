"""
弹性计算 OpenAPI ScaledObject 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/ScaledObject.jmx
线程组: Thread Group - ScaledObject完整生命周期
测试内容：ScaledObject 完整生命周期（查询/清理 → 创建 → 更新 → 删除）
"""
from typing import Any, Dict

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
@allure.story("ScaledObject 生命周期接口")
class TestEcOpenapiScaledObject:
    """
    对应 JMeter 脚本: ScaledObject.jmx
    线程组: Thread Group - ScaledObject完整生命周期

    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：查询+清理 → 创建 → 更新 → 删除
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
        """提取 ScaledObject 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "PROD_PLANE1_CELL3"),
            "sys_code": api_env.get("sysCode", "test"),
            "so_name": "test-scaled-object-001",
            "workload_kind": api_env.get("soWorkloadKind", "Deployment"),
            "workload_name": api_env.get("soWorkloadName", "auto-test-deploy-probe-ns-test-0002"),
        }

    # ---------------- Body helpers ----------------

    @staticmethod
    def _build_create_payload(
        name: str, workload_kind: str, workload_name: str,
    ) -> Dict[str, Any]:
        """
        构造创建 ScaledObject 请求体。

        源自 JMX ScaledObject.jmx 中"创建ScaledObject"sampler 的 postBodyRaw。
        """
        return {
            "name": name,
            "workloadKind": workload_kind,
            "workloadName": workload_name,
            "pollingInterval": 30,
            "cooldownPeriod": 300,
            "minReplicaCount": 1,
            "maxReplicaCount": 5,
            "restoreToOriginalReplicaCount": False,
            "timezone": "Asia/Shanghai",
            "start": "30 * * * *",
            "end": "45 * * * *",
            "desiredReplicas": 3,
        }

    @staticmethod
    def _build_update_payload() -> Dict[str, Any]:
        """
        构造更新 ScaledObject 请求体。

        源自 JMX ScaledObject.jmx 中"更新ScaledObject"sampler 的 postBodyRaw。
        """
        return {
            "start": "35 * * * *",
            "end": "45 * * * *",
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询指定 ScaledObject")
    @allure.description("查询指定 ScaledObject 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="scaled_object_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_scaled_object_and_cleanup(self, ec_service, public_params):
        """查询指定 ScaledObject，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        so_name = public_params["so_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_scaled_object(
                cell_code=cell_code, sys_code=sys_code, name=so_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 ScaledObject 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            # 若已存在，先删除以保证幂等
            if ec_get_code == BUSINESS_SUCCESS_CODE:
                del_resp = ec_service.delete_scaled_object(
                    cell_code=cell_code, sys_code=sys_code, name=so_name,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除已存在的 ScaledObject 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

    @allure.title("创建 ScaledObject")
    @allure.description("创建 ScaledObject 资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="scaled_object_create", depends=["scaled_object_query_and_cleanup"],
    )
    @pytest.mark.order(2)
    def test_create_scaled_object(self, ec_service, public_params):
        """创建 ScaledObject，断言创建成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        so_name = public_params["so_name"]
        workload_kind = public_params["workload_kind"]
        workload_name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_create_payload(
                so_name, workload_kind, workload_name,
            )
            create_resp = ec_service.create_scaled_object(
                cell_code=cell_code, sys_code=sys_code, payload=create_payload,
            )

            assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 ScaledObject 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )

    @allure.title("更新 ScaledObject")
    @allure.description("使用 PUT 方法更新 ScaledObject 的定时伸缩参数，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="scaled_object_update", depends=["scaled_object_create"],
    )
    @pytest.mark.order(3)
    def test_update_scaled_object(self, ec_service, public_params):
        """PUT 更新 ScaledObject，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        so_name = public_params["so_name"]

        with AllureHelper.api_test(ec_service):
            update_payload = self._build_update_payload()
            update_resp = ec_service.update_scaled_object(
                cell_code=cell_code, sys_code=sys_code, name=so_name,
                payload=update_payload,
            )

            assert update_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"更新 ScaledObject 失败, code: {update_resp.get('code')}, 响应: {update_resp}"
            )

    @allure.title("删除 ScaledObject")
    @allure.description("删除创建的 ScaledObject 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="scaled_object_delete", depends=["scaled_object_update"],
    )
    @pytest.mark.order(4)
    def test_delete_scaled_object(self, ec_service, public_params):
        """删除 ScaledObject，断言删除成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        so_name = public_params["so_name"]

        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_scaled_object(
                cell_code=cell_code, sys_code=sys_code, name=so_name,
            )

            assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"删除 ScaledObject 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )
