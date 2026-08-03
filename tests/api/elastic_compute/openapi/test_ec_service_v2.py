"""
弹性计算 OpenAPI Service 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/ServiceV2.jmx
线程组: Thread Group - service
测试内容：Service 完整生命周期（查询/删除/创建/列表/全集群列表/PUT 更新/PATCH 增量更新/删除）
"""
import json
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
@allure.story("Service 生命周期接口")
class TestEcOpenapiServiceV2:
    """
    对应 JMeter 脚本: ServiceV2.jmx
    线程组: Thread Group - service

    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：查询 → 清理已存在 → 创建 → 列表查询 → 全集群列表查询 → PUT更新 → PATCH更新 → 删除清理
    """

    TENANT = "monitor-group"

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc
    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Service 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "test"),
            "sys_code": api_env.get("sysCode", "test-sys"),
            "svc_name": "auto-test-probe-svc-test-0001",
        }

    # ---------------- Body helpers ----------------

    @staticmethod
    def _build_service_create_payload(name: str) -> Dict[str, Any]:
        """构造创建 Service 请求体（ClusterIP 类型）。"""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": name,
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": 80,
                        "targetPort": 8080,
                        "protocol": "TCP",
                        "name": "http",
                    },
                ],
                "selector": {
                    "app": "auto-test-probe",
                },
            },
        }

    @staticmethod
    def _build_service_put_payload(name: str) -> Dict[str, Any]:
        """构造 PUT 全量更新 Service 请求体。"""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": name,
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": 8080,
                        "targetPort": 9090,
                        "protocol": "TCP",
                        "name": "http-updated",
                    },
                ],
                "selector": {
                    "app": "auto-test-probe",
                },
            },
        }

    @staticmethod
    def _build_service_patch_payload() -> Dict[str, Any]:
        """构造 PATCH 增量更新 Service 请求体。"""
        return {
            "metadata": {
                "labels": {
                    "test": "patch-test",
                },
            },
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询指定 Service")
    @allure.description("查询指定 Service 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="service_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_service_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 Service，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        svc_name = public_params["svc_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_service(
                cell_code=cell_code, sys_code=sys_code, name=svc_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 Service 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == BUSINESS_SUCCESS_CODE:
                del_resp = ec_service.delete_service(
                    cell_code=cell_code, sys_code=sys_code, name=svc_name,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除已存在的 Service 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_service_v2_created", False)

    @allure.title("创建 Service 资源")
    @allure.description("创建 ClusterIP 类型 Service，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="service_create", depends=["service_query_and_cleanup"])
    @pytest.mark.order(2)
    def test_create_service(self, ec_service, public_params, api_cache):
        """创建 Service，断言创建成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        svc_name = public_params["svc_name"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_service_create_payload(svc_name)
            create_resp = ec_service.create_service(
                cell_code=cell_code, sys_code=sys_code, payload=create_payload,
            )

            assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 Service 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )
            resp_str = json.dumps(create_resp, ensure_ascii=False)
            assert svc_name in resp_str, (
                f"创建 Service 响应中未包含资源名称 {svc_name}, 响应: {create_resp}"
            )

            api_cache.set("ec_service_v2_created", True)

    @allure.title("查询命名空间 Service 列表")
    @allure.description("查询指定命名空间下 Service 列表，验证包含新创建的 Service")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="service_list_ns", depends=["service_create"])
    @pytest.mark.order(3)
    def test_list_services_by_namespace(self, ec_service, public_params):
        """查询 Namespace 下 Service 列表，断言包含目标 Service。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        svc_name = public_params["svc_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_services_by_ns(
                cell_code=cell_code, sys_code=sys_code,
            )

            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Namespace Service 列表失败, code: {list_resp.get('code')}, "
                f"响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert svc_name in resp_str, (
                f"Namespace Service 列表未找到 {svc_name}, 响应: {list_resp}"
            )

    @allure.title("查询全集群 Service 列表")
    @allure.description("查询全集群所有 Service 列表，验证包含新创建的 Service")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="service_list_cell", depends=["service_create"])
    @pytest.mark.order(4)
    def test_list_services_by_cell(self, ec_service, public_params):
        """查询全集群 Service 列表，断言包含目标 Service。"""
        cell_code = public_params["cell_code"]
        svc_name = public_params["svc_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_services_by_cell(cell_code=cell_code)

            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询全集群 Service 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert svc_name in resp_str, (
                f"全集群 Service 列表未找到 {svc_name}, 响应: {list_resp}"
            )

    @allure.title("PUT 全量更新 Service")
    @allure.description("使用 PUT 方法全量更新 Service 的端口配置，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="service_put", depends=["service_create"])
    @pytest.mark.order(5)
    def test_put_update_service(self, ec_service, public_params):
        """PUT 全量更新 Service，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        svc_name = public_params["svc_name"]

        with AllureHelper.api_test(ec_service):
            put_payload = self._build_service_put_payload(svc_name)
            put_resp = ec_service.update_service(
                cell_code=cell_code, sys_code=sys_code, name=svc_name,
                payload=put_payload,
            )

            assert put_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PUT 更新 Service 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )

    @allure.title("PATCH 增量更新 Service")
    @allure.description("使用 PATCH 方法增量更新 Service 的 labels 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="service_patch", depends=["service_put"])
    @pytest.mark.order(6)
    def test_patch_update_service(self, ec_service, public_params):
        """PATCH 增量更新 Service，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        svc_name = public_params["svc_name"]

        with AllureHelper.api_test(ec_service):
            patch_payload = self._build_service_patch_payload()
            patch_resp = ec_service.patch_service(
                cell_code=cell_code, sys_code=sys_code, name=svc_name,
                payload=patch_payload,
            )

            assert patch_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PATCH 增量更新 Service 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )

    @allure.title("删除 Service 资源")
    @allure.description("删除创建的 Service 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="service_delete", depends=["service_patch"])
    @pytest.mark.order(7)
    def test_delete_service(self, ec_service, public_params, api_cache):
        """删除 Service，断言删除成功并清理缓存标记。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        svc_name = public_params["svc_name"]

        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_service(
                cell_code=cell_code, sys_code=sys_code, name=svc_name,
            )

            assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"删除 Service 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_service_v2_created", False)
