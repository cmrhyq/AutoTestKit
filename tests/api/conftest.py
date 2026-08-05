"""
API 测试模块的公共 conftest。

提供多租户 Token 管理与 Service 构造工厂：

- `_login_fn`：session-scope 登录回调工厂。给定 tenant_code 返回该租户的 token。
- `service_factory`：session-scope Service 构造工厂（context manager 语法），
  内部通过 TokenManager 保证同一租户 token 只登录一次，跨测试类复用。

用法示例：

    class TestFoo:
        TENANT = Tenant.MONITOR_GROUP

        @pytest.fixture(scope="class")
        def ec_service(self, service_factory):
            with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
                yield svc

        def test_something(self, ec_service):
            ec_service.list_cluster_info_v1()

无需 `_login` fixture，无需在 Service 构造时手动传 token，
所有认证细节由 BaseService 的 `auth_type='bearer'` + `session.headers` 统一承载。
"""
from base.api.fixtures import *  # noqa: F401,F403
from contextlib import contextmanager

import pytest

from base.api.services.portal_open_service import PortalOpenService, PortalUserEntity
from core.auth import TokenManager
from core.log import get_logger
from core.constants import ApiCode, Tenant

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def _login_fn(api_env):
    """登录回调工厂：接受 tenant_code，返回该租户的 token 字符串。

    - 使用未鉴权的 PortalOpenService 调用登录接口（token=None）
    - 租户凭据从 config/env_*.yaml 的 `tenants` 字典中读取
    - 该 fixture 仅在首次访问某租户时被 TokenManager 调用
    """
    portal = PortalOpenService(
        base_url=api_env["apiBaseUrl"],
    )

    def _login(tenant: str) -> str:
        creds = (api_env.get("tenants") or {}).get(tenant)
        assert creds, (
            f"config/env_*.yaml 的 tenants 中未配置 {tenant}，"
            f"请补充该租户的 username/password"
        )
        resp = portal.get_token(PortalUserEntity(
            username=creds["username"],
            password=creds["password"],
            tenant_code=tenant,
        ))
        assert isinstance(resp, dict), f"[{tenant}] 登录响应非 dict: {resp!r}"
        assert resp.get("code") == ApiCode.LOGIN_SUCCESS, f"[{tenant}] 登录失败: {resp}"
        assert resp.get("data"), f"[{tenant}] 登录响应缺少 data: {resp}"
        logger.info(f"[Login] {tenant} success")
        return resp["data"]

    yield _login
    portal.close()


@pytest.fixture(scope="session")
def service_factory(api_env, _login_fn):
    """Service 构造工厂 + 租户绑定。

    调用签名：
        with service_factory(ServiceCls, tenant, **overrides) as svc:
            ...

    参数：
    - service_cls: Service 类（BaseService 子类），其 __init__ 需支持 `token` 关键字参数
    - tenant: 租户 code，用于从 TokenManager 获取或首次登录并缓存 token
    - overrides: 可选覆盖 `base_url`，或传递给 Service 的其他构造参数

    session teardown 时会清理 TokenManager 中的全部 token 缓存。
    """

    @contextmanager
    def _factory(service_cls, tenant: str, **overrides):
        token = TokenManager.get_or_login(tenant, _login_fn)
        service = service_cls(
            base_url=overrides.pop("base_url", api_env["apiBaseUrl"]),
            token=token,
            **overrides,
        )
        try:
            yield service
        finally:
            service.close()

    yield _factory
    TokenManager.clear()
