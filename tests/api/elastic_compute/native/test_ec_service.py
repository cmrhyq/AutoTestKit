"""
弹性计算 Native Service 接口测试

转换自 JMeter 脚本: service.jmx
测试内容：K8s Service 原生接口完成生命周期测试（查询、创建、列表、更新、删除）

注意：本处的 Service 指 K8s Service 资源（非本项目服务层的 service）。
"""
import json
import time

import allure
import pytest

from base.api.entity.elastic_compute import ServiceEntity, ServiceNativePublicParams
from base.api.services.elastic_compute_native_service import (
    ElasticComputeNativeService,
)
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper
from core.constants import HttpStatus, Tenant

logger = get_logger(__name__)



@pytest.mark.api
@pytest.mark.native
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Native接口")
@allure.story("Service 原生接口")
class TestEcNativeService:
    """
    对应 JMeter 脚本: service.jmx
    线程组: Thread Group - service
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> ServiceNativePublicParams:
        """提取 Service 测试所需的公共参数。"""
        return ServiceNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            namespace=api_env.get("namespace", "test-admin"),
            name="native-test-nginx-svc",
            paas_app_code=api_env.get("appCodeDeploy", "test-app-svc"),
            paas_env_code=api_env.get("paasEnvCode", "ENV1"),
            paas_owner=api_env.get("user", "panji_probe"),
            paas_plane_code=api_env.get("paasPlaneCode", "PLANE1"),
            paas_tenant_code=api_env.get("paasTenantCode", "tenant-001"),
            paas_unit_code=api_env.get("paasUnitCode", "TEST"),
            paas_workload_name="native-test-nginx-deploy",
        )

    @pytest.mark.dependency(name="svc_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 Service 并清理已有资源")
    @allure.description("查询指定 Service 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_svc_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 Service，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_service_resource(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 Service 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_service_resource(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 Service 失败, "
                    f"status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_svc_created", False)

    @pytest.mark.dependency(name="svc_create", depends=["svc_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 Service")
    @allure.description("创建 Service 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_svc(self, native_service, public_params, api_cache):
        """创建 Service，断言创建成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            svc = ServiceEntity(
                name=public_params.name,
                namespace=public_params.namespace,
                paas_app_code=public_params.paas_app_code,
                paas_env_code=public_params.paas_env_code,
                paas_owner=public_params.paas_owner,
                paas_plane_code=public_params.paas_plane_code,
                paas_tenant_code=public_params.paas_tenant_code,
                paas_unit_code=public_params.paas_unit_code,
                paas_workload_name=public_params.paas_workload_name,
            )
            create_resp = native_service.create_service_resource(
                cluster_id=cluster_id, namespace=namespace, svc=svc,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 Service 失败, 期望201, 实际: {create_http_code}, "
                f"响应: {create_resp}"
            )

            api_cache.set("ec_svc_created", True)

    @pytest.mark.dependency(name="svc_list", depends=["svc_create"])
    @pytest.mark.order(3)
    @allure.title("查询 Service 列表")
    @allure.description("查询 Service 列表，验证包含新创建的 Service")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_svc(self, native_service, public_params):
        """查询 Service 列表，断言包含目标资源。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        time.sleep(2)

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_service_resources(
                cluster_id=cluster_id, namespace=namespace,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 Service 列表失败, "
                f"status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert name in resp_str, (
                f"Service 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="svc_update", depends=["svc_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 Service")
    @allure.description("全量更新 Service（新增 test:update 标签），验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_svc(self, native_service, public_params):
        """PUT 全量更新 Service，断言更新成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            svc = ServiceEntity(
                name=public_params.name,
                namespace=public_params.namespace,
                paas_app_code=public_params.paas_app_code,
                paas_env_code=public_params.paas_env_code,
                paas_owner=public_params.paas_owner,
                paas_plane_code=public_params.paas_plane_code,
                paas_tenant_code=public_params.paas_tenant_code,
                paas_unit_code=public_params.paas_unit_code,
                paas_workload_name=public_params.paas_workload_name,
                extra_labels={"test": "update"},
            )
            native_service.update_service_resource(
                cluster_id=cluster_id, namespace=namespace, name=name, svc=svc,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 Service 失败, status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(name="svc_delete", depends=["svc_update"])
    @pytest.mark.order(5)
    @allure.title("删除 Service")
    @allure.description("删除创建的 Service 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_svc(self, native_service, public_params, api_cache):
        """删除 Service，断言删除成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_service_resource(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 Service 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_svc_created", False)
