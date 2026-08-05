"""
弹性计算 OpenAPI 工作负载查询接口测试

转换自 JMeter 脚本: elastic-compute/openapi/workload-query.jmx
线程组: Thread Group - workload-query
测试内容：工作负载多维度查询（按 NS/Cell/Kind/Sys 组合查询、拓扑信息、资源类型列表、事件）
"""
import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("工作负载查询接口")
class TestEcOpenapiWorkloadQuery:
    """
    对应 JMeter 脚本: workload-query.jmx
    线程组: Thread Group - workload-query

    拆分为独立接口测试函数，覆盖 18 个工作负载查询维度接口。
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc
    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取工作负载查询测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "test"),
            "sys_code": api_env.get("sysCode", "test-sys"),
            "kind": api_env.get("nativeHpaWorkloadKind", "Deployment"),
            "app_code": api_env.get("appCodeDeploy", "test-probe-deploy1"),
            "workload_name": api_env.get("nativeHpaWorkloadName", "test-hpa-workload-0001"),
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("按命名空间和Kind查询工作负载")
    @allure.description("按 cell+sys+kind 维度查询工作负载列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_list_ns_kind")
    @pytest.mark.order(1)
    def test_list_workloads_by_ns_kind(self, ec_service, public_params):
        """按命名空间+Kind 查询工作负载列表。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_workloads_by_ns_kind(
                cell_code=cell_code, sys_code=sys_code, kind=kind,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"按 NS+Kind 查询工作负载失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("按命名空间查询工作负载列表")
    @allure.description("按 cell+sys 维度查询工作负载列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_list_ns")
    @pytest.mark.order(2)
    def test_list_workloads_by_ns(self, ec_service, public_params):
        """按命名空间查询工作负载列表。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_workloads_by_ns(
                cell_code=cell_code, sys_code=sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"按 NS 查询工作负载失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("按集群和Kind查询工作负载")
    @allure.description("按 cell+kind 维度查询工作负载列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_list_cell_kind")
    @pytest.mark.order(3)
    def test_list_workloads_by_cell_kind(self, ec_service, public_params):
        """按集群+Kind 查询工作负载列表。"""
        cell_code = public_params["cell_code"]
        kind = public_params["kind"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_workloads_by_cell_kind(
                cell_code=cell_code, kind=kind,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"按 Cell+Kind 查询工作负载失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("按系统和Kind查询工作负载")
    @allure.description("按 sys+kind 维度查询工作负载列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_list_sys_kind")
    @pytest.mark.order(4)
    def test_list_workloads_by_sys_kind(self, ec_service, public_params):
        """按系统+Kind 查询工作负载列表。"""
        sys_code = public_params["sys_code"]
        kind = public_params["kind"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_workloads_by_sys_kind(
                sys_code=sys_code, kind=kind,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"按 Sys+Kind 查询工作负载失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("按集群查询工作负载列表")
    @allure.description("按 cell 维度查询工作负载列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_list_cell")
    @pytest.mark.order(5)
    def test_list_workloads_by_cell(self, ec_service, public_params):
        """按集群查询工作负载列表。"""
        cell_code = public_params["cell_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_workloads_by_cell(cell_code=cell_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"按 Cell 查询工作负载失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("按系统查询工作负载列表")
    @allure.description("按 sys 维度查询工作负载列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_list_sys")
    @pytest.mark.order(6)
    def test_list_workloads_by_sys(self, ec_service, public_params):
        """按系统查询工作负载列表。"""
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_workloads_by_sys(sys_code=sys_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"按 Sys 查询工作负载失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("按Kind查询工作负载列表")
    @allure.description("按 kind 维度查询工作负载列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_list_kind")
    @pytest.mark.order(7)
    def test_list_workloads_by_kind(self, ec_service, public_params):
        """按 Kind 查询工作负载列表。"""
        kind = public_params["kind"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_workloads_by_kind(kind=kind)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"按 Kind 查询工作负载失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询所有工作负载列表")
    @allure.description("查询全平台所有工作负载列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_list_all")
    @pytest.mark.order(8)
    def test_list_all_workloads(self, ec_service):
        """查询所有工作负载列表。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_all_workloads()

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询所有工作负载失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询工作负载拓扑（含应用码）")
    @allure.description("查询指定工作负载含 appCode 的拓扑信息，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_topo_with_app")
    @pytest.mark.order(9)
    def test_get_workload_topology_with_app(self, ec_service, public_params):
        """查询工作负载拓扑信息（含 appCode）。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        app_code = public_params["app_code"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_workload_topology_with_app(
                cell_code=cell_code, sys_code=sys_code,
                app_code=app_code, name=name,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询工作负载拓扑(含app)失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询工作负载拓扑信息")
    @allure.description("查询指定工作负载拓扑信息，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_topo")
    @pytest.mark.order(10)
    def test_get_workload_topology(self, ec_service, public_params):
        """查询工作负载拓扑信息。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        name = public_params["workload_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_workload_topology(
                cell_code=cell_code, sys_code=sys_code, name=name,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询工作负载拓扑失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询命名空间拓扑（含应用码）")
    @allure.description("查询命名空间含 appCode 的拓扑信息，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_ns_topo_with_app")
    @pytest.mark.order(11)
    def test_get_ns_topology_with_app(self, ec_service, public_params):
        """查询命名空间拓扑信息（含 appCode）。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        app_code = public_params["app_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_ns_topology_with_app(
                cell_code=cell_code, sys_code=sys_code, app_code=app_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询命名空间拓扑(含app)失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询命名空间拓扑信息")
    @allure.description("查询命名空间拓扑信息，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_ns_topo")
    @pytest.mark.order(12)
    def test_get_ns_topology(self, ec_service, public_params):
        """查询命名空间拓扑信息。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_ns_topology(
                cell_code=cell_code, sys_code=sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询命名空间拓扑失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询命名空间 Deployment 列表")
    @allure.description("查询指定命名空间下 Deployment 列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_deploy_ns")
    @pytest.mark.order(13)
    def test_list_deployments_by_ns(self, ec_service, public_params):
        """查询命名空间下 Deployment 列表。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_deployments_by_ns(
                cell_code=cell_code, sys_code=sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 NS Deployment 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询集群 Deployment 列表")
    @allure.description("查询集群级 Deployment 列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_deploy_cell")
    @pytest.mark.order(14)
    def test_list_deployments_by_cell(self, ec_service, public_params):
        """查询集群下 Deployment 列表。"""
        cell_code = public_params["cell_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_deployments_by_cell(cell_code=cell_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Cell Deployment 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询命名空间 StatefulSet 列表")
    @allure.description("查询指定命名空间下 StatefulSet 列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_sts_ns")
    @pytest.mark.order(15)
    def test_list_statefulsets_by_ns(self, ec_service, public_params):
        """查询命名空间下 StatefulSet 列表。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_statefulsets_by_ns(
                cell_code=cell_code, sys_code=sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 NS StatefulSet 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询集群 StatefulSet 列表")
    @allure.description("查询集群级 StatefulSet 列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_sts_cell")
    @pytest.mark.order(16)
    def test_list_statefulsets_by_cell(self, ec_service, public_params):
        """查询集群下 StatefulSet 列表。"""
        cell_code = public_params["cell_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_statefulsets_by_cell(cell_code=cell_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Cell StatefulSet 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询命名空间 DaemonSet 列表")
    @allure.description("查询指定命名空间下 DaemonSet 列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_ds_ns")
    @pytest.mark.order(17)
    def test_list_daemonsets_by_ns(self, ec_service, public_params):
        """查询命名空间下 DaemonSet 列表。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_daemonsets_by_ns(
                cell_code=cell_code, sys_code=sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 NS DaemonSet 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询集群 DaemonSet 列表")
    @allure.description("查询集群级 DaemonSet 列表，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_ds_cell")
    @pytest.mark.order(18)
    def test_list_daemonsets_by_cell(self, ec_service, public_params):
        """查询集群下 DaemonSet 列表。"""
        cell_code = public_params["cell_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_daemonsets_by_cell(cell_code=cell_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Cell DaemonSet 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询工作负载事件列表")
    @allure.description("查询集群下工作负载相关事件，验证接口正常返回")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="wq_events")
    @pytest.mark.order(19)
    def test_list_workload_events(self, ec_service, public_params):
        """查询集群工作负载事件列表。"""
        cell_code = public_params["cell_code"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_workload_events(cell_code=cell_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询工作负载事件失败, code: {resp.get('code')}, 响应: {resp}"
            )
