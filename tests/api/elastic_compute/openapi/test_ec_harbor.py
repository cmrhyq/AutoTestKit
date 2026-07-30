"""
弹性计算 OpenAPI Harbor 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/harbor.jmx
线程组: Thread Group - harbor
测试内容：Harbor 项目/成员/仓库/复制策略完整生命周期。

JMX 中通过 IfController(harbor项目已存在 / 不存在) 分成两条对称流程，
本文件合并为一条：查询 → 若存在先删除 → 创建 → 后续 CRUD → 收尾清理。
"""
import time
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper

# 业务码 / 常量（顶部集中定义，禁止方法内魔法数字）
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004
RESOURCE_ALREADY_EXISTS_CODE = 4009

# 复制策略 speed 参数（-1 表示不限速，源自 JMX 请求体）
HARBOR_REPLICATION_SPEED_UNLIMITED = -1
# harbor 分页参数
HARBOR_DEFAULT_PAGE = 1
HARBOR_DEFAULT_PAGE_SIZE = 10


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Harbor 项目/成员/仓库/复制策略生命周期接口")
class TestEcOpenapiHarbor:
    """
    对应 JMeter 脚本: harbor.jmx
    线程组: Thread Group - harbor

    执行顺序：
      1) 查询 harbor 列表 & 集群 harbor 地址
      2) 查询 project → 若存在则先删除
      3) 创建 project → 分页列表
      4) 创建/删除项目成员
      5) 查询新注册中心/新仓库
      6) 添加/查询/更新/查询详情 复制策略 → 启动执行 → 查询执行/任务/日志
      7) 查询 harbor 镜像仓库列表 / artifacts / repository 详情
      8) 收尾清理：删除复制策略 → 删除项目
    """

    TENANT = "monitor-group"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        """创建服务实例，base_url 从 yaml 显式传入（camelCase key）。"""
        service = ElasticComputeOpenService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Harbor 测试所需的公共参数。"""
        return {
            "harbor_id": api_env.get("harborId"),
            "project_name": "test-harbor-project-0001",
            "project_member_name": "ec-harbor-admin",
            "replication_policy_name": "test-replication-policiy-name001",
            "copy_harbor_access_id": "admin",
            "copy_harbor_access_secret": "******",
            "rep_name": api_env.get("copyRepName"),
        }

    # ---------------- Body helpers（对应 JMX POST/PUT 请求体，从 XML 实体还原） ----------------

    @staticmethod
    def _build_project_payload(project_name: str) -> Dict[str, Any]:
        """构造 harbor 项目创建请求体（来源 JMX 创建 harbor 项目 sampler）。"""
        return {
            "project_name": project_name,
            "metadata": {"public": "true"},
        }

    @staticmethod
    def _build_project_member_payload(username: str) -> Dict[str, Any]:
        """构造 harbor 项目成员创建请求体（来源 JMX 创建 harbor 项目成员关系 sampler）。"""
        return {
            "role_id": 1,
            "member_user": {"username": username},
        }

    @staticmethod
    def _build_replication_policy_payload(
        name: str, project_name: str, target_id: int,
    ) -> Dict[str, Any]:
        """
        构造 harbor 复制策略请求体（来源 JMX 添加/更新 harbor 复制策略 sampler）。
        """
        return {
            "name": name,
            "description": name,
            "src_registry": None,
            "dest_registry": {"id": target_id},
            "dest_namespace": project_name,
            "trigger": {"type": "manual", "trigger_settings": {"cron": ""}},
            "filters": [
                {"type": "name", "value": f"{project_name}/**"},
            ],
            "deletion": False,
            "override": True,
            "enabled": True,
            "speed": "-1",
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询 harbor 列表")
    @allure.description("查询 harbor 列表，验证返回业务成功码")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="harbor_list")
    @pytest.mark.order(1)
    def test_list_harbors(self, ec_service):
        """查询 harbor 列表。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_harbors()
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 harbor 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询所有集群 harbor 地址")
    @allure.description("查询所有集群 harbor 地址，验证返回业务成功码")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="harbor_addr_list", depends=["harbor_list"])
    @pytest.mark.order(2)
    def test_list_all_cluster_harbor_addresses(self, ec_service):
        """查询所有集群 harbor 地址。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_all_cluster_harbor_addresses()
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询集群 harbor 地址失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询 harbor 项目并清理已有项目")
    @allure.description(
        "查询指定 harbor 项目信息，若已存在则先删除以保证后续创建的幂等性"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="harbor_project_query_and_cleanup", depends=["harbor_addr_list"]
    )
    @pytest.mark.order(3)
    def test_query_project_and_cleanup(
        self, ec_service, public_params, api_cache
    ):
        """查询指定 harbor 项目，若存在则先删除。"""
        harbor_id = public_params["harbor_id"]
        project_name = public_params["project_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_harbor_project_by_id(
                harbor_id=harbor_id, project_name=project_name,
            )
            code = get_resp.get("code")

            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 harbor 项目返回异常 code: {code}, 响应: {get_resp}"
            )

            if code == BUSINESS_SUCCESS_CODE:
                del_resp = ec_service.delete_harbor_project_by_id(
                    harbor_id=harbor_id, project_name=project_name,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除已有 harbor 项目失败, code: {del_resp.get('code')}, "
                    f"响应: {del_resp}"
                )

            api_cache.set("ec_harbor_project_created", False)

    @allure.title("创建 harbor 项目")
    @allure.description("创建 harbor 项目，验证业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="harbor_project_create", depends=["harbor_project_query_and_cleanup"]
    )
    @pytest.mark.order(4)
    def test_create_project(self, ec_service, public_params, api_cache):
        """创建 harbor 项目，断言业务码成功。"""
        harbor_id = public_params["harbor_id"]
        project_name = public_params["project_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_project_payload(project_name)
            resp = ec_service.create_harbor_project_by_id(
                harbor_id=harbor_id, payload=payload,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 harbor 项目失败, code: {resp.get('code')}, 响应: {resp}"
            )
            api_cache.set("ec_harbor_project_created", True)

    @allure.title("分页查询 harbor 项目列表并获取项目 ID")
    @allure.description(
        "分页查询 harbor 项目列表，验证包含新创建项目并抽取 project_id 缓存"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_project_list", depends=["harbor_project_create"]
    )
    @pytest.mark.order(5)
    def test_list_projects(self, ec_service, public_params, api_cache):
        """分页查询 harbor 项目列表，抽取目标项目 ID。"""
        harbor_id = public_params["harbor_id"]
        project_name = public_params["project_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_harbor_projects_by_id(
                harbor_id=harbor_id,
                page=HARBOR_DEFAULT_PAGE,
                page_size=HARBOR_DEFAULT_PAGE_SIZE,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 harbor 项目列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

            data = resp.get("data") or {}
            items = data.get("list") or data.get("items") or data.get("data") or []
            target = next(
                (item for item in items if item.get("name") == project_name
                 or item.get("project_name") == project_name),
                None,
            )
            assert target is not None, (
                f"harbor 项目列表未找到 {project_name}, 响应: {resp}"
            )
            project_id = target.get("project_id") or target.get("id")
            assert project_id is not None, (
                f"harbor 项目 {project_name} 未返回 project_id, 项目详情: {target}"
            )
            api_cache.set("ec_harbor_project_id", project_id)

    @allure.title("创建 harbor 项目成员")
    @allure.description("为 harbor 项目创建成员关系，验证业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="harbor_member_create", depends=["harbor_project_list"]
    )
    @pytest.mark.order(6)
    def test_create_project_member(self, ec_service, public_params, api_cache):
        """创建项目成员，缓存 memberId。"""
        harbor_id = public_params["harbor_id"]
        member_name = public_params["project_member_name"]
        project_id = api_cache.get("ec_harbor_project_id")

        with AllureHelper.api_test(ec_service):
            payload = self._build_project_member_payload(member_name)
            resp = ec_service.create_harbor_project_member(
                harbor_id=harbor_id, project_id=project_id, payload=payload,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 harbor 项目成员失败, code: {resp.get('code')}, 响应: {resp}"
            )
            data = resp.get("data") or {}
            member_id = (
                data.get("id")
                or data.get("member_id")
                or (data.get("data") or {}).get("id")
            )
            if member_id is not None:
                api_cache.set("ec_harbor_member_id", member_id)

    @allure.title("删除 harbor 项目成员")
    @allure.description("删除 harbor 项目成员，验证业务码为成功或成员不存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_member_delete", depends=["harbor_member_create"]
    )
    @pytest.mark.order(7)
    def test_delete_project_member(self, ec_service, public_params, api_cache):
        """删除项目成员。若之前未获取到 member_id 则跳过为无效值检测。"""
        harbor_id = public_params["harbor_id"]
        project_id = api_cache.get("ec_harbor_project_id")
        member_id = api_cache.get("ec_harbor_member_id") or -1

        with AllureHelper.api_test(ec_service):
            resp = ec_service.delete_harbor_project_member(
                harbor_id=harbor_id, project_id=project_id, member_id=member_id,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"删除 harbor 项目成员返回异常 code: {code}, 响应: {resp}"
            )

    @allure.title("查询新注册中心/新仓库")
    @allure.description(
        "查询 harbor 新注册中心，验证业务码成功；作为下一阶段 target_id 的来源"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_registry_query", depends=["harbor_member_delete"]
    )
    @pytest.mark.order(8)
    def test_get_registry(self, ec_service, public_params, api_env, api_cache):
        """查询指定 targetId 的注册中心。targetId 来源于环境 harborId 复用。"""
        harbor_id = public_params["harbor_id"]
        target_id = api_env.get("harborTargetId") or harbor_id

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_harbor_registry(
                harbor_id=harbor_id, target_id=target_id,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询新注册中心返回异常 code: {code}, 响应: {resp}"
            )
            api_cache.set("ec_harbor_target_id", target_id)

    @allure.title("添加 harbor 复制策略")
    @allure.description("添加 harbor 复制策略，验证业务码为成功并缓存策略 ID")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="harbor_policy_create", depends=["harbor_registry_query"]
    )
    @pytest.mark.order(9)
    def test_create_replication_policy(
        self, ec_service, public_params, api_cache
    ):
        """添加复制策略。"""
        harbor_id = public_params["harbor_id"]
        policy_name = public_params["replication_policy_name"]
        project_name = public_params["project_name"]
        target_id = api_cache.get("ec_harbor_target_id") or harbor_id

        with AllureHelper.api_test(ec_service):
            payload = self._build_replication_policy_payload(
                name=policy_name, project_name=project_name, target_id=target_id,
            )
            resp = ec_service.create_harbor_replication_policy(
                harbor_id=harbor_id, payload=payload,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_ALREADY_EXISTS_CODE), (
                f"添加 harbor 复制策略失败, code: {code}, 响应: {resp}"
            )

    @allure.title("查询 harbor 复制/备份策略列表")
    @allure.description("按名称查询复制策略列表，验证包含目标策略并缓存策略 ID")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_policy_list", depends=["harbor_policy_create"]
    )
    @pytest.mark.order(10)
    def test_list_replication_policies(
        self, ec_service, public_params, api_cache
    ):
        """查询复制策略列表，抽取 policyId。"""
        harbor_id = public_params["harbor_id"]
        policy_name = public_params["replication_policy_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_harbor_replication_policies(
                harbor_id=harbor_id,
                name=policy_name,
                page=HARBOR_DEFAULT_PAGE,
                page_size=HARBOR_DEFAULT_PAGE_SIZE,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询复制策略列表失败, code: {resp.get('code')}, 响应: {resp}"
            )
            data = resp.get("data") or {}
            items = data.get("list") or data.get("items") or data.get("data") or []
            target = next(
                (i for i in items if i.get("name") == policy_name),
                None,
            )
            assert target is not None, (
                f"复制策略列表未找到 {policy_name}, 响应: {resp}"
            )
            policy_id = target.get("id") or target.get("policy_id")
            assert policy_id is not None, (
                f"策略 {policy_name} 未返回 policy_id: {target}"
            )
            api_cache.set("ec_harbor_policy_id", policy_id)

    @allure.title("更新 harbor 复制/备份策略")
    @allure.description("PUT 更新复制策略，验证业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_policy_update", depends=["harbor_policy_list"]
    )
    @pytest.mark.order(11)
    def test_update_replication_policy(
        self, ec_service, public_params, api_cache
    ):
        """PUT 更新策略。"""
        harbor_id = public_params["harbor_id"]
        policy_name = public_params["replication_policy_name"]
        project_name = public_params["project_name"]
        policy_id = api_cache.get("ec_harbor_policy_id")
        target_id = api_cache.get("ec_harbor_target_id") or harbor_id

        with AllureHelper.api_test(ec_service):
            payload = self._build_replication_policy_payload(
                name=policy_name, project_name=project_name, target_id=target_id,
            )
            resp = ec_service.update_harbor_replication_policy(
                harbor_id=harbor_id, policy_id=policy_id, payload=payload,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"更新 harbor 复制策略失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询 harbor 复制策略详情")
    @allure.description("GET 查询复制策略详情，验证业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_policy_detail", depends=["harbor_policy_update"]
    )
    @pytest.mark.order(12)
    def test_get_replication_policy(
        self, ec_service, public_params, api_cache
    ):
        """查询复制策略详情。"""
        harbor_id = public_params["harbor_id"]
        policy_id = api_cache.get("ec_harbor_policy_id")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_harbor_replication_policy(
                harbor_id=harbor_id, policy_id=policy_id,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 harbor 复制策略详情失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("启动 harbor 复制策略执行")
    @allure.description("触发复制策略执行，验证业务码为成功并缓存 execution_id")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="harbor_execution_start", depends=["harbor_policy_detail"]
    )
    @pytest.mark.order(13)
    def test_start_replication_execution(
        self, ec_service, public_params, api_cache
    ):
        """启动复制策略，缓存 execution_id。"""
        harbor_id = public_params["harbor_id"]
        policy_id = api_cache.get("ec_harbor_policy_id")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.start_harbor_replication_execution(
                harbor_id=harbor_id, policy_id=policy_id,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"启动 harbor 复制策略失败, code: {resp.get('code')}, 响应: {resp}"
            )
            data = resp.get("data") or {}
            execution_id = (
                data.get("id")
                or data.get("execution_id")
                or (data.get("data") or {}).get("id")
            )
            if execution_id is not None:
                api_cache.set("ec_harbor_execution_id", execution_id)
            # 等待执行任务生成（源自 JMX ConstantTimer 10s）
            time.sleep(10)

    @allure.title("查询 harbor 复制策略执行列表")
    @allure.description("查询复制策略执行列表，验证业务码为成功并回填 execution_id")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_execution_list", depends=["harbor_execution_start"]
    )
    @pytest.mark.order(14)
    def test_list_replication_executions(
        self, ec_service, public_params, api_cache
    ):
        """查询执行列表，回填 execution_id。"""
        harbor_id = public_params["harbor_id"]
        policy_id = api_cache.get("ec_harbor_policy_id")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_harbor_replication_executions(
                harbor_id=harbor_id,
                policy_id=policy_id,
                page=HARBOR_DEFAULT_PAGE,
                page_size=HARBOR_DEFAULT_PAGE_SIZE,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 harbor 策略执行列表失败, code: {resp.get('code')}, 响应: {resp}"
            )
            data = resp.get("data") or {}
            items = data.get("list") or data.get("items") or data.get("data") or []
            if items and not api_cache.get("ec_harbor_execution_id"):
                first_id = items[0].get("id") or items[0].get("execution_id")
                if first_id is not None:
                    api_cache.set("ec_harbor_execution_id", first_id)

    @allure.title("查询 harbor 复制执行任务列表")
    @allure.description("查询指定执行的任务列表，验证业务码为成功并回填 task_id")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_task_list", depends=["harbor_execution_list"]
    )
    @pytest.mark.order(15)
    def test_list_replication_tasks(
        self, ec_service, public_params, api_cache
    ):
        """查询任务列表，回填 task_id。"""
        harbor_id = public_params["harbor_id"]
        execution_id = api_cache.get("ec_harbor_execution_id")
        assert execution_id is not None, "启动执行阶段未拿到 execution_id，无法继续"

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_harbor_replication_tasks(
                harbor_id=harbor_id, execution_id=execution_id,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 harbor 复制执行任务列表失败, code: {resp.get('code')}, 响应: {resp}"
            )
            data = resp.get("data") or {}
            items = data.get("list") or data.get("items") or data.get("data") or []
            if items:
                task_id = items[0].get("id") or items[0].get("task_id")
                if task_id is not None:
                    api_cache.set("ec_harbor_task_id", task_id)

    @allure.title("查询 harbor 复制执行任务日志")
    @allure.description("查询任务日志，验证业务码为成功或任务不存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_task_log", depends=["harbor_task_list"]
    )
    @pytest.mark.order(16)
    def test_get_replication_task_log(
        self, ec_service, public_params, api_cache
    ):
        """查询任务日志。"""
        harbor_id = public_params["harbor_id"]
        execution_id = api_cache.get("ec_harbor_execution_id")
        task_id = api_cache.get("ec_harbor_task_id")
        if task_id is None:
            pytest.skip("上一阶段未取到 task_id, 跳过日志查询")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_harbor_replication_task_log(
                harbor_id=harbor_id,
                execution_id=execution_id,
                task_id=task_id,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询任务日志返回异常 code: {code}, 响应: {resp}"
            )

    @allure.title("查询 harbor 镜像仓库列表")
    @allure.description("查询指定项目下镜像仓库列表，验证业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_repo_list", depends=["harbor_task_log"]
    )
    @pytest.mark.order(17)
    def test_list_repositories(self, ec_service, public_params):
        """查询项目下镜像仓库列表。"""
        harbor_id = public_params["harbor_id"]
        project_name = public_params["project_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_harbor_repositories_by_id(
                harbor_id=harbor_id,
                project_name=project_name,
                page=HARBOR_DEFAULT_PAGE,
                page_size=HARBOR_DEFAULT_PAGE_SIZE,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 harbor 镜像仓库列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询 harbor 镜像库 artifacts")
    @allure.description(
        "查询指定项目/仓库下 artifacts 列表，验证业务码为成功或仓库为空"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_artifact_list", depends=["harbor_repo_list"]
    )
    @pytest.mark.order(18)
    def test_list_artifacts(self, ec_service, public_params):
        """查询 artifacts 列表。"""
        harbor_id = public_params["harbor_id"]
        project_name = public_params["project_name"]
        rep_name = public_params["rep_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_harbor_artifacts_by_id(
                harbor_id=harbor_id,
                project_name=project_name,
                rep_name=rep_name,
                page=HARBOR_DEFAULT_PAGE,
                page_size=HARBOR_DEFAULT_PAGE_SIZE,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 harbor artifacts 返回异常 code: {code}, 响应: {resp}"
            )

    @allure.title("获取指定的 harbor 镜像仓库")
    @allure.description("查询指定 harbor 镜像仓库详情，验证业务码为成功或仓库不存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_repo_detail", depends=["harbor_artifact_list"]
    )
    @pytest.mark.order(19)
    def test_get_repository(self, ec_service, public_params):
        """查询仓库详情。"""
        harbor_id = public_params["harbor_id"]
        project_name = public_params["project_name"]
        rep_name = public_params["rep_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_harbor_repository_by_id(
                harbor_id=harbor_id,
                project_name=project_name,
                rep_name=rep_name,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 harbor 镜像仓库返回异常 code: {code}, 响应: {resp}"
            )

    @allure.title("删除 harbor 复制策略")
    @allure.description("清理阶段：删除复制策略，验证业务码为成功或策略不存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="harbor_policy_delete", depends=["harbor_repo_detail"]
    )
    @pytest.mark.order(20)
    def test_delete_replication_policy(
        self, ec_service, public_params, api_cache
    ):
        """收尾：删除复制策略。"""
        harbor_id = public_params["harbor_id"]
        policy_id = api_cache.get("ec_harbor_policy_id")
        if policy_id is None:
            pytest.skip("未拿到 policy_id, 跳过删除")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.delete_harbor_replication_policy(
                harbor_id=harbor_id, policy_id=policy_id,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"删除复制策略返回异常 code: {code}, 响应: {resp}"
            )

    @allure.title("删除 harbor 项目")
    @allure.description("清理阶段：删除测试期间创建的 harbor 项目")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(depends=["harbor_policy_delete"])
    @pytest.mark.order(21)
    def test_delete_project(self, ec_service, public_params, api_cache):
        """收尾：删除项目。"""
        harbor_id = public_params["harbor_id"]
        project_name = public_params["project_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.delete_harbor_project_by_id(
                harbor_id=harbor_id, project_name=project_name,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"删除 harbor 项目返回异常 code: {code}, 响应: {resp}"
            )
            api_cache.set("ec_harbor_project_created", False)





