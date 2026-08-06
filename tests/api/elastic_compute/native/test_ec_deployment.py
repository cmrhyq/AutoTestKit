"""
弹性计算 Native Deployment 接口测试

转换自 JMeter 脚本: deployment.jmx
测试内容：Deployment 原生接口完成生命周期测试（查询、创建、列表、更新、删除）
"""
import json
import time

import allure
import pytest

from base.api.entity.elastic_compute import DeploymentNativePublicParams, WorkloadNativeEntity
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
@allure.story("Deployment 原生接口")
class TestEcNativeDeployment:
    """
    对应 JMeter 脚本: deployment.jmx
    线程组: Thread Group - deployment
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> DeploymentNativePublicParams:
        """提取 Deployment 测试所需的公共参数。"""
        return DeploymentNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            namespace=api_env.get("namespace", "test-admin"),
            name="native-test-app-nginx",
            paas_app_code=api_env.get("appCodeDeploy", "test-app"),
            paas_env_code=api_env.get("paasEnvCode", "ENV1"),
            paas_owner=api_env.get("user", "panji_probe"),
            paas_plane_code=api_env.get("paasPlaneCode", "PLANE1"),
            paas_tenant_code=api_env.get("paasTenantCode", "tenant-001"),
            paas_unit_code=api_env.get("paasUnitCode", "TEST"),
            image=api_env.get("nginxImageUrl", "hpe_containers/nginx:latest"),
            replicas=1,
        )

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="deploy_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 Deployment 并清理已有资源")
    @allure.description("查询指定 Deployment 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_deployment_and_cleanup(
        self, native_service, public_params, api_cache
    ):
        """查询指定 Deployment，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_deployment(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 Deployment 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_deployment(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 Deployment 失败, status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_deploy_created", False)

    @pytest.mark.dependency(name="deploy_create", depends=["deploy_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 Deployment")
    @allure.description("创建 Deployment 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_deployment(self, native_service, public_params, api_cache):
        """创建 Deployment，断言创建成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            workload = WorkloadNativeEntity(
                name=public_params.name,
                namespace=public_params.namespace,
                kind="Deployment",
                paas_app_code=public_params.paas_app_code,
                paas_env_code=public_params.paas_env_code,
                paas_owner=public_params.paas_owner,
                paas_plane_code=public_params.paas_plane_code,
                paas_tenant_code=public_params.paas_tenant_code,
                paas_unit_code=public_params.paas_unit_code,
                image=public_params.image,
                replicas=public_params.replicas,
            )
            create_resp = native_service.create_deployment(
                cluster_id=cluster_id, namespace=namespace, workload=workload,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 Deployment 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_deploy_created", True)

    @pytest.mark.dependency(name="deploy_list", depends=["deploy_create"])
    @pytest.mark.order(3)
    @allure.title("查询 Deployment 列表")
    @allure.description("按标签选择器查询 Deployment 列表，验证包含新创建的 Deployment")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_deployments(self, native_service, public_params):
        """查询 Deployment 列表，断言包含目标资源。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        time.sleep(3)

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_deployments(
                cluster_id=cluster_id,
                namespace=namespace,
                label_selector=f"paas-workload-name={name}",
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 Deployment 列表失败, status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert f'"name":"{name}"' in resp_str or name in resp_str, (
                f"Deployment 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="deploy_update", depends=["deploy_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 Deployment")
    @allure.description("全量更新 Deployment（含 replicas 与 test 标签变更），验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_deployment(self, native_service, public_params):
        """PUT 全量更新 Deployment，断言更新成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            workload = WorkloadNativeEntity(
                name=public_params.name,
                namespace=public_params.namespace,
                kind="Deployment",
                paas_app_code=public_params.paas_app_code,
                paas_env_code=public_params.paas_env_code,
                paas_owner=public_params.paas_owner,
                paas_plane_code=public_params.paas_plane_code,
                paas_tenant_code=public_params.paas_tenant_code,
                paas_unit_code=public_params.paas_unit_code,
                image=public_params.image,
                replicas=public_params.replicas + 1,
                container_port=8090,
                extra_labels={"test": "update"},
            )
            native_service.update_deployment(
                cluster_id=cluster_id, namespace=namespace, name=name, workload=workload,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 Deployment 失败, status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(name="deploy_delete", depends=["deploy_update"])
    @pytest.mark.order(5)
    @allure.title("删除 Deployment")
    @allure.description("删除创建的 Deployment 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_deployment(self, native_service, public_params, api_cache):
        """删除 Deployment，断言删除成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_deployment(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 Deployment 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_deploy_created", False)
