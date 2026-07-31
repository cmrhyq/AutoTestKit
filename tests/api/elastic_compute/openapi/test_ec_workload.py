"""
弹性计算 OpenAPI workload CRUD + 生命周期接口测试

转换自 JMeter 脚本: elastic-compute/openapi/workload.jmx
线程组: Thread Group - workload
测试内容：workload完整生命周期（Deployment 类型）
  创建/状态查询/批量状态查询/PUT更新/PATCH更新/滚动操作/停止/启动/重启/批量操作/Pod操作/删除
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

# 业务码 / 常量（顶部集中定义，禁止方法内魔法数字）
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004
# 固定等待时间/S
WAIT_SECONDS = 10


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("workload生命周期接口")
class TestEcOpenapiWorkload:
    """
    对应 JMeter 脚本: workload.jmx
    线程组: Thread Group - workload

    以 Deployment 为主要测试路径，覆盖完整生命周期。
    执行顺序：
      查询+清理 → 创建 → 查询状态 → 批量查询状态 → PUT更新 → PATCH更新
      → 滚动回滚 → 滚动暂停 → 滚动恢复 → 滚动重启
      → 停止 → 启动 → 重启 → 批量停止 → 批量启动 → 批量重启
      → 批量Patch → Pod执行命令 → 批量删Pod → 按标签删除
    """

    TENANT = "monitor-group"

    # 测试使用的workload Kind
    WORKLOAD_KIND = "Deployment"

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
        """提取workload测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "test"),
            "sys_code": api_env.get("sysCode", "test-sys"),
            "app_code": api_env.get("appCodeDeploy", "test-probe-deploy"),
            "kind": self.WORKLOAD_KIND,
            "workload_name": "auto-test-probe-workload-0001",
            "image": api_env.get("nginxImageUrl", "127.0.0.1:1121/tools/nginx:latest"),
        }

    # ---------------- Body helpers ----------------

    @staticmethod
    def _build_workload_create_payload(name: str, image: str) -> Dict[str, Any]:
        """构造创建 Deployment workload请求体。"""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "labels": {
                    "app": name,
                },
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": name,
                    },
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": name,
                        },
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "nginx",
                                "image": image,
                                "ports": [
                                    {"containerPort": 80},
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "128Mi",
                                    },
                                    "limits": {
                                        "cpu": "200m",
                                        "memory": "256Mi",
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        }

    @staticmethod
    def _build_workload_update_payload(name: str, image: str) -> Dict[str, Any]:
        """构造 PUT 全量更新 Deployment 请求体。"""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "labels": {
                    "app": name,
                    "version": "v2",
                },
            },
            "spec": {
                "replicas": 2,
                "selector": {
                    "matchLabels": {
                        "app": name,
                    },
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": name,
                            "version": "v2",
                        },
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "nginx",
                                "image": image,
                                "ports": [
                                    {"containerPort": 80},
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "128Mi",
                                    },
                                    "limits": {
                                        "cpu": "300m",
                                        "memory": "512Mi",
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        }

    @staticmethod
    def _build_workload_patch_payload() -> Dict[str, Any]:
        """构造 PATCH 增量更新workload请求体。"""
        return {
            "metadata": {
                "labels": {
                    "patch-label": "patched",
                },
            },
        }

    @staticmethod
    def _build_batch_status_payload(kind: str, name: str) -> Dict[str, Any]:
        """构造批量查询workload状态请求体。"""
        return {
            "workloads": [
                {"kind": kind, "name": name},
            ],
        }

    @staticmethod
    def _build_batch_rolling_payload(kind: str, name: str) -> Dict[str, Any]:
        """构造批量滚动操作请求体。"""
        return {
            "workloads": [
                {"kind": kind, "name": name},
            ],
        }

    @staticmethod
    def _build_batch_lifecycle_payload(kind: str, name: str) -> Dict[str, Any]:
        """构造批量生命周期操作（停止/启动/重启）请求体。"""
        return {
            "workloads": [
                {"kind": kind, "name": name},
            ],
        }

    @staticmethod
    def _build_batch_patch_payload(kind: str, name: str) -> Dict[str, Any]:
        """构造批量 Patch 请求体。"""
        return {
            "workloads": [
                {
                    "kind": kind,
                    "name": name,
                    "patch": {
                        "metadata": {
                            "labels": {
                                "batch-patch": "true",
                            },
                        },
                    },
                },
            ],
        }

    @staticmethod
    def _build_exec_payload(name: str) -> Dict[str, Any]:
        """构造 Pod exec 请求体。"""
        return {
            "workloadName": name,
            "containerName": "nginx",
            "command": ["echo", "hello"],
        }

    @staticmethod
    def _build_batch_delete_pods_payload(kind: str, name: str) -> Dict[str, Any]:
        """构造批量删除 Pod 请求体。"""
        return {
            "workloads": [
                {"kind": kind, "name": name},
            ],
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询并清理workload")
    @allure.description("查询指定workload确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_workload_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定workload，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_workload_status(
                cell_code=cell_code, sys_code=sys_code, kind=kind, name=name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询workload返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == BUSINESS_SUCCESS_CODE:
                del_resp = ec_service.delete_workload(
                    cell_code=cell_code, sys_code=sys_code, kind=kind, name=name,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除已存在的workload失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_workload_created", False)

    @allure.title("创建 Deployment workload")
    @allure.description("创建 Deployment 类型workload，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_create", depends=["workload_query_and_cleanup"])
    @pytest.mark.order(2)
    def test_create_workload(self, ec_service, public_params, api_cache):
        """创建workload，断言创建成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        app_code = public_params["app_code"]
        name = public_params["workload_name"]
        image = public_params["image"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_workload_create_payload(name, image)
            resp = ec_service.create_workload(
                cell_code=cell_code, sys_code=sys_code,
                app_code=app_code, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建workload失败, code: {resp.get('code')}, 响应: {resp}"
            )
            resp_str = json.dumps(resp, ensure_ascii=False)
            assert name in resp_str, (
                f"创建workload响应中未包含名称 {name}, 响应: {resp}"
            )

            api_cache.set("ec_workload_created", True)

    @allure.title("查询workload运行状态")
    @allure.description("查询已创建workload的运行状态，验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_status", depends=["workload_create"])
    @pytest.mark.order(3)
    def test_get_workload_status(self, ec_service, public_params):
        """查询workload状态，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_workload_status(
                cell_code=cell_code, sys_code=sys_code, kind=kind, name=name,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询workload状态失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("批量查询workload状态")
    @allure.description("批量查询workload运行状态，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_batch_status", depends=["workload_create"])
    @pytest.mark.order(4)
    def test_batch_query_workload_status(self, ec_service, public_params):
        """批量查询workload状态，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_batch_status_payload(kind, name)
            resp = ec_service.batch_query_workload_status(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量查询workload状态失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("PUT 全量更新workload")
    @allure.description("使用 PUT 方法全量更新 Deployment 配置，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_put", depends=["workload_create"])
    @pytest.mark.order(5)
    def test_update_workload(self, ec_service, public_params):
        """PUT 全量更新workload，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]
        image = public_params["image"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_workload_update_payload(name, image)
            resp = ec_service.update_workload(
                cell_code=cell_code, sys_code=sys_code,
                kind=kind, name=name, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PUT 更新workload失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("PATCH 增量更新workload")
    @allure.description("使用 PATCH 方法增量更新workload labels，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_patch", depends=["workload_put"])
    @pytest.mark.order(6)
    def test_patch_workload(self, ec_service, public_params):
        """PATCH 增量更新workload，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_workload_patch_payload()
            resp = ec_service.patch_workload(
                cell_code=cell_code, sys_code=sys_code,
                kind=kind, name=name, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PATCH 增量更新workload失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("滚动回滚workload")
    @allure.description("对workload执行滚动回滚操作，验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_rolling_undo", depends=["workload_patch"])
    @pytest.mark.order(7)
    def test_workload_rolling_undo(self, ec_service, public_params):
        """workload滚动回滚操作。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.workload_rolling(
                cell_code=cell_code, sys_code=sys_code,
                kind=kind, name=name, action="undo",
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"滚动回滚失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("滚动暂停workload")
    @allure.description("对workload执行滚动暂停操作，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_rolling_pause", depends=["workload_rolling_undo"])
    @pytest.mark.order(8)
    def test_workload_rolling_pause(self, ec_service, public_params):
        """workload滚动暂停操作。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.workload_rolling(
                cell_code=cell_code, sys_code=sys_code,
                kind=kind, name=name, action="pause",
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"滚动暂停失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("滚动恢复workload")
    @allure.description("对workload执行滚动恢复操作，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_rolling_resume", depends=["workload_rolling_pause"])
    @pytest.mark.order(9)
    def test_workload_rolling_resume(self, ec_service, public_params):
        """workload滚动恢复操作。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.workload_rolling(
                cell_code=cell_code, sys_code=sys_code,
                kind=kind, name=name, action="resume",
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"滚动恢复失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("滚动重启workload")
    @allure.description("对workload执行滚动重启操作，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_rolling_restart", depends=["workload_rolling_resume"])
    @pytest.mark.order(10)
    def test_workload_rolling_restart(self, ec_service, public_params):
        """workload滚动重启操作。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.workload_rolling(
                cell_code=cell_code, sys_code=sys_code,
                kind=kind, name=name, action="restart",
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"滚动重启失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("停止workload")
    @allure.description("停止指定workload，验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_stop", depends=["workload_rolling_restart"])
    @pytest.mark.order(11)
    def test_stop_workload(self, ec_service, public_params):
        """停止workload，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.stop_workload(
                cell_code=cell_code, sys_code=sys_code, kind=kind, name=name,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"停止workload失败, code: {resp.get('code')}, 响应: {resp}"
            )
        time.sleep(WAIT_SECONDS)

    @allure.title("启动workload")
    @allure.description("启动已停止的workload，验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_start", depends=["workload_stop"])
    @pytest.mark.order(12)
    def test_start_workload(self, ec_service, public_params):
        """启动workload，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.start_workload(
                cell_code=cell_code, sys_code=sys_code, kind=kind, name=name,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"启动workload失败, code: {resp.get('code')}, 响应: {resp}"
            )
        time.sleep(WAIT_SECONDS)

    @allure.title("重启workload")
    @allure.description("重启运行中的workload，验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_restart", depends=["workload_start"])
    @pytest.mark.order(13)
    def test_restart_workload(self, ec_service, public_params):
        """重启workload，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.restart_workload(
                cell_code=cell_code, sys_code=sys_code, kind=kind, name=name,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"重启workload失败, code: {resp.get('code')}, 响应: {resp}"
            )
        time.sleep(WAIT_SECONDS)

    @allure.title("批量停止workload")
    @allure.description("批量停止workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_batch_stop", depends=["workload_restart"])
    @pytest.mark.order(14)
    def test_batch_stop_workloads(self, ec_service, public_params):
        """批量停止workload，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_batch_lifecycle_payload(kind, name)
            resp = ec_service.batch_stop_workloads(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量停止workload失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("批量启动workload")
    @allure.description("批量启动workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_batch_start", depends=["workload_batch_stop"])
    @pytest.mark.order(15)
    def test_batch_start_workloads(self, ec_service, public_params):
        """批量启动workload，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_batch_lifecycle_payload(kind, name)
            resp = ec_service.batch_start_workloads(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量启动workload失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("批量重启workload")
    @allure.description("批量重启workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_batch_restart", depends=["workload_batch_start"])
    @pytest.mark.order(16)
    def test_batch_restart_workloads(self, ec_service, public_params):
        """批量重启workload，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_batch_lifecycle_payload(kind, name)
            resp = ec_service.batch_restart_workloads(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量重启workload失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("批量滚动重启workload")
    @allure.description("批量执行workload滚动重启操作，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_batch_rolling", depends=["workload_batch_restart"])
    @pytest.mark.order(17)
    def test_batch_workload_rolling(self, ec_service, public_params):
        """批量滚动重启workload，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_batch_rolling_payload(kind, name)
            resp = ec_service.batch_workload_rolling(
                cell_code=cell_code, sys_code=sys_code,
                action="restart", payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量滚动重启失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("批量增量更新workload")
    @allure.description("批量 PATCH 更新workload labels，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_batch_patch", depends=["workload_batch_rolling"])
    @pytest.mark.order(18)
    def test_batch_patch_workloads(self, ec_service, public_params):
        """批量 Patch workload，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_batch_patch_payload(kind, name)
            resp = ec_service.batch_patch_workloads(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量 Patch workload失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("Pod 执行命令")
    @allure.description("在workload Pod 中执行命令，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_exec", depends=["workload_batch_patch"])
    @pytest.mark.order(19)
    def test_workload_exec(self, ec_service, public_params):
        """在 Pod 中执行命令，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        app_code = public_params["app_code"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_exec_payload(name)
            resp = ec_service.workload_exec(
                cell_code=cell_code, sys_code=sys_code,
                app_code=app_code, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Pod 执行命令失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("批量删除workload Pod")
    @allure.description("批量删除workload关联的 Pod，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="workload_batch_del_pods", depends=["workload_exec"])
    @pytest.mark.order(20)
    def test_batch_delete_workload_pods(self, ec_service, public_params):
        """批量删除workload Pod，断言返回成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_batch_delete_pods_payload(kind, name)
            resp = ec_service.batch_delete_workload_pods(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量删除 Pod 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("按标签删除workload")
    @allure.description("按标签删除workload资源，验证删除成功并清理测试环境")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="workload_delete_by_labels", depends=["workload_batch_del_pods"])
    @pytest.mark.order(21)
    def test_delete_workload_by_labels(self, ec_service, public_params, api_cache):
        """按标签删除workload，断言删除成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            labels = f"app={name}"
            resp = ec_service.delete_workload_by_labels(
                cell_code=cell_code, sys_code=sys_code,
                kind=kind, labels=labels,
            )

            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"按标签删除workload失败, code: {resp.get('code')}, 响应: {resp}"
            )

            api_cache.set("ec_workload_created", False)
