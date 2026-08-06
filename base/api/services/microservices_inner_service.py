"""
微服务 InnerAPI 服务封装（apikey 鉴权）

面向磐基（PanJi）微服务治理平台的 **内部管控接口** 客户端，与对外的 `microservices_open`
系统互补，供平台自身与内部治理链路调用。

业务域覆盖：
- ISTIO 网关内部接口：Kem（Ingress Gateway 实例）、MeshVirtualService、MeshNode 的
  内部生命周期管理与状态同步

鉴权：`apikey` 请求头（值取自 `env yaml` 的 `ms_apikey` 键，避免源码硬编码）
      + `username` / `tenantCode` 三件头（由 `_get_default_headers()` 每次请求补充）。
URL 前缀：`/ms-mesh/microservice-mesh-console/openapi/internal/...`
（**注意**：路径含 `openapi/internal` 段，但语义仍为 Inner API，与 open 系不同）。
"""
from typing import Dict, Any

from base import BaseService
from config import get_env_config
from core import get_logger
from core.config import env_manager

from base.api.entity.microservices import (
    Kem,
    MeshVS,
    MeshNode,
)

logger = get_logger(__name__)


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头。

    apikey 从 env yaml 的 ms_apikey 键读取，避免在源码中硬编码敏感凭证；
    username 复用 basicAuthUsername；tenantCode 复用 tenantCode。
    """
    env = env_manager.get_config()
    return {
        "username": env.get("basicAuthUsername"),
        "tenantCode": env.get("tenantCode"),
    }


class MicroservicesInnerService(BaseService):
    """
    微服务 InnerAPI 服务（内部管控接口）。

    - 鉴权：`apikey` 请求头（值取自 `env yaml` 的 `ms_apikey`）
      + `username` / `tenantCode` 三件头
    - URL 前缀：`/ms-mesh/microservice-mesh-console/openapi/internal/...`
    - base_url：由 fixture `api_env["apiBaseUrl"]` 提供，必传
    """

    def __init__(self, base_url: str):
        """
        初始化 Panji Microservices InnerAPI 服务

        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）

        Raises:
            ValueError: 如果 base_url 为空
        """
        if not base_url:
            raise ValueError(
                "base_url is required. "
                "Configure it in config/env_*.yaml (apiBaseUrl) "
                "and pass via fixture: api_env.get('apiBaseUrl')"
            )
        super().__init__(
            base_url=base_url,
            auth_type="api_key",
            auth_credentials={
                "api_key": get_env_config().get("ms_apikey"),
                "header_name": "apikey"
            },
        )
        logger.info(f"Initializing PanJi Microservices InnerAPI Service with base_url: {self.base_url}")

    # ==================== ISTIO网关内部接口 ====================

    def kem_check(self, check_info: Kem) -> Dict[str, Any]:
        """
        统一校验接口
        POST /ms-mesh/microservice-mesh-console/openapi/internal/kem/check
        Args:
            check_info: 校验信息，数据类参数全都需要
        """
        logger.info("KEM check")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/kem/check"
        body = [
            {
                "configs": [
                    {
                        "sysCode": check_info.sysCode,
                        "clusterName": "",
                        "channel": "",
                        "cellCode": check_info.cellCode,
                        "planeCode": check_info.planeCode,
                        "gatewayInstans": [
                            {
                                "channel": "",
                                "name": check_info.gatewayInsName
                            }
                        ],
                        "gatewayConfigs": [
                            {
                                "channel": "",
                                "name": check_info.gatewayName
                            }
                        ],
                        "virtualServices": [
                            {
                                "channel": "",
                                "name": check_info.vsName
                            }
                        ]
                    }
                ],
                "channel": "",
                "tenantCode": check_info.tenantCode,
                "userCode": check_info.username
            }
        ]
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def kem_create(self, data: Kem) -> Dict[str, Any]:
        """
        统一创建接口
        POST /ms-mesh/microservice-mesh-console/openapi/internal/kem/create
        Args:
            data: 创建数据，数据类参数全都需要
        """
        logger.info("KEM create")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/kem/create"
        body = [
            {
                "configs": [
                    {
                        "sysCode": data.sysCode,
                        "clusterName": "",
                        "channel": "",
                        "cellCode": data.cellCode,
                        "planeCode": data.planeCode,
                        "gatewayInstans": [
                            {
                                "numTrustedProxies": 0,
                                "nodes": [],
                                "directionType": "I",
                                "replicas": 1,
                                "exposeType": "NODEPORT",
                                "channel": "",
                                "name": data.gatewayInsName,
                                "maxBodySize": 1000,
                                "dualstack": "Y",
                                "portMaps": [
                                    {
                                        "protocol": "https",
                                        "port": 443,
                                        "nodePort": data.gatewayNodePort
                                    }
                                ]
                            }
                        ],
                        "gatewayConfigs": [
                            {
                                "gatewayInstanNamespace": data.sysCode,
                                "servers": [
                                    {
                                        "port": {
                                            "number": 443,
                                            "protocol": "https",
                                            "name": "https",
                                            "targetPort": 0
                                        },
                                        "hosts": [
                                            "*"
                                        ],
                                        "tls": {
                                            "mode": "SIMPLE",
                                            "credentialName": "default-token-vp69r"
                                        }
                                    }
                                ],
                                "gatewayInstanName": data.gatewayInsName,
                                "channel": "",
                                "name": data.gatewayName
                            }
                        ],
                        "virtualServices": [
                            {
                                "gateways": [
                                    {
                                        "name": data.gatewayName,
                                        "namespace": "",
                                        "wholename": "",
                                        "id": "",
                                        "selected": [
                                            "*"
                                        ]
                                    }
                                ],
                                "hosts": [],
                                "channel": "",
                                "name": data.vsName,
                                "http": [
                                    {
                                        "route": [
                                            {
                                                "destination": {
                                                    "port": {
                                                        "number": "8080"
                                                    },
                                                    "host": ""
                                                }
                                            }
                                        ],
                                        "name": "",
                                        "match": [
                                            {
                                                "port": "",
                                                "uri": {
                                                    "prefix": "/"
                                                }
                                            }
                                        ]
                                    }
                                ],
                                "tls": [],
                                "tcp": [],
                                "serviceNames": []
                            }
                        ],
                        "serviceEntries": [
                            {
                                "channel": "",
                                "name": "fwtm-api-0718",
                                "spec": {
                                    "addresses": [
                                        ""
                                    ],
                                    "hosts": [
                                        "www.baidu.com"
                                    ],
                                    "location": "MESH_EXTERNAL",
                                    "ports": [
                                        {
                                            "number": 80,
                                            "protocol": "http",
                                            "name": "http",
                                            "targetPort": 1
                                        }
                                    ],
                                    "resolution": "DNS"
                                }
                            }
                        ],
                        "clusterId": "",
                        "destinationRules": [
                            {
                                "channel": "",
                                "name": "mbgz-api-0718",
                                "spec": {
                                    "host": "mesh-gw.xt-1215.svc.cluster.local",
                                    "trafficPolicy": {
                                        "loadBalancer": {
                                            "simple": "",
                                            "consistentHash": {
                                                "httpHeaderName": "",
                                                "httpCookie": {
                                                    "path": None,
                                                    "name": None,
                                                    "ttl": None
                                                },
                                                "httpQueryParameterName": "",
                                                "useSourceIp": True
                                            }
                                        },
                                        "portLevelSettings": [
                                            {
                                                "port": {
                                                    "number": None
                                                },
                                                "loadBalancer": {
                                                    "simple": None,
                                                    "consistentHash": None
                                                },
                                                "connectionPool": {
                                                    "tcp": None,
                                                    "http": None
                                                },
                                                "tls": {
                                                    "mode": None
                                                },
                                                "outlierDetection": {
                                                    "minHealthPercent": None,
                                                    "baseEjectionTime": None,
                                                    "consecutive5xxErrors": None,
                                                    "interval": None,
                                                    "maxEjectionPercent": None
                                                }
                                            }
                                        ],
                                        "connectionPool": {
                                            "tcp": {
                                                "tcpKeepalive": {
                                                    "probes": None,
                                                    "interval": None,
                                                    "time": None
                                                },
                                                "connectTimeout": "",
                                                "maxConnections": 1
                                            },
                                            "http": {
                                                "http2MaxRequests": 1,
                                                "http1MaxPendingRequests": 1,
                                                "maxRequestsPerConnection": 1
                                            }
                                        },
                                        "tls": {
                                            "mode": ""
                                        },
                                        "outlierDetection": {
                                            "minHealthPercent": 1,
                                            "baseEjectionTime": "",
                                            "consecutive5xxErrors": 1,
                                            "interval": "",
                                            "maxEjectionPercent": 1
                                        }
                                    },
                                    "subsets": [
                                        {
                                            "name": "",
                                            "labels": {
                                                "someKey": ""
                                            },
                                            "trafficPolicy": {
                                                "loadBalancer": {
                                                    "simple": None,
                                                    "consistentHash": None
                                                },
                                                "portLevelSettings": [
                                                    None
                                                ],
                                                "connectionPool": {
                                                    "tcp": None,
                                                    "http": None
                                                },
                                                "tls": {
                                                    "mode": None
                                                },
                                                "outlierDetection": {
                                                    "minHealthPercent": None,
                                                    "baseEjectionTime": None,
                                                    "consecutive5xxErrors": None,
                                                    "interval": None,
                                                    "maxEjectionPercent": None
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ],
                        "authorizationPolicies": [
                            {
                                "channel": "",
                                "name": "hbmd-api-0718",
                                "spec": {
                                    "action": "",
                                    "selector": {
                                        "matchLabels": {
                                            "someKey": ""
                                        }
                                    },
                                    "rules": [
                                        {
                                            "from": [
                                                {
                                                    "source": None
                                                }
                                            ],
                                            "to": [
                                                {
                                                    "operation": None
                                                }
                                            ],
                                            "when": [
                                                {
                                                    "notValues": None,
                                                    "values": None,
                                                    "key": None
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ],
                "channel": "",
                "tenantCode": data.tenantCode,
                "userCode": data.username
            }
        ]
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def kem_delete(self, data: Kem) -> Dict[str, Any]:
        """
        统一删除接口
        POST /ms-mesh/microservice-mesh-console/openapi/internal/kem/delete
        Args:
            data: Kem 删除数据
        """
        logger.info("KEM delete")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/kem/delete"
        body = [
            {
                "configs": [
                    {
                        "sysCode": data.sysCode,
                        "clusterName": "",
                        "channel": "",
                        "cellCode": data.cellCode,
                        "planeCode": data.planeCode,
                        "gatewayInstans": [
                            {
                                "channel": "",
                                "name": data.gatewayInsName
                            }
                        ],
                        "gatewayConfigs": [
                            {
                                "channel": "",
                                "name": data.gatewayName
                            }
                        ],
                        "virtualServices": [
                            {
                                "channel": "",
                                "name": data.vsName
                            }
                        ],
                        "serviceEntries": [
                            {
                                "channel": "",
                                "name": "fwtm-api-0718"
                            }
                        ],
                        "destinationRules": [
                            {
                                "channel": "",
                                "name": "mbgz-api-0718"
                            }
                        ],
                        "authorizationPolicies": [
                            {
                                "channel": "",
                                "name": "hbmd-api-0718"
                            }
                        ]
                    }
                ],
                "channel": "",
                "tenantCode": data.tenantCode,
                "userCode": data.username
            }
        ]
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def batch_create_secret(self, data: Kem) -> Dict[str, Any]:
        """
        批量上传证书
        POST /ms-mesh/microservice-mesh-console/openapi/internal/kem/batchCreateSecret
        Args:
            data: Kem 证书数据
        """
        logger.info("Batch create secret")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/kem/batchCreateSecret"
        body = [
            {
                "channel": "",
                "tenantCode": data.tenantCode,
                "secrets": [
                    {
                        "gatewayInstanNamespace": data.sysCode,
                        "sysCode": data.sysCode,
                        "caFile": "",
                        "gatewayInstanName": data.gatewayInsName,
                        "keyFile": "",
                        "clusterName": "",
                        "channel": "",
                        "cellCode": data.cellCode,
                        "name": "testapi-demo",
                        "planeCode": data.planeCode,
                        "clusterId": ""
                    }
                ],
                "userCode": data.username
            }
        ]
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def list_virtual_service(self, data: MeshVS) -> Dict[str, Any]:
        """
        查询虚拟服务列表
        POST /ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/list
        Args:
            data: dataclass 查询参数
            - sysCode
            - cellCode
            - planeCode
            - clusterId
        """
        logger.info("List virtual service")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/list"
        body = {
          "sysCode": data.sysCode,
          "channel": "",
          "cellCode": data.cellCode,
          "planeCode": data.planeCode,
          "page": 1,
          "clusterId": data.clusterId,
          "keyword": "",
          "rows": 10
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def get_virtual_service(self, data: MeshVS) -> Dict[str, Any]:
        """
        精确查询虚拟服务信息
        POST /ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/getVirtualService
        Args:
            data: Dict 查询参数
        """
        logger.info("Get virtual service")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/getVirtualService"
        body = {
            "sysCode": data.sysCode,
            "channel": "",
            "cellCode": data.cellCode,
            "name": data.vsName,
            "planeCode": data.planeCode,
            "clusterId": data.clusterId
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def add_virtual_service(self, data: MeshVS) -> Dict[str, Any]:
        """
        新增虚拟服务
        POST /ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/add
        Args:
            data: Dict 虚拟服务数据
        """
        logger.info("Add virtual service")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/add"
        body = {
            "cellCode": data.cellCode,
            "channel": "",
            "clusterId": "",
            "gateways": [
                {
                    "id": "",
                    "name": data.gatewayName,
                    "namespace": "",
                    "selected": [],
                    "wholename": ""
                }
            ],
            "hosts": [],
            "http": [
                {
                    "match": [
                        {
                            "uri": {
                                "exact": "/ccc"
                            }
                        }
                    ],
                    "name": "",
                    "route": []
                }
            ],
            "name": data.vsName,
            "planeCode": data.planeCode,
            "serviceNames": [],
            "sysCode": data.sysCode,
            "tcp": [],
            "tls": []
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def delete_virtual_service(self, data: MeshVS) -> Dict[str, Any]:
        """
        删除虚拟服务
        POST /ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/delete
        Args:
            data: Dict 删除参数
        """
        logger.info("Delete virtual service")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/delete"
        body = {
            "sysCode": data.sysCode,
            "channel": "",
            "cellCode": data.cellCode,
            "name": data.vsName,
            "planeCode": data.planeCode,
            "clusterId": data.clusterId
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def get_gateway_name(self) -> Dict[str, Any]:
        """
        查询网关配置名称
        GET /ms-mesh/microservice-mesh-console/openapi/internal/v3/mesh/gateway/getGatewayName
        """
        logger.info("Get gateway name")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v3/mesh/gateway/getGatewayName"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_node(self, data: MeshNode) -> Dict[str, Any]:
        """
        查询节点列表
        POST /ms-mesh/microservice-mesh-console/openapi/internal/v1/mesh/node/list
        Args:
            data: MeshNode 查询参数
        """
        logger.info("List node")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v1/mesh/node/list"
        body = {
            "cellCode": data.cellCode,
            "planeCode": data.planeCode,
            "clusterId": data.clusterId,
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()
