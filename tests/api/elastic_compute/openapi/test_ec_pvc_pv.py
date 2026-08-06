"""
PVC/PV/StorageClass 接口测试

测试内容：PVC 完整生命周期（查询、创建、列表、全集群列表、删除）+ PV 查询 + StorageClass 查询
"""
import json
import time

import allure
import pytest

from base.api.entity.elastic_compute.openapi import (
    K8sPvcEntity,
    PvcPvPublicParams,
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
@allure.story("PVC/PV/StorageClass 生命周期接口")
class TestEcOpenapiPvcPv:

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> PvcPvPublicParams:
        """提取 PVC/PV 测试所需的公共参数。"""
        return PvcPvPublicParams(
            cell_code=api_env.get("cellCode", "PROD_PLANE1_CELL3"),
            sys_code=api_env.get("sysCode", "test"),
            pvc_name=api_env.get("pvcName", "test-hpa-001"),
            pv_name=api_env.get("pvName", "test-pv-001"),
            storage_class_name=api_env.get("storageClassName", "test-sc-001"),
        )

    # -------------------- 测试用例 --------------------

    @pytest.mark.dependency(name="pvc_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 PVC 并清理环境")
    @allure.description("查询指定 PVC 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_pvc_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 PVC，若已存在则删除，确保测试环境干净。"""
        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_pvc(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=public_params.pvc_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"查询 PVC 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == ApiCode.SUCCESS:
                del_resp = ec_service.delete_pvc(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    name=public_params.pvc_name,
                )
                assert del_resp.get("code") == ApiCode.SUCCESS, (
                    f"删除已存在的 PVC 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_pvc_created", False)

    @pytest.mark.dependency(name="pvc_create", depends=["pvc_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 PVC")
    @allure.description("创建 PVC 资源并等待就绪，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_pvc(self, ec_service, public_params, api_cache):
        """创建 PVC，断言创建成功。"""
        with AllureHelper.api_test(ec_service):
            pvc = K8sPvcEntity(
                name=public_params.pvc_name,
                storage_class_name=public_params.storage_class_name,
            )
            create_resp = ec_service.create_pvc(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                pvc=pvc,
            )

            assert create_resp.get("code") == ApiCode.SUCCESS, (
                f"创建 PVC 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )

            api_cache.set("ec_pvc_created", True)
            time.sleep(Timing.PVC_CREATE_WAIT_SECONDS)

    @pytest.mark.dependency(name="pvc_list_ns", depends=["pvc_create"])
    @pytest.mark.order(3)
    @allure.title("查询 Namespace 下 PVC 列表")
    @allure.description("查询指定命名空间下的 PVC 列表，验证包含新创建的 PVC")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_pvc_by_namespace(self, ec_service, public_params):
        """查询 Namespace 下 PVC 列表，断言包含目标 PVC。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_pvc(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 PVC 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert public_params.pvc_name in resp_str, (
                f"Namespace 下 PVC 列表未找到 {public_params.pvc_name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="pvc_list_cell", depends=["pvc_create"])
    @pytest.mark.order(4)
    @allure.title("查询全集群 PVC 列表")
    @allure.description("查询全集群所有 PVC 列表，验证包含新创建的 PVC")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_pvc_by_cell(self, ec_service, public_params):
        """查询全集群 PVC 列表，断言包含目标 PVC。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_all_cluster_pvc(cell_code=public_params.cell_code)

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询全集群 PVC 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert public_params.pvc_name in resp_str, (
                f"全集群 PVC 列表未找到 {public_params.pvc_name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="pvc_delete", depends=["pvc_list_ns", "pvc_list_cell"])
    @pytest.mark.order(5)
    @allure.title("删除 PVC")
    @allure.description("删除创建的 PVC 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_pvc(self, ec_service, public_params, api_cache):
        """删除 PVC，断言删除成功。"""
        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_pvc(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=public_params.pvc_name,
            )

            assert del_resp.get("code") == ApiCode.SUCCESS, (
                f"删除 PVC 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_pvc_created", False)

    @pytest.mark.order(6)
    @allure.title("查询指定 PV")
    @allure.description("查询指定 PersistentVolume，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_pv(self, ec_service, public_params):
        """查询指定 PV，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_pv(
                cell_code=public_params.cell_code,
                pv_name=public_params.pv_name,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 PV 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.order(7)
    @allure.title("查询指定 StorageClass")
    @allure.description("查询指定 StorageClass，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_storage_class(self, ec_service, public_params):
        """查询指定 StorageClass，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_storage_class(
                cell_code=public_params.cell_code,
                storage_class_name=public_params.storage_class_name,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 StorageClass 失败, code: {resp.get('code')}, 响应: {resp}"
            )
