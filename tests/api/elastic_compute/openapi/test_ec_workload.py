"""
弹性计算 OpenAPI Workload 完整生命周期接口测试

转换自 JMeter 脚本: elastic-compute/openapi/workload.jmx
线程组: Thread Group - workload
测试内容：Workload(Deployment) 完整生命周期
  查询/创建/批量查询状态/PUT更新/撤销更新/暂停更新/增量更新/恢复更新/滚动重启
  /停止/启动/重启/批量暂停/批量增量更新/批量恢复/批量撤销/批量滚动重启
  /批量停止/批量启动/批量重启/查询Pod列表/Pod exec/Pod复制文件
  /批量删除应用服务Pod/批量删除Pod实例/按标签删除
"""
import json
import time

import allure
import pytest

from base.api.entity.elastic_compute_openapi import (
    WorkloadAppPodDeleteEntity,
    WorkloadBatchPatchTargetEntity,
    WorkloadBatchTargetEntity,
    WorkloadCreateEntity,
    WorkloadExecEntity,
    WorkloadPatchEntity,
    WorkloadPodDeleteEntity,
    WorkloadPublicParams,
    WorkloadUpdateEntity,
)
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant, Timing
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Workload 生命周期接口")
class TestEcOpenapiWorkload:
    """
    对应 JMeter 脚本: workload.jmx
    线程组: Thread Group - workload
    IF 控制器: Deployment 类型

    以 Deployment 为主要测试路径，覆盖完整生命周期。
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> WorkloadPublicParams:
        """提取 Workload 测试所需的公共参数（对应 JMX 用户定义变量）。"""
        return WorkloadPublicParams(
            cell_code=api_env.get("cellCode", "TEST"),
            sys_code=api_env.get("sysCode", "test-admin"),
            app_code=api_env.get("appCode", "test-app"),
            kind="Deployment",
            name=api_env.get("workloadName", "app-nginx"),
            image=api_env.get("image", "hpe_containers/nginx:latest"),
            replicas=int(api_env.get("replicas", 1)),
            file_path_in_pod=api_env.get("filePathInPod", "/docker-entrypoint.sh"),
        )

    # ==================== 测试用例 ====================

    @pytest.mark.dependency(name="workload_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询并清理 Workload")
    @allure.description("查询指定 Workload 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_workload_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 Workload，若已存在则删除，确保测试环境干净。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("查询指定 Workload 状态"):
                get_resp = ec_service.get_workload_status(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                )
                ec_get_code = get_resp.get("code")

            with AllureHelper.step("验证响应"):
                assert ec_get_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                    f"查询 Workload 返回异常 code: {ec_get_code}, 响应: {get_resp}"
                )

            if ec_get_code == ApiCode.SUCCESS:
                with AllureHelper.step("删除已存在的 Workload"):
                    del_resp = ec_service.delete_workload(
                        cell_code=public_params.cell_code,
                        sys_code=public_params.sys_code,
                        kind=public_params.kind,
                        name=public_params.name,
                    )
                    assert del_resp.get("code") == ApiCode.SUCCESS, (
                        f"删除已存在的 Workload 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                    )

            api_cache.set("ec_workload_created", False)

    @pytest.mark.dependency(name="workload_create", depends=["workload_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 Deployment Workload")
    @allure.description("创建 Deployment 类型 Workload，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_workload(self, ec_service, public_params, api_cache):
        """创建 Workload，断言创建成功。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送创建 Workload 请求"):
                resp = ec_service.create_workload(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    app_code=public_params.app_code,
                    workload=WorkloadCreateEntity(
                        kind=public_params.kind,
                        name=public_params.name,
                        image=public_params.image,
                        replicas=public_params.replicas,
                    ),
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"创建 Workload 失败, code: {resp.get('code')}, 响应: {resp}"
                )

            api_cache.set("ec_workload_created", True)

    @pytest.mark.dependency(name="workload_batch_status", depends=["workload_create"])
    @pytest.mark.order(3)
    @allure.title("批量查询 Workload 状态列表")
    @allure.description("批量查询 Deployment 状态列表，验证响应包含目标 Workload")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_query_workload_status(self, ec_service, public_params):
        """批量查询 Workload 状态，断言返回成功且包含目标名称。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量查询状态请求"):
                resp = ec_service.batch_query_workload_status(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    applications=[
                        WorkloadBatchTargetEntity(
                            name=public_params.name, kind=public_params.kind
                        )
                    ],
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量查询 Workload 状态失败, code: {resp.get('code')}, 响应: {resp}"
                )
                resp_str = json.dumps(resp, ensure_ascii=False)
                assert public_params.name in resp_str, (
                    f"批量查询状态响应中未包含 {public_params.name}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_put", depends=["workload_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 Workload")
    @allure.description("使用 PUT 方法全量更新 Deployment 配置，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_workload(self, ec_service, public_params):
        """PUT 全量更新 Workload，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 PUT 更新请求"):
                resp = ec_service.update_workload(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                    workload=WorkloadUpdateEntity(
                        kind=public_params.kind,
                        name=public_params.name,
                        image=public_params.image,
                        replicas=public_params.replicas,
                    ),
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"PUT 更新 Workload 失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_rolling_undo", depends=["workload_put"])
    @pytest.mark.order(5)
    @allure.title("撤销更新 Workload")
    @allure.description("对 Workload 执行撤销更新操作（undo），验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_workload_rolling_undo(self, ec_service, public_params):
        """撤销更新 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送撤销更新请求"):
                resp = ec_service.workload_rolling(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                    action="undo",
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"撤销更新失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_rolling_pause", depends=["workload_rolling_undo"])
    @pytest.mark.order(6)
    @allure.title("暂停更新 Workload")
    @allure.description("对 Workload 执行暂停更新操作（pause），验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_workload_rolling_pause(self, ec_service, public_params):
        """暂停更新 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送暂停更新请求"):
                resp = ec_service.workload_rolling(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                    action="pause",
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"暂停更新失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_patch", depends=["workload_rolling_pause"])
    @pytest.mark.order(7)
    @allure.title("PATCH 增量更新 Workload")
    @allure.description("使用 PATCH 方法增量更新 Workload labels 和 spec，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_patch_workload(self, ec_service, public_params):
        """PATCH 增量更新 Workload，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 PATCH 增量更新请求"):
                resp = ec_service.patch_workload(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                    workload=WorkloadPatchEntity(
                        replicas=public_params.replicas,
                    ),
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"PATCH 增量更新失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_rolling_resume", depends=["workload_patch"])
    @pytest.mark.order(8)
    @allure.title("恢复更新 Workload")
    @allure.description("对 Workload 执行恢复更新操作（resume），验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_workload_rolling_resume(self, ec_service, public_params):
        """恢复更新 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送恢复更新请求"):
                resp = ec_service.workload_rolling(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                    action="resume",
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"恢复更新失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_rolling_restart", depends=["workload_rolling_resume"])
    @pytest.mark.order(9)
    @allure.title("滚动重启 Workload")
    @allure.description("对 Workload 执行滚动重启操作（restart），验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_workload_rolling_restart(self, ec_service, public_params):
        """滚动重启 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送滚动重启请求"):
                resp = ec_service.workload_rolling(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                    action="restart",
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"滚动重启失败, code: {resp.get('code')}, 响应: {resp}"
                )
        time.sleep(Timing.WORKLOAD_WAIT_SECONDS)

    @pytest.mark.dependency(name="workload_stop", depends=["workload_rolling_restart"])
    @pytest.mark.order(10)
    @allure.title("停止 Workload")
    @allure.description("停止指定 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_stop_workload(self, ec_service, public_params):
        """停止 Workload，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送停止请求"):
                resp = ec_service.stop_workload(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"停止 Workload 失败, code: {resp.get('code')}, 响应: {resp}"
                )
        time.sleep(Timing.WORKLOAD_WAIT_SECONDS)

    @pytest.mark.dependency(name="workload_start", depends=["workload_stop"])
    @pytest.mark.order(11)
    @allure.title("启动 Workload")
    @allure.description("启动已停止的 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_start_workload(self, ec_service, public_params):
        """启动 Workload，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送启动请求"):
                resp = ec_service.start_workload(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"启动 Workload 失败, code: {resp.get('code')}, 响应: {resp}"
                )
        time.sleep(Timing.WORKLOAD_WAIT_SECONDS)

    @pytest.mark.dependency(name="workload_restart", depends=["workload_start"])
    @pytest.mark.order(12)
    @allure.title("重启 Workload")
    @allure.description("重启运行中的 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_restart_workload(self, ec_service, public_params):
        """重启 Workload，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送重启请求"):
                resp = ec_service.restart_workload(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"重启 Workload 失败, code: {resp.get('code')}, 响应: {resp}"
                )
        time.sleep(Timing.WORKLOAD_WAIT_SECONDS)

    @pytest.mark.dependency(name="workload_batch_pause", depends=["workload_restart"])
    @pytest.mark.order(13)
    @allure.title("批量暂停更新 Workload")
    @allure.description("批量暂停更新 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_rolling_pause(self, ec_service, public_params):
        """批量暂停更新 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量暂停更新请求"):
                resp = ec_service.batch_workload_rolling(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    action="pause",
                    applications=[
                        WorkloadBatchTargetEntity(
                            name=public_params.name, kind=public_params.kind
                        )
                    ],
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量暂停更新失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_batch_patch", depends=["workload_batch_pause"])
    @pytest.mark.order(14)
    @allure.title("批量增量更新 Workload")
    @allure.description("批量 PATCH 更新 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_patch_workloads(self, ec_service, public_params):
        """批量增量更新 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量增量更新请求"):
                resp = ec_service.batch_patch_workloads(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    applications=[
                        WorkloadBatchPatchTargetEntity(
                            name=public_params.name, kind=public_params.kind
                        )
                    ],
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量增量更新失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_batch_resume", depends=["workload_batch_patch"])
    @pytest.mark.order(15)
    @allure.title("批量恢复更新 Workload")
    @allure.description("批量恢复更新 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_rolling_resume(self, ec_service, public_params):
        """批量恢复更新 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量恢复更新请求"):
                resp = ec_service.batch_workload_rolling(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    action="resume",
                    applications=[
                        WorkloadBatchTargetEntity(
                            name=public_params.name, kind=public_params.kind
                        )
                    ],
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量恢复更新失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_batch_undo", depends=["workload_batch_resume"])
    @pytest.mark.order(16)
    @allure.title("批量撤销更新 Workload")
    @allure.description("批量撤销更新 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_rolling_undo(self, ec_service, public_params):
        """批量撤销更新 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量撤销更新请求"):
                resp = ec_service.batch_workload_rolling(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    action="undo",
                    applications=[
                        WorkloadBatchTargetEntity(
                            name=public_params.name, kind=public_params.kind
                        )
                    ],
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量撤销更新失败, code: {resp.get('code')}, 响应: {resp}"
                )
        time.sleep(Timing.WORKLOAD_WAIT_SECONDS)

    @pytest.mark.dependency(name="workload_batch_rolling_restart", depends=["workload_batch_undo"])
    @pytest.mark.order(17)
    @allure.title("批量滚动重启 Workload")
    @allure.description("批量滚动重启 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_rolling_restart(self, ec_service, public_params):
        """批量滚动重启 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量滚动重启请求"):
                resp = ec_service.batch_workload_rolling(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    action="restart",
                    applications=[
                        WorkloadBatchTargetEntity(
                            name=public_params.name, kind=public_params.kind
                        )
                    ],
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量滚动重启失败, code: {resp.get('code')}, 响应: {resp}"
                )
        time.sleep(Timing.WORKLOAD_WAIT_SECONDS)

    @pytest.mark.dependency(name="workload_batch_stop", depends=["workload_batch_rolling_restart"])
    @pytest.mark.order(18)
    @allure.title("批量停止 Workload")
    @allure.description("批量停止 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_stop_workloads(self, ec_service, public_params):
        """批量停止 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量停止请求"):
                resp = ec_service.batch_stop_workloads(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    applications=[
                        WorkloadBatchTargetEntity(
                            name=public_params.name, kind=public_params.kind
                        )
                    ],
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量停止失败, code: {resp.get('code')}, 响应: {resp}"
                )
        time.sleep(Timing.WORKLOAD_WAIT_SECONDS)

    @pytest.mark.dependency(name="workload_batch_start", depends=["workload_batch_stop"])
    @pytest.mark.order(19)
    @allure.title("批量启动 Workload")
    @allure.description("批量启动 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_start_workloads(self, ec_service, public_params):
        """批量启动 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量启动请求"):
                resp = ec_service.batch_start_workloads(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    applications=[
                        WorkloadBatchTargetEntity(
                            name=public_params.name, kind=public_params.kind
                        )
                    ],
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量启动失败, code: {resp.get('code')}, 响应: {resp}"
                )
        time.sleep(Timing.WORKLOAD_WAIT_SECONDS)

    @pytest.mark.dependency(name="workload_batch_restart", depends=["workload_batch_start"])
    @pytest.mark.order(20)
    @allure.title("批量重启 Workload")
    @allure.description("批量重启 Workload，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_restart_workloads(self, ec_service, public_params):
        """批量重启 Workload。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量重启请求"):
                resp = ec_service.batch_restart_workloads(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    applications=[
                        WorkloadBatchTargetEntity(
                            name=public_params.name, kind=public_params.kind
                        )
                    ],
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量重启失败, code: {resp.get('code')}, 响应: {resp}"
                )
        time.sleep(Timing.WORKLOAD_WAIT_SECONDS)

    @pytest.mark.dependency(name="workload_query_pods", depends=["workload_batch_restart"])
    @pytest.mark.order(21)
    @allure.title("查询 Pod 实例列表")
    @allure.description("查询 Workload 关联的 Pod 实例列表，缓存 podName 供后续操作使用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_pod_list(self, ec_service, public_params, api_cache):
        """查询 Pod 列表并缓存 podName。"""
        time.sleep(Timing.POD_WAIT_SECONDS)

        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("查询 Pod 列表"):
                label_selector = (
                    f"name={public_params.name},kind={public_params.kind}"
                )
                resp = ec_service.list_pods_by_ns(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    label_selector=label_selector,
                )

            with AllureHelper.step("验证响应并提取 podName"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"查询 Pod 列表失败, code: {resp.get('code')}, 响应: {resp}"
                )
                # 提取第一个 Pod 名称
                items = resp.get("data", {}).get("items", [])
                if items:
                    pod_name = items[0].get("metadata", {}).get("name", "")
                    api_cache.set("workload_pod_name", pod_name)
                else:
                    api_cache.set("workload_pod_name", "")

    @pytest.mark.dependency(name="workload_exec", depends=["workload_query_pods"])
    @pytest.mark.order(22)
    @allure.title("Pod 执行命令")
    @allure.description("在 Workload Pod 中执行 exec 命令，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_workload_exec(self, ec_service, public_params, api_cache):
        """在 Pod 中执行命令，断言返回成功。"""
        pod_name = api_cache.get("workload_pod_name", "")

        if not pod_name:
            pytest.skip("无可用 Pod，跳过 exec 测试")

        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 Pod exec 请求"):
                resp = ec_service.workload_exec(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    app_code=public_params.app_code,
                    exec_entity=WorkloadExecEntity(pod_name=pod_name),
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"Pod exec 失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_copy_file", depends=["workload_exec"])
    @pytest.mark.order(23)
    @allure.title("Pod 复制文件")
    @allure.description("从 Workload Pod 中复制文件，验证 HTTP 200 响应")
    @allure.severity(allure.severity_level.NORMAL)
    def test_workload_copy_file(self, ec_service, public_params, api_cache):
        """从 Pod 复制文件，断言返回成功。"""
        pod_name = api_cache.get("workload_pod_name", "")

        if not pod_name:
            pytest.skip("无可用 Pod，跳过复制文件测试")

        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送 Pod 复制文件请求"):
                # 注意: copy 接口返回的是文件流，此处验证 HTTP 响应状态
                # service 方法内部 raise_for_status() 已覆盖 HTTP 状态检查
                resp = ec_service.workload_copy_file(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    name=public_params.name,
                    pod_name=pod_name,
                    container_name="container0",
                    file_path=public_params.file_path_in_pod,
                )
                # copy 接口 JMX 中只断言 HTTP 200，由 raise_for_status 覆盖
                # 若到此未抛异常则视为成功
                assert resp is not None, "Pod 复制文件返回为空"

    @pytest.mark.dependency(name="workload_batch_del_app_pods", depends=["workload_copy_file"])
    @pytest.mark.order(24)
    @allure.title("批量删除应用服务 Pod 实例")
    @allure.description("批量删除应用服务 Pod 实例，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_delete_workload_pods(self, ec_service, public_params, api_cache):
        """批量删除应用服务 Pod 实例。"""
        pod_name = api_cache.get("workload_pod_name", "")

        if not pod_name:
            pytest.skip("无可用 Pod，跳过批量删除测试")

        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量删除应用服务 Pod 请求"):
                resp = ec_service.batch_delete_workload_pods(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    pod_delete=WorkloadPodDeleteEntity(
                        pod_name=pod_name, app_code=public_params.app_code
                    ),
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量删除应用服务 Pod 失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_query_pods_2", depends=["workload_batch_del_app_pods"])
    @pytest.mark.order(25)
    @allure.title("再次查询 Pod 实例列表")
    @allure.description("再次查询 Pod 列表获取新 Pod 名称，供后续批量删除 Pod 实例使用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_pod_list_again(self, ec_service, public_params, api_cache):
        """再次查询 Pod 列表并缓存新 podName。"""
        time.sleep(Timing.POD_WAIT_SECONDS)

        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("查询 Pod 列表"):
                label_selector = (
                    f"name={public_params.name},kind={public_params.kind}"
                )
                resp = ec_service.list_pods_by_ns(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    label_selector=label_selector,
                )

            with AllureHelper.step("验证响应并提取 podName"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"查询 Pod 列表失败, code: {resp.get('code')}, 响应: {resp}"
                )
                items = resp.get("data", {}).get("items", [])
                if items:
                    pod_name = items[0].get("metadata", {}).get("name", "")
                    api_cache.set("workload_pod_name_2", pod_name)
                else:
                    api_cache.set("workload_pod_name_2", "")

    @pytest.mark.dependency(name="workload_batch_del_pods", depends=["workload_query_pods_2"])
    @pytest.mark.order(26)
    @allure.title("批量删除 Pod 实例")
    @allure.description("批量删除 Pod 实例（跨应用），验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_delete_app_pods(self, ec_service, public_params, api_cache):
        """批量删除 Pod 实例。"""
        pod_name = api_cache.get("workload_pod_name_2", "")

        if not pod_name:
            pytest.skip("无可用 Pod，跳过批量删除 Pod 实例测试")

        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送批量删除 Pod 实例请求"):
                resp = ec_service.batch_delete_app_pods(
                    pods=[
                        WorkloadAppPodDeleteEntity(
                            pod_name=pod_name,
                            app_code=public_params.app_code,
                            cell_code=public_params.cell_code,
                            sys_code=public_params.sys_code,
                        )
                    ]
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"批量删除 Pod 实例失败, code: {resp.get('code')}, 响应: {resp}"
                )

    @pytest.mark.dependency(name="workload_delete_by_labels", depends=["workload_batch_del_pods"])
    @pytest.mark.order(27)
    @allure.title("按标签删除 Workload")
    @allure.description("按标签删除 Workload 资源，验证删除成功并清理测试环境")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_workload_by_labels(self, ec_service, public_params, api_cache):
        """按标签删除 Workload，断言删除成功。"""
        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("发送按标签删除请求"):
                labels = f"name={public_params.name},kind={public_params.kind}"
                resp = ec_service.delete_workload_by_labels(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    kind=public_params.kind,
                    labels=labels,
                )

            with AllureHelper.step("验证响应"):
                assert resp.get("code") == ApiCode.SUCCESS, (
                    f"按标签删除 Workload 失败, code: {resp.get('code')}, 响应: {resp}"
                )

            api_cache.set("ec_workload_created", False)
