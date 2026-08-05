"""
Partitions API 接口测试（Extensions - apikey 鉴权）

转换自 JMeter 脚本: partitions-api.jmx
测试内容：
    - 托管集群分支（testHostCluster==1）：
        1) 创建/获取/更新 ResourceQuota
        2) 预清理/创建/获取/更新/删除 LimitRange
    - 标准集群分支（testHostCluster==0）：
        1) 获取/更新 ResourceQuota（PUT 空 body）
        2) 获取/更新 LimitRange（PUT 空 body）
    - 共同分支：查询节点信息（使用 admin 头覆盖）

依赖：
    - config/env_*.yaml 需提供：apiInnerBaseUrl / clusterId / namespace /
      testHostCluster / adminUsername / adminTenantCode
"""

import allure
import pytest

from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper
from tests.api.microservices.test_microservices_ingress import public_params

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Partitions API - ResourceQuota / LimitRange 接口")
class TestEcExtensionsPartitionsApi:
    """
    对应 JMeter 脚本: partitions-api.jmx
    线程组: Thread Group - partitions-api

    JMX 通过 testHostCluster 变量分流：
        1: 托管集群 → 有 create/delete 接口
        0: 标准集群 → 只有 get/update
    最后共同分支查询节点信息（局部 HeaderManager 使用 adminUsername/adminTenantCode）。
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
    def public_params(self, api_env):
        """提取 Partitions API 测试所需的公共参数。"""
        return {
            "cluster_id": str(api_env.get("clusterId", "1")),
            "namespace": api_env.get("namespace", "test-ns"),
            "is_host_cluster": str(api_env.get("testHostCluster", "0")),
        }

    # ==================== payload 构造 helper ====================

    @staticmethod
    def _build_resource_quota_payload() -> dict:
        """构造 ResourceQuota create/update payload（对齐 JMX 原始 body）。"""
        return {
            "limitsCpu": 1,
            "limitsMemory": 1,
            "requestsCpu": 1,
            "requestsMemory": 1,
        }

    @staticmethod
    def _build_limit_range_payload() -> dict:
        """构造 LimitRange create/update payload（对齐 JMX 原始 body）。"""
        return {
            "maxCpu": 2,
            "maxMemory": 1024,
            "minCpu": 1,
            "minMemory": 256,
        }

    @staticmethod
    def _skip_if_not_host_cluster(is_host_cluster: str) -> None:
        """当前 env 非托管集群时跳过托管集群分支用例。"""
        if is_host_cluster != 1:
            pytest.skip("当前 env testHostCluster != 1，跳过托管集群分支用例")

    @staticmethod
    def _skip_if_host_cluster(is_host_cluster: str) -> None:
        """当前 env 为托管集群时跳过标准集群分支用例。"""
        if is_host_cluster == "1":
            pytest.skip("当前 env testHostCluster == 1，跳过标准集群分支用例")

    # ==================== 托管集群分支：ResourceQuota ====================

    @pytest.mark.order(1)
    @allure.title("创建 ResourceQuota（托管集群）")
    @allure.description("在托管集群下创建 ResourceQuota，断言业务码为成功；标准集群 env 跳过")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_resource_quota(self, ec_ext_service, public_params):
        """创建 ResourceQuota（仅托管集群），断言业务码为成功。"""
        self._skip_if_not_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.create_resource_quota(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
                payload=self._build_resource_quota_payload(),
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"创建 ResourceQuota 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(2)
    @allure.title("获取 ResourceQuota（托管集群）")
    @allure.description("在托管集群下查询 ResourceQuota，断言业务码为成功；标准集群 env 跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_resource_quota(self, ec_ext_service, public_params):
        """获取 ResourceQuota（仅托管集群），断言业务码为成功。"""
        self._skip_if_not_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_resource_quota(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"获取 ResourceQuota 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(3)
    @allure.title("更新 ResourceQuota（托管集群，PUT 空 body）")
    @allure.description("对齐 JMX PUT 空 body 场景更新 ResourceQuota，断言业务码为成功；标准集群 env 跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_resource_quota(self, ec_ext_service, public_params):
        """更新 ResourceQuota（托管集群），断言业务码为成功。"""
        self._skip_if_not_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.update_resource_quota(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
                payload={},
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"更新 ResourceQuota 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 托管集群分支：LimitRange 生命周期 ====================

    @pytest.mark.order(4)
    @allure.title("预清理 LimitRange（托管集群）")
    @allure.description(
        "对齐 JMX 中 defaultValues=5000 的等价预删除逻辑："
        "尝试 DELETE 已存在的 LimitRange，忽略失败结果；标准集群 env 跳过"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_pre_cleanup_limit_range(self, ec_ext_service, public_params):
        """预清理 LimitRange：调用 DELETE 忽略返回码。"""
        self._skip_if_not_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            # 忽略 code：可能不存在（首次运行），也可能成功
            ec_ext_service.delete_limit_range(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
            )

    @pytest.mark.order(5)
    @allure.title("创建 LimitRange（托管集群）")
    @allure.description("在托管集群下创建 LimitRange，断言业务码为成功；标准集群 env 跳过")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_limit_range(self, ec_ext_service, public_params):
        """创建 LimitRange（仅托管集群），断言业务码为成功。"""
        self._skip_if_not_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.create_limit_range(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
                payload=self._build_limit_range_payload(),
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"创建 LimitRange 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(6)
    @allure.title("获取 LimitRange（托管集群）")
    @allure.description("在托管集群下查询 LimitRange，断言业务码为成功；标准集群 env 跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_limit_range(self, ec_ext_service, public_params):
        """获取 LimitRange（仅托管集群），断言业务码为成功。"""
        self._skip_if_not_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_limit_range(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"获取 LimitRange 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(7)
    @allure.title("更新 LimitRange（托管集群）")
    @allure.description("在托管集群下 PUT 更新 LimitRange，断言业务码为成功；标准集群 env 跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_limit_range(self, ec_ext_service, public_params):
        """更新 LimitRange（托管集群），断言业务码为成功。"""
        self._skip_if_not_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.update_limit_range(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
                payload=self._build_limit_range_payload(),
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"更新 LimitRange 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(8)
    @allure.title("删除 LimitRange（托管集群）")
    @allure.description("在托管集群下删除 LimitRange，断言业务码为成功；标准集群 env 跳过")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_limit_range(self, ec_ext_service, public_params):
        """删除 LimitRange（托管集群），断言业务码为成功。"""
        self._skip_if_not_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.delete_limit_range(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"删除 LimitRange 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 标准集群分支：只读/更新 ====================

    @pytest.mark.order(11)
    @allure.title("获取 ResourceQuota（标准集群）")
    @allure.description("标准集群下查询 ResourceQuota，断言业务码为成功；托管集群 env 跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_resource_quota_standard(self, ec_ext_service, public_params):
        """标准集群 ResourceQuota 查询。"""
        self._skip_if_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_resource_quota(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"标准集群获取 ResourceQuota 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(12)
    @allure.title("更新 ResourceQuota（标准集群，PUT 空 body）")
    @allure.description("标准集群下 PUT 空 body 更新 ResourceQuota，断言业务码为成功；托管集群 env 跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_resource_quota_standard(self, ec_ext_service, public_params):
        """标准集群 ResourceQuota 更新（PUT 空 body 对齐 JMX）。"""
        self._skip_if_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.update_resource_quota(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
                payload={},
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"标准集群更新 ResourceQuota 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(13)
    @allure.title("获取 LimitRange（标准集群）")
    @allure.description("标准集群下查询 LimitRange，断言业务码为成功；托管集群 env 跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_limit_range_standard(self, ec_ext_service, public_params):
        """标准集群 LimitRange 查询。"""
        self._skip_if_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_limit_range(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"标准集群获取 LimitRange 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    @pytest.mark.order(14)
    @allure.title("更新 LimitRange（标准集群，PUT 空 body）")
    @allure.description("标准集群下 PUT 空 body 更新 LimitRange，断言业务码为成功；托管集群 env 跳过")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_limit_range_standard(self, ec_ext_service, public_params):
        """标准集群 LimitRange 更新（PUT 空 body 对齐 JMX）。"""
        self._skip_if_host_cluster(public_params["is_host_cluster"])

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.update_limit_range(
                cluster_id=public_params["cluster_id"],
                namespace=public_params["namespace"],
                payload={},
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"标准集群更新 LimitRange 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 共同分支：查询节点信息（admin 头覆盖）====================

    @pytest.mark.order(20)
    @allure.title("查询节点信息（admin 头覆盖）")
    @allure.description(
        "共同分支：使用 adminUsername / adminTenantCode 头覆盖调用 /v1/clusters/{clusterId}/nodes，"
        "断言业务码为成功。对齐 JMX 中局部 HeaderManager 场景。"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_partition_nodes(self, ec_ext_service, public_params):
        """查询节点信息（admin 头），断言业务码为成功。"""
        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.list_partition_nodes(
                cluster_id=public_params["cluster_id"],
                admin=True,
            )
            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询节点信息失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
