from base.api.fixtures import *  # noqa: F401,F403

import pytest

from base.api.services.portal_open_service import (
    PanJiPortalOpenService,
    PortalUserEntity,
)


@pytest.fixture(scope="session")
def get_token(api_env, api_cache, api_logger):
    """
    多租户 Token 懒加载工厂 fixture。

    返回一个函数：get_token(tenant_code) -> token 字符串。

    行为：
    - 首次调用某租户 -> 调用 login 接口，把 token 存到：
        * cache["token::<tenant_code>"]  本 fixture 内的复用缓存
        * cache["token"]                 供 _get_default_headers() 直接读取（零 service 改动）
    - 再次调用同租户 -> 命中缓存，仅刷新 cache["token"] 为该租户 token（相当于切租户）。
    - 租户账号信息来自 config/env_{env}.yaml 的 `tenants` 字典。
    """
    service = PanJiPortalOpenService(
        base_url=api_env.get("apiBaseUrl"),
        logger=api_logger,
    )

    def _get(tenant_code: str) -> str:
        cache_key = f"token::{tenant_code}"

        if api_cache.has(cache_key):
            token = api_cache.get(cache_key)
            api_cache.set("token", token)
            return token

        creds = (api_env.get("tenants") or {}).get(tenant_code)
        assert creds, (
            f"config/env_*.yaml 的 tenants 中未配置 {tenant_code}，"
            f"请在配置文件里补充该租户的 username/password"
        )

        resp = service.get_token(PortalUserEntity(
            username=creds["username"],
            password=creds["password"],
            tenant_code=tenant_code,
        ))
        assert isinstance(resp, dict), f"[{tenant_code}] 登录响应非 dict: {resp!r}"
        assert resp.get("code") == 200, f"[{tenant_code}] 登录失败: {resp}"
        assert resp.get("data"), f"[{tenant_code}] 登录响应缺少 data: {resp}"

        token = resp["data"]
        api_cache.set(cache_key, token)
        api_cache.set("token", token)
        api_logger.info(f"[Login] {tenant_code} token cached")
        return token

    yield _get
    service.close()
