"""
弹性计算资源采集类接口测试

测试内容：全量节点、工作负载、裸金属主机、集群资源、配额、容器软件等采集接口
"""

import allure
import pytest

from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("资源采集类接口")
class TestEcExtensionsResourceCollector:

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, test_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=test_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.mark.order(1)
    @allure.title("查询全量集群节点列表")
    @allure.description("获取弹性计算所纳管集群中各个集群节点信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_nodes(self, ec_ext_service):
        """查询全量集群节点列表，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_nodes()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询节点列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(2)
    @allure.title("查询全量应用服务列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_workloads(self, ec_ext_service):
        """查询全量应用服务列表，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_workloads()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询工作负载列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(3)
    @allure.title("查询裸金属主机列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_physical_hosts(self, ec_ext_service):
        """查询裸金属主机列表，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_physical_hosts()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询裸金属主机列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(4)
    @allure.title("查询裸金属主机数量")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_physical_host_number(self, ec_ext_service):
        """查询裸金属主机数量，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_physical_host_number()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询裸金属主机数量失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(5)
    @allure.title("查询集群资源信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_cluster_resource(self, ec_ext_service):
        """查询集群资源信息，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_cluster_resource()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询集群资源信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(6)
    @allure.title("查询集群配额信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_cluster_quota(self, ec_ext_service):
        """查询集群配额信息，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_cluster_quota()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询集群配额信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(7)
    @allure.title("查询租户配额信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_tenant_quota(self, ec_ext_service):
        """查询租户配额信息，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_tenant_quota()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询租户配额信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(8)
    @allure.title("查询应用/组件系统配额信息")
    @allure.description("查询应用和组件系统级别的配额信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_system_quota(self, ec_ext_service):
        """查询应用/组件系统配额信息，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_system_quota()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询系统配额信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(9)
    @allure.title("查询容器存储软件信息")
    @allure.description("查询容器存储软件版本及配置信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_container_storage_software(self, ec_ext_service):
        """查询容器存储软件信息，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_container_storage_software()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询容器存储软件信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(10)
    @allure.title("查询容器编排软件信息")
    @allure.description("查询容器编排软件版本及配置信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_metrics_container_orchestration_software(self, ec_ext_service):
        """查询容器编排软件信息，断言业务码为 2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_metrics_container_orchestration_software()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询容器编排软件信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
