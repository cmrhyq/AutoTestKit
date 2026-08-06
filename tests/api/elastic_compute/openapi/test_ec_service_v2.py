"""
弹性计算 OpenAPI Service 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/ServiceV2.jmx
线程组: Thread Group - service
测试内容：Service 完整生命周期（查询/删除/创建/列表/全集群列表/PUT 更新/PATCH 增量更新/删除）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute.openapi import (
    K8sServiceEntity,
    K8sServicePatchEntity,
    K8sServicePortSpec,
    ServiceV2PublicParams,
)
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper


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

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> ServiceV2PublicParams:
        """提取 Service 测试所需的公共参数。"""
        return ServiceV2PublicParams(
            cell_code=api_env.get("cellCode", "test"),
            sys_code=api_env.get("sysCode", "test-sys"),
            svc_name="auto-test-probe-svc-test-0001",
        )

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询指定 Service")
    @allure.description("查询指定 Service 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="service_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_service_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 Service，若已存在则删除，确保测试环境干净。"""
        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_service(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=public_params.svc_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"查询 Service 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == ApiCode.SUCCESS:
                del_resp = ec_service.delete_service(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    name=public_params.svc_name,
                )
                assert del_resp.get("code") == ApiCode.SUCCESS, (
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
        with AllureHelper.api_test(ec_service):
            service = K8sServiceEntity(
                name=public_params.svc_name,
                ports=[K8sServicePortSpec(port=80, target_port=8080, name="http")],
            )
            create_resp = ec_service.create_service(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                service=service,
            )

            assert create_resp.get("code") == ApiCode.SUCCESS, (
                f"创建 Service 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )
            resp_str = json.dumps(create_resp, ensure_ascii=False)
            assert public_params.svc_name in resp_str, (
                f"创建 Service 响应中未包含资源名称 {public_params.svc_name}, 响应: {create_resp}"
            )

            api_cache.set("ec_service_v2_created", True)

    @allure.title("查询命名空间 Service 列表")
    @allure.description("查询指定命名空间下 Service 列表，验证包含新创建的 Service")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="service_list_ns", depends=["service_create"])
    @pytest.mark.order(3)
    def test_list_services_by_namespace(self, ec_service, public_params):
        """查询 Namespace 下 Service 列表，断言包含目标 Service。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_services_by_ns(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Namespace Service 列表失败, code: {list_resp.get('code')}, "
                f"响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert public_params.svc_name in resp_str, (
                f"Namespace Service 列表未找到 {public_params.svc_name}, 响应: {list_resp}"
            )

    @allure.title("查询全集群 Service 列表")
    @allure.description("查询全集群所有 Service 列表，验证包含新创建的 Service")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="service_list_cell", depends=["service_create"])
    @pytest.mark.order(4)
    def test_list_services_by_cell(self, ec_service, public_params):
        """查询全集群 Service 列表，断言包含目标 Service。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_services_by_cell(cell_code=public_params.cell_code)

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询全集群 Service 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert public_params.svc_name in resp_str, (
                f"全集群 Service 列表未找到 {public_params.svc_name}, 响应: {list_resp}"
            )

    @allure.title("PUT 全量更新 Service")
    @allure.description("使用 PUT 方法全量更新 Service 的端口配置，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="service_put", depends=["service_create"])
    @pytest.mark.order(5)
    def test_put_update_service(self, ec_service, public_params):
        """PUT 全量更新 Service，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            service = K8sServiceEntity(
                name=public_params.svc_name,
                ports=[K8sServicePortSpec(port=8080, target_port=9090, name="http-updated")],
            )
            put_resp = ec_service.update_service(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=public_params.svc_name,
                service=service,
            )

            assert put_resp.get("code") == ApiCode.SUCCESS, (
                f"PUT 更新 Service 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )

    @allure.title("PATCH 增量更新 Service")
    @allure.description("使用 PATCH 方法增量更新 Service 的 labels 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="service_patch", depends=["service_put"])
    @pytest.mark.order(6)
    def test_patch_update_service(self, ec_service, public_params):
        """PATCH 增量更新 Service，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            patch = K8sServicePatchEntity()
            patch_resp = ec_service.patch_service(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=public_params.svc_name,
                patch=patch,
            )

            assert patch_resp.get("code") == ApiCode.SUCCESS, (
                f"PATCH 增量更新 Service 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )

    @allure.title("删除 Service 资源")
    @allure.description("删除创建的 Service 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="service_delete", depends=["service_patch"])
    @pytest.mark.order(7)
    def test_delete_service(self, ec_service, public_params, api_cache):
        """删除 Service，断言删除成功并清理缓存标记。"""
        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_service(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=public_params.svc_name,
            )

            assert del_resp.get("code") == ApiCode.SUCCESS, (
                f"删除 Service 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_service_v2_created", False)
