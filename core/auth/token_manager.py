"""
多租户 Token 管理器

基于线程安全的 DataCache 实现 token 的按租户缓存与懒登录。

存储约定：
- DataCache key: "auth::token::<tenant_code>"
- value:         对应租户的 token 字符串

设计原则：
- 复用 DataCache 单例作为底层存储，天然线程安全
- 不引入新的锁、不引入 threading.local
- 一次登录、跨测试类复用；session 结束时统一清理
"""

from typing import Callable, Optional

from core.cache.data_cache import DataCache


_TOKEN_KEY_PREFIX = "auth::token::"


class TokenManager:
    """多租户 Token 管理器（基于 DataCache）。"""

    @classmethod
    def _key(cls, tenant: str) -> str:
        return f"{_TOKEN_KEY_PREFIX}{tenant}"

    @classmethod
    def get(cls, tenant: str) -> Optional[str]:
        """获取指定租户的 token，不存在返回 None。"""
        return DataCache.get_instance().get(cls._key(tenant))

    @classmethod
    def set(cls, tenant: str, token: str) -> None:
        """设置指定租户的 token（token 不能为空）。"""
        if not token:
            raise ValueError(f"token must be non-empty: tenant={tenant}")
        DataCache.get_instance().set(cls._key(tenant), token)

    @classmethod
    def has(cls, tenant: str) -> bool:
        """判断指定租户是否已存在 token。"""
        return DataCache.get_instance().has(cls._key(tenant))

    @classmethod
    def get_or_login(cls, tenant: str, login_fn: Callable[[str], str]) -> str:
        """
        返回指定租户 token；不存在时调用 login_fn 登录并写入缓存。

        Args:
            tenant: 租户 code
            login_fn: 登录回调，签名 (tenant) -> token

        Returns:
            str: 该租户的有效 token

        Raises:
            RuntimeError: login_fn 未返回有效 token
        """
        token = cls.get(tenant)
        if token:
            return token
        token = login_fn(tenant)
        if not token:
            raise RuntimeError(f"login_fn returned no token: tenant={tenant}")
        cls.set(tenant, token)
        return token

    @classmethod
    def clear(cls, tenant: Optional[str] = None) -> None:
        """
        清理 token 缓存。

        Args:
            tenant: 指定租户则只清该租户；为 None 时清所有 auth 前缀键。
        """
        cache = DataCache.get_instance()
        if tenant is None:
            for key in cache.get_all_keys():
                if key.startswith(_TOKEN_KEY_PREFIX):
                    cache.delete(key)
        else:
            cache.delete(cls._key(tenant))
