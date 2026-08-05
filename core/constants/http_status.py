"""
HTTP 状态码枚举。

本枚举集中收拢测试代码中散落的 ``HTTP_OK / HTTP_CREATED / HTTP_NOT_FOUND`` 等
本地常量，以及少量硬编码的 ``== 200 / == 201 / == 404`` 判断。

由于继承自 :class:`IntEnum`，成员可与原始 ``int`` 直接比较，无需 ``.value``::

    >>> HttpStatus.OK == 200
    True
    >>> response.status_code == HttpStatus.OK
    True

注意 HTTP 状态码（``response.status_code``、部分接口响应体中的 ``statusCode`` 字段）
与后端业务码（``response_json["code"]``）语义不同，业务码请使用
:class:`core.constants.api_codes.ApiCode`。
"""

from enum import IntEnum


class HttpStatus(IntEnum):
    """标准 HTTP 状态码。"""

    #: 请求成功
    OK = 200
    #: 资源创建成功
    CREATED = 201
    #: 请求参数错误
    BAD_REQUEST = 400
    #: 未认证
    UNAUTHORIZED = 401
    #: 无权限
    FORBIDDEN = 403
    #: 资源不存在
    NOT_FOUND = 404
    #: 资源冲突（已存在）
    CONFLICT = 409
    #: 服务端错误
    INTERNAL_SERVER_ERROR = 500


__all__ = ["HttpStatus"]
