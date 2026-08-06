"""
集群管理接口测试

转换自 JMeter 脚本: cluster-manager.jmx
测试内容：获取集群列表、查询集群详情、查询集群状态、获取控制面集群信息
"""

import allure
import pytest

from base.api.entity.elastic_compute import ClusterManagerPublicParams
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("集群管理接口")
class TestEcExtensionsClusterManager:
    """
    对应 JMeter 脚本: cluster-manager.jmx
    线程组: Thread Group - 集群管理
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
    def public_params(self, api_env) -> ClusterManagerPublicParams:
        """提取集群管理测试所需的公共参数。"""
        return ClusterManagerPublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
        )

    @pytest.mark.dependency(name="cluster_list")
    @pytest.mark.order(1)
    @allure.title("获取集群列表")
    @allure.description("获取集群列表信息并缓存首个集群 ID 供后续用例使用")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_list_clusters(self, ec_ext_service, api_cache):
        """获取集群列表，断言业务码为 2000，缓存首个集群 ID。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.list_clusters()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"获取集群列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

            # 提取首个集群 ID（对应 JMX JSONPostProcessor: $.data[0].id）
            data = response_json.get("data", [])
            if data and isinstance(data, list) and len(data) > 0:
                cluster_id = data[0].get("id")
                api_cache.set("ext_cluster_id", str(cluster_id))

    @pytest.mark.dependency(name="cluster_info", depends=["cluster_list"])
    @pytest.mark.order(2)
    @allure.title("查询指定集群详情")
    @allure.description("根据集群 ID 查询集群详情信息，验证返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_info(self, ec_ext_service, public_params, api_cache):
        """查询指定集群详情，断言业务码为2000。"""
        cluster_id = api_cache.get("ext_cluster_id") or public_params.cluster_id

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_cluster_info(
                cluster_id=cluster_id,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询集群详情失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="cluster_status", depends=["cluster_list"])
    @pytest.mark.order(3)
    @allure.title("查询集群状态")
    @allure.description("根据集群 ID 查询集群运行状态，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_cluster_status(self, ec_ext_service, public_params, api_cache):
        """查询集群状态，断言业务码为2000。"""
        cluster_id = api_cache.get("ext_cluster_id") or public_params.cluster_id

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_cluster_status(
                cluster_id=cluster_id,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询集群状态失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="cluster_controller")
    @pytest.mark.order(4)
    @allure.title("获取控制面集群信息")
    @allure.description("获取控制面集群信息，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_controller_cluster(self, ec_ext_service):
        """获取控制面集群信息，断言业务码为2000。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_controller_cluster()

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"获取控制面集群信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
