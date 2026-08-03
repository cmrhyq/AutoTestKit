"""
Pod 接口测试

转换自 JMeter 脚本: pod.jmx
测试内容：Pod 完整生命周期（查询、创建、列表、全集群列表、事件列表、日志、PUT更新、PATCH更新、删除）
"""
import json
import time
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper

# 顶部常量抽取
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004
POD_CREATE_WAIT_SECONDS = 10

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Pod 生命周期接口")
class TestEcOpenapiPod:
    """
    对应 JMeter 脚本: pod.jmx
    线程组: Thread Group - pod
    """

    TENANT = "monitor-group"

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc
    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Pod 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "TEST"),
            "sys_code": api_env.get("sysCode", "test-admin"),
            "pod_name": "openapi-test-nginx-pod",
            "pod_image": api_env.get("nginxImageName", "tools/nginx:x86"),
            "container_name": "container0",
        }

    # -------------------- Payload 构造 --------------------

    @staticmethod
    def _build_create_payload(name: str, image: str) -> Dict[str, Any]:
        """构造 Pod 创建请求体。"""
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": name,
                "labels": {
                    "name": name,
                    "kind": "Pod",
                },
            },
            "spec": {
                "containers": [
                    {
                        "image": image,
                        "name": "container0",
                        "ports": [
                            {
                                "containerPort": 8080,
                                "name": "port0",
                                "protocol": "TCP",
                            }
                        ],
                    }
                ]
            },
        }

    @staticmethod
    def _build_patch_payload() -> Dict[str, Any]:
        """构造 Pod PATCH 增量更新请求体。"""
        return {
            "metadata": {
                "labels": {
                    "test": "patch-update",
                },
            },
        }

    # -------------------- 测试用例 --------------------

    @pytest.mark.dependency(name="pod_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 Pod 并清理环境")
    @allure.description("查询指定 Pod 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_pod_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 Pod，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        pod_name = public_params["pod_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_pod(
                cell_code=cell_code, sys_code=sys_code, name=pod_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 Pod 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == BUSINESS_SUCCESS_CODE:
                del_resp = ec_service.delete_pod(
                    cell_code=cell_code, sys_code=sys_code, name=pod_name,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除已存在的 Pod 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )
                time.sleep(POD_CREATE_WAIT_SECONDS)

            api_cache.set("ec_pod_created", False)

    @pytest.mark.dependency(name="pod_create", depends=["pod_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 Pod")
    @allure.description("创建 Pod 资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_pod(self, ec_service, public_params, api_cache):
        """创建 Pod，断言创建成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        pod_name = public_params["pod_name"]
        pod_image = public_params["pod_image"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_create_payload(pod_name, pod_image)
            create_resp = ec_service.create_pod(
                cell_code=cell_code, sys_code=sys_code, payload=create_payload,
            )

            assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 Pod 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )

            api_cache.set("ec_pod_created", True)
            time.sleep(POD_CREATE_WAIT_SECONDS)

    @pytest.mark.dependency(name="pod_get_after_create", depends=["pod_create"])
    @pytest.mark.order(3)
    @allure.title("创建后查询指定 Pod")
    @allure.description("创建后查询指定 Pod 验证资源存在，并缓存 Pod 对象用于后续更新")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pod_after_create(self, ec_service, public_params, api_cache):
        """创建后查询指定 Pod，缓存 Pod 对象用于 PUT 更新。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        pod_name = public_params["pod_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_pod(
                cell_code=cell_code, sys_code=sys_code, name=pod_name,
            )

            assert get_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询指定 Pod 失败, code: {get_resp.get('code')}, 响应: {get_resp}"
            )

            # 缓存 Pod 对象，用于 PUT 更新（模拟 JMX 中 JSR223 提取 podObject 的逻辑）
            pod_object = get_resp.get("data", {})
            if pod_object and "metadata" in pod_object:
                labels = pod_object.get("metadata", {}).get("labels", {})
                labels["test"] = "update"
            api_cache.set("pod_object", pod_object)

    @pytest.mark.dependency(name="pod_list_by_ns", depends=["pod_create"])
    @pytest.mark.order(4)
    @allure.title("查询 Namespace 下 Pod 列表")
    @allure.description("按标签选择器查询 Namespace 下 Pod 列表，验证包含新创建的 Pod")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_pods_by_namespace(self, ec_service, public_params):
        """查询 Namespace 下 Pod 列表，断言包含目标 Pod。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        pod_name = public_params["pod_name"]

        with AllureHelper.api_test(ec_service):
            label_selector = f"name={pod_name},kind=Pod"
            list_resp = ec_service.list_pods_by_ns(
                cell_code=cell_code, sys_code=sys_code,
                label_selector=label_selector,
            )

            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Namespace Pod 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert pod_name in resp_str, (
                f"Namespace 下 Pod 列表未找到 {pod_name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="pod_list_by_cell", depends=["pod_create"])
    @pytest.mark.order(5)
    @allure.title("查询全集群 Pod 列表")
    @allure.description("按标签选择器查询全集群 Pod 列表，验证包含新创建的 Pod")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_pods_by_cell(self, ec_service, public_params):
        """查询全集群 Pod 列表，断言包含目标 Pod。"""
        cell_code = public_params["cell_code"]
        pod_name = public_params["pod_name"]

        with AllureHelper.api_test(ec_service):
            label_selector = f"name={pod_name},kind=Pod"
            list_resp = ec_service.list_pods_by_cell(
                cell_code=cell_code, label_selector=label_selector,
            )

            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询全集群 Pod 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert pod_name in resp_str, (
                f"全集群 Pod 列表未找到 {pod_name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="pod_events", depends=["pod_create"])
    @pytest.mark.order(6)
    @allure.title("查询 Pod 事件列表")
    @allure.description("查询指定 Pod 的事件列表，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_pod_events(self, ec_service, public_params):
        """查询 Pod 事件列表，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        pod_name = public_params["pod_name"]

        with AllureHelper.api_test(ec_service):
            events_resp = ec_service.list_pod_events(
                cell_code=cell_code, sys_code=sys_code, name=pod_name,
            )

            assert events_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Pod 事件列表失败, code: {events_resp.get('code')}, 响应: {events_resp}"
            )

    @pytest.mark.dependency(name="pod_logs", depends=["pod_create"])
    @pytest.mark.order(7)
    @allure.title("查询 Pod 容器日志")
    @allure.description("查询指定 Pod 容器日志，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_pod_logs(self, ec_service, public_params):
        """查询 Pod 容器日志，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        pod_name = public_params["pod_name"]
        container_name = public_params["container_name"]

        with AllureHelper.api_test(ec_service):
            logs_resp = ec_service.get_pod_logs(
                cell_code=cell_code, sys_code=sys_code,
                name=pod_name, container=container_name,
            )

            assert logs_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Pod 日志失败, code: {logs_resp.get('code')}, 响应: {logs_resp}"
            )

    @pytest.mark.dependency(name="pod_update", depends=["pod_get_after_create"])
    @pytest.mark.order(8)
    @allure.title("PUT 全量更新 Pod")
    @allure.description("使用查询到的 Pod 对象（修改 labels）进行 PUT 全量更新，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_pod(self, ec_service, public_params, api_cache):
        """PUT 全量更新 Pod，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        pod_name = public_params["pod_name"]

        with AllureHelper.api_test(ec_service):
            pod_object = api_cache.get("pod_object")
            assert pod_object, "未找到缓存的 Pod 对象，前置用例可能失败"

            update_resp = ec_service.update_pod(
                cell_code=cell_code, sys_code=sys_code,
                name=pod_name, payload=pod_object,
            )

            assert update_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PUT 更新 Pod 失败, code: {update_resp.get('code')}, 响应: {update_resp}"
            )

    @pytest.mark.dependency(name="pod_patch", depends=["pod_update"])
    @pytest.mark.order(9)
    @allure.title("PATCH 增量更新 Pod")
    @allure.description("使用 PATCH 方法增量更新 Pod 的 labels 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_patch_pod(self, ec_service, public_params):
        """PATCH 增量更新 Pod，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        pod_name = public_params["pod_name"]

        with AllureHelper.api_test(ec_service):
            patch_payload = self._build_patch_payload()
            patch_resp = ec_service.patch_pod(
                cell_code=cell_code, sys_code=sys_code,
                name=pod_name, payload=patch_payload,
            )

            assert patch_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PATCH 增量更新 Pod 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )

    @pytest.mark.dependency(name="pod_delete", depends=["pod_patch"])
    @pytest.mark.order(10)
    @allure.title("删除 Pod")
    @allure.description("删除创建的 Pod 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_pod(self, ec_service, public_params, api_cache):
        """删除 Pod，断言删除成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        pod_name = public_params["pod_name"]

        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_pod(
                cell_code=cell_code, sys_code=sys_code, name=pod_name,
            )

            assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"删除 Pod 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_pod_created", False)
