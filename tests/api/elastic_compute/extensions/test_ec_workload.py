"""
Workload 生命周期接口测试（Extensions - apikey 鉴权）

转换自 JMeter 脚本: workload.jmx（默认仅覆盖 Deployment 分支）

测试内容：
    单实例：
        pre_cleanup → create → get_status → list_pods → pod_events → pod_logs
        → update → volume_mounts → hpa → update_replicas → list_hpa_after
        → patch → stop → start → restart → get_services → update_services
        → get_services_workloads → delete
    批量接口：
        batch_create → batch_update → batch_stop → batch_start → batch_delete
"""

import allure
import pytest

from base.api.entity.elastic_compute import (
    WorkloadEntity,
    WorkloadPatchEntity,
    WorkloadPublicParams,
    WorkloadServiceEntity,
)
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.reporting.allure_helper import AllureHelper

BUSINESS_SUCCESS_CODE = 2000
WORKLOAD_NOT_FOUND_CODE = 4004


@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Workload 生命周期接口")
class TestEcExtensionsWorkload:
    """
    对应 JMeter 脚本: workload.jmx
    线程组: Thread Group - workload
    """

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, api_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=api_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> WorkloadPublicParams:
        """提取 Workload 测试所需的公共参数。"""
        return WorkloadPublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            namespace=api_env.get("namespace", "test-ns"),
            cell_code=api_env.get("cellCode", "test"),
            sys_code=api_env.get("sysCode", "test-sys"),
            name="inner-test-app-nginx",
            # Deployment / StatefulSet / CloneSet / DaemonSet / CronJob / Job
            kind="Deployment",
            image=api_env.get("nginxImageName", "hpe_containers/nginx:latest"),
            replicas=1,
            app_code=api_env.get("appCodeDeploy", "test-app"),
            paas_env_code=api_env.get("paasEnvCode", "PROD"),
            paas_plane_code=api_env.get("paasPlaneCode", "test"),
            paas_tenant_code=api_env.get("paasTenantCode", "monitor-group"),
            paas_owner=api_env.get("user", "panji_probe"),
            paas_unit_code=api_env.get("paasUnitCode", "test"),
        )

    # ==================== 0) 预清理：若存在则删除 ====================

    @pytest.mark.order(0)
    @allure.title("预清理 Workload")
    @allure.description(
        "对齐 JMX 中 IfController 双分支：先 GET 查询 Workload 状态，"
        "若 code==2000 则 DELETE 预清理，若 code==4004 则表示不存在，直接跳过。"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_00_pre_cleanup_workload(self, ec_ext_service, public_params):
        """Workload 预清理：GET 若存在则 DELETE，否则跳过。"""
        with AllureHelper.api_test(ec_ext_service):
            get_resp = ec_ext_service.get_workload_status(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                kind=public_params.kind,
                name=public_params.name,
            )
            get_code = get_resp.get("code")

            if get_code == BUSINESS_SUCCESS_CODE:
                delete_resp = ec_ext_service.delete_workload(
                    cluster_id=public_params.cluster_id,
                    namespace=public_params.namespace,
                    kind=public_params.kind,
                    name=public_params.name,
                )
                assert delete_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"预清理阶段删除 Workload 失败, 响应: {delete_resp}"
                )
            elif get_code == WORKLOAD_NOT_FOUND_CODE:
                pytest.skip(f"目标 Workload 不存在 (code={WORKLOAD_NOT_FOUND_CODE})，无需预清理")
            else:
                pytest.fail(f"查询 Workload 状态返回未知业务码 code={get_code}, 响应: {get_resp}")

    # ==================== 1) 创建 Workload ====================

    @pytest.mark.order(1)
    @allure.title("创建 Workload")
    @allure.description("POST 创建 Workload，body 含 name/kind/replicas/image/appCode/labels 等字段")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_workload(self, ec_ext_service, public_params):
        """创建 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            workload = WorkloadEntity.from_public_params(public_params)
            response_json = ec_ext_service.create_workload(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                workload=workload,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 2) 查询 Workload 状态 ====================

    @pytest.mark.order(2)
    @allure.title("查询 Workload 状态")
    @allure.description("GET workload status，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_workload_status(self, ec_ext_service, public_params):
        """查询 Workload 状态，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_workload_status(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Workload 状态失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 3) 查询 Pod 实例列表（提取 podName）====================

    @pytest.mark.order(3)
    @allure.title("查询 Workload 的 Pod 实例列表")
    @allure.description("GET Pod 列表并提取 data[0].podName 到 api_cache，供后续 pod 事件/日志用例使用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_workload_pods(self, ec_ext_service, public_params, api_cache):
        """查询 Pod 列表，提取 podName 到 api_cache。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.list_workload_pods(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Pod 列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
            data = response_json.get("data") or []
            pod_name = None
            if data and isinstance(data, list):
                pod_name = data[0].get("podName") or data[0].get("name")
            api_cache.set(f"workload_pod_name_{public_params.kind}", pod_name)

    # ==================== 4) 查询 Pod 事件 ====================

    @pytest.mark.order(4)
    @allure.title("查询 Workload 的 Pod 事件列表")
    @allure.description("使用 api_cache 中的 podName 查询事件列表；若 podName 缺失则跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_pod_events(self, ec_ext_service, public_params, api_cache):
        """查询 Pod 事件列表，缺 podName 则 skip。"""
        pod_name = api_cache.get(f"workload_pod_name_{public_params.kind}")
        if not pod_name:
            pytest.skip("未提取到 podName，跳过 Pod 事件查询")

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_workload_pod_events(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                kind=public_params.kind,
                name=public_params.name,
                pod_name=pod_name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Pod 事件失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 5) 查询 Pod 日志 ====================

    @pytest.mark.order(5)
    @allure.title("查询 Workload 的 Pod 容器日志")
    @allure.description("使用 api_cache 中的 podName + 默认 container0 查询容器日志；缺 podName 则跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_pod_logs(self, ec_ext_service, public_params, api_cache):
        """查询 Pod 容器日志，缺 podName 则 skip。"""
        pod_name = api_cache.get(f"workload_pod_name_{public_params.kind}")
        if not pod_name:
            pytest.skip("未提取到 podName，跳过 Pod 日志查询")

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_workload_pod_logs(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                kind=public_params.kind,
                name=public_params.name,
                pod_name=pod_name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Pod 日志失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 6) 更新 Workload（PUT）====================

    @pytest.mark.order(6)
    @allure.title("更新指定 Workload（PUT）")
    @allure.description("PUT 全量更新 Workload，body 沿用创建 payload，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_workload(self, ec_ext_service, public_params):
        """更新 Workload（PUT），断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            workload = WorkloadEntity.from_public_params(public_params)
            response_json = ec_ext_service.update_workload(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
                workload=workload,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"更新 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 7) 查询挂载存储列表 ====================

    @pytest.mark.order(7)
    @allure.title("查询 Workload 的挂载存储列表")
    @allure.description("GET 挂载存储列表，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_volume_mounts(self, ec_ext_service, public_params):
        """查询挂载存储列表，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_workload_volume_mounts(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询挂载存储列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 8) 查询 HPA ====================

    @pytest.mark.order(8)
    @allure.title("查询 Workload 的 HPA")
    @allure.description("GET HPA 配置，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_hpa(self, ec_ext_service, public_params):
        """查询 HPA，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_workload_hpa(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 HPA 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 9) 更新副本数 ====================

    @pytest.mark.order(9)
    @allure.title("更新 Workload 副本数")
    @allure.description("POST 更新副本数为 replicas+1，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_replicas(self, ec_ext_service, public_params):
        """更新副本数，断言业务码为成功。"""
        new_replicas = int(public_params.replicas) + 1
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.update_workload_replicas(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
                replicas=new_replicas,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"更新副本数失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 10) 再次查询 HPA（对齐 JMX）====================

    @pytest.mark.order(10)
    @allure.title("再次查询 Workload 的 HPA")
    @allure.description("更新副本数后再次查询 HPA，验证接口幂等性")
    @allure.severity(allure.severity_level.MINOR)
    def test_list_hpa_after(self, ec_ext_service, public_params):
        """再次查询 HPA，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_workload_hpa(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"再次查询 HPA 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 11) 增量更新（PATCH）====================

    @pytest.mark.order(11)
    @allure.title("增量更新 Workload（PATCH）")
    @allure.description("PATCH 增量更新 Workload，body 使用 labels 局部字段")
    @allure.severity(allure.severity_level.NORMAL)
    def test_patch_workload(self, ec_ext_service, public_params):
        """PATCH 增量更新，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            patch = WorkloadPatchEntity(labels={"test": "update"})
            response_json = ec_ext_service.patch_workload(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
                patch=patch,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"增量更新 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 12) 停止 Workload ====================

    @pytest.mark.order(12)
    @allure.title("停止 Workload")
    @allure.description("POST 停止 Workload，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_stop_workload(self, ec_ext_service, public_params):
        """停止 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.stop_workload(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"停止 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 13) 启动 Workload ====================

    @pytest.mark.order(13)
    @allure.title("启动 Workload")
    @allure.description("POST 启动 Workload，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_start_workload(self, ec_ext_service, public_params):
        """启动 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.start_workload(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"启动 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 14) 重启 Workload ====================

    @pytest.mark.order(14)
    @allure.title("重启 Workload")
    @allure.description("POST 重启 Workload，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_restart_workload(self, ec_ext_service, public_params):
        """重启 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.restart_workload(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"重启 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 15) 查询 Workload 关联的 Service ====================

    @pytest.mark.order(15)
    @allure.title("查询 Workload 关联的 Service")
    @allure.description("GET Workload 关联 Service 列表，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_workload_services(self, ec_ext_service, public_params):
        """查询 Workload 关联 Service，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_workload_services(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Workload 关联 Service 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 16) 更新 Workload 关联的 Service ====================

    @pytest.mark.order(16)
    @allure.title("更新 Workload 关联的 Service")
    @allure.description("PUT 更新 Workload 关联 Service，body 含 name/type/ports 等字段")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_workload_services(self, ec_ext_service, public_params):
        """更新 Workload 关联 Service，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            services = [WorkloadServiceEntity(name=public_params.name)]
            response_json = ec_ext_service.update_workload_services(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
                services=services,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"更新 Workload 关联 Service 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 17) 通过 Service 反查 Workload ====================

    @pytest.mark.order(17)
    @allure.title("通过 Service 反查 Workload")
    @allure.description("GET /services/{name}/workloads，断言业务码为成功")
    @allure.severity(allure.severity_level.MINOR)
    def test_get_services_workloads(self, ec_ext_service, public_params):
        """通过 Service 反查 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_services_workloads(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"通过 Service 反查 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 18) 删除 Workload（单实例清理）====================

    @pytest.mark.order(18)
    @allure.title("删除 Workload（单实例清理）")
    @allure.description("DELETE 删除单实例 Workload，为后续批量测试腾出干净环境")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_workload(self, ec_ext_service, public_params):
        """删除单实例 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.delete_workload(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                kind=public_params.kind,
                name=public_params.name,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"删除 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 20-24) 批量接口 ====================

    @pytest.mark.order(20)
    @allure.title("批量创建 Workload")
    @allure.description("POST /applications/batch，body 含 workloadList，断言业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_create_workloads(self, ec_ext_service, public_params):
        """批量创建 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            workloads = [WorkloadEntity.from_public_params(public_params)]
            response_json = ec_ext_service.batch_create_workloads(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                workloads=workloads,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量创建 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(21)
    @allure.title("批量更新 Workload")
    @allure.description("PUT /applications/batch，body 含 workloadList，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_update_workloads(self, ec_ext_service, public_params):
        """批量更新 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            workloads = [WorkloadEntity.from_public_params(public_params)]
            response_json = ec_ext_service.batch_update_workloads(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                workloads=workloads,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量更新 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(22)
    @allure.title("批量停止 Workload")
    @allure.description("POST /applications/stop/batch，body 含 kind/name，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_stop_workloads(self, ec_ext_service, public_params):
        """批量停止 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            workloads = [WorkloadEntity.from_public_params(public_params)]
            response_json = ec_ext_service.batch_stop_workloads(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                workloads=workloads,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量停止 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(23)
    @allure.title("批量启动 Workload")
    @allure.description("POST /applications/start/batch，body 含 kind/name，断言业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_start_workloads(self, ec_ext_service, public_params):
        """批量启动 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            workloads = [WorkloadEntity.from_public_params(public_params)]
            response_json = ec_ext_service.batch_start_workloads(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                workloads=workloads,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量启动 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(24)
    @allure.title("批量删除 Workload")
    @allure.description("DELETE /applications/batch，body 含 kind/name，断言业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_delete_workloads(self, ec_ext_service, public_params):
        """批量删除 Workload，断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            workloads = [WorkloadEntity.from_public_params(public_params)]
            response_json = ec_ext_service.batch_delete_workloads(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                workloads=workloads,
            )
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"批量删除 Workload 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
