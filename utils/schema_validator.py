"""
API Schema 验证工具模块

该模块提供 API 响应的 JSON Schema 验证功能，用于确保 API 响应结构的正确性。
支持从文件加载 schema、内联 schema 定义以及自定义错误消息。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from jsonschema import validate, ValidationError, Draft7Validator
from jsonschema.exceptions import SchemaError

from core.log.logger import TestLogger


class SchemaValidator:
    """
    JSON Schema 验证器类
    
    提供以下功能：
    - 验证 API 响应是否符合预定义的 schema
    - 从文件或字典加载 schema
    - 详细的验证错误报告
    - 支持自定义验证规则
    
    使用示例：
        validator = SchemaValidator()
        
        # 使用内联 schema
        schema = {
            "type": "object",
            "properties": {
                "code": {"type": "integer"},
                "message": {"type": "string"},
                "data": {"type": "object"}
            },
            "required": ["code", "message"]
        }
        is_valid, errors = validator.validate(response_data, schema)
        
        # 从文件加载 schema
        is_valid, errors = validator.validate_with_file(response_data, "schemas/user_response.json")
    """
    
    def __init__(self, schema_dir: str = None):
        """
        初始化 Schema 验证器
        
        Args:
            schema_dir: Schema 文件目录路径，默认为项目根目录下的 schemas 目录
        """
        self.logger = TestLogger.get_logger(self.__class__.__name__)
        self.schema_dir = Path(schema_dir) if schema_dir else Path("schemas")
        self._schema_cache: Dict[str, dict] = {}
        
        self.logger.debug(f"SchemaValidator initialized with schema_dir: {self.schema_dir}")
    
    def validate(
        self, 
        data: Any, 
        schema: Dict[str, Any],
        raise_on_error: bool = False
    ) -> tuple[bool, List[str]]:
        """
        验证数据是否符合给定的 JSON Schema
        
        Args:
            data: 要验证的数据（通常是 API 响应的 JSON 数据）
            schema: JSON Schema 定义
            raise_on_error: 如果为 True，验证失败时抛出异常
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误消息列表)
            
        Raises:
            ValidationError: 当 raise_on_error=True 且验证失败时
            SchemaError: 当 schema 本身无效时
        """
        errors = []
        
        try:
            # 首先验证 schema 本身是否有效
            Draft7Validator.check_schema(schema)
            
            # 创建验证器并收集所有错误
            validator = Draft7Validator(schema)
            validation_errors = list(validator.iter_errors(data))
            
            if validation_errors:
                for error in validation_errors:
                    error_path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                    error_msg = f"[{error_path}] {error.message}"
                    errors.append(error_msg)
                    self.logger.warning(f"Schema validation error: {error_msg}")
                
                if raise_on_error:
                    raise ValidationError(f"Schema validation failed with {len(errors)} error(s)")
                
                return False, errors
            
            self.logger.debug("Schema validation passed")
            return True, []
            
        except SchemaError as e:
            error_msg = f"Invalid schema: {str(e)}"
            self.logger.error(error_msg)
            if raise_on_error:
                raise
            return False, [error_msg]
    
    def validate_with_file(
        self, 
        data: Any, 
        schema_file: str,
        raise_on_error: bool = False
    ) -> tuple[bool, List[str]]:
        """
        使用文件中的 schema 验证数据
        
        Args:
            data: 要验证的数据
            schema_file: Schema 文件路径（相对于 schema_dir 或绝对路径）
            raise_on_error: 如果为 True，验证失败时抛出异常
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误消息列表)
        """
        schema = self.load_schema(schema_file)
        if schema is None:
            return False, [f"Failed to load schema from file: {schema_file}"]
        
        return self.validate(data, schema, raise_on_error)
    
    def load_schema(self, schema_file: str) -> Optional[Dict[str, Any]]:
        """
        从文件加载 JSON Schema
        
        支持缓存，同一文件只加载一次。
        
        Args:
            schema_file: Schema 文件路径
            
        Returns:
            Optional[Dict[str, Any]]: Schema 字典，加载失败返回 None
        """
        # 检查缓存
        if schema_file in self._schema_cache:
            self.logger.debug(f"Loading schema from cache: {schema_file}")
            return self._schema_cache[schema_file]
        
        # 构建完整路径
        schema_path = Path(schema_file)
        if not schema_path.is_absolute():
            schema_path = self.schema_dir / schema_file
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # 缓存 schema
            self._schema_cache[schema_file] = schema
            self.logger.debug(f"Schema loaded from file: {schema_path}")
            return schema
            
        except FileNotFoundError:
            self.logger.error(f"Schema file not found: {schema_path}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in schema file {schema_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load schema from {schema_path}: {e}")
            return None
    
    def clear_cache(self) -> None:
        """清除 schema 缓存"""
        self._schema_cache.clear()
        self.logger.debug("Schema cache cleared")


# =============================================================================
# 常用 Schema 模板
# =============================================================================

class CommonSchemas:
    """
    常用的 API 响应 Schema 模板
    
    提供预定义的 schema 模板，可以直接使用或作为基础进行扩展。
    """
    
    @staticmethod
    def standard_response(data_schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        标准 API 响应 schema
        
        适用于格式为 {"code": 0, "message": "success", "data": {...}} 的响应
        
        Args:
            data_schema: data 字段的 schema，如果为 None 则允许任意类型
            
        Returns:
            Dict[str, Any]: 完整的 schema 定义
        """
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "integer",
                    "description": "响应状态码，0 表示成功"
                },
                "message": {
                    "type": "string",
                    "description": "响应消息"
                },
                "data": data_schema or {}
            },
            "required": ["code"]
        }
        return schema
    
    @staticmethod
    def paginated_response(item_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        分页响应 schema
        
        适用于包含分页信息的列表响应
        
        Args:
            item_schema: 列表项的 schema
            
        Returns:
            Dict[str, Any]: 完整的 schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "code": {"type": "integer"},
                "message": {"type": "string"},
                "data": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": item_schema
                        },
                        "total": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "总记录数"
                        },
                        "page": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "当前页码"
                        },
                        "pageSize": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "每页大小"
                        },
                        "totalPages": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "总页数"
                        }
                    },
                    "required": ["items", "total"]
                }
            },
            "required": ["code", "data"]
        }
    
    @staticmethod
    def error_response() -> Dict[str, Any]:
        """
        错误响应 schema
        
        Returns:
            Dict[str, Any]: 错误响应的 schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "integer",
                    "description": "错误码，非 0 值"
                },
                "message": {
                    "type": "string",
                    "description": "错误消息"
                },
                "error": {
                    "type": "string",
                    "description": "详细错误信息"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "错误发生时间"
                }
            },
            "required": ["code", "message"]
        }
    
    @staticmethod
    def user_schema() -> Dict[str, Any]:
        """
        用户对象 schema 示例
        
        Returns:
            Dict[str, Any]: 用户对象的 schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "id": {
                    "type": ["integer", "string"],
                    "description": "用户 ID"
                },
                "username": {
                    "type": "string",
                    "minLength": 1,
                    "description": "用户名"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "邮箱地址"
                },
                "phone": {
                    "type": ["string", "null"],
                    "description": "手机号"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending"],
                    "description": "用户状态"
                },
                "createdAt": {
                    "type": "string",
                    "format": "date-time",
                    "description": "创建时间"
                },
                "updatedAt": {
                    "type": "string",
                    "format": "date-time",
                    "description": "更新时间"
                }
            },
            "required": ["id", "username"]
        }


# =============================================================================
# 便捷函数
# =============================================================================

# 全局验证器实例
_default_validator: Optional[SchemaValidator] = None


def get_validator(schema_dir: str = None) -> SchemaValidator:
    """
    获取 Schema 验证器实例
    
    Args:
        schema_dir: Schema 文件目录路径
        
    Returns:
        SchemaValidator: 验证器实例
    """
    global _default_validator
    if _default_validator is None or schema_dir is not None:
        _default_validator = SchemaValidator(schema_dir)
    return _default_validator


def validate_response(
    data: Any, 
    schema: Dict[str, Any],
    raise_on_error: bool = False
) -> tuple[bool, List[str]]:
    """
    验证 API 响应数据的便捷函数
    
    Args:
        data: 要验证的数据
        schema: JSON Schema 定义
        raise_on_error: 如果为 True，验证失败时抛出异常
        
    Returns:
        tuple[bool, List[str]]: (是否有效, 错误消息列表)
        
    使用示例：
        from utils.schema_validator import validate_response, CommonSchemas
        
        # 验证标准响应
        is_valid, errors = validate_response(
            response.json(),
            CommonSchemas.standard_response()
        )
        assert is_valid, f"Schema validation failed: {errors}"
    """
    return get_validator().validate(data, schema, raise_on_error)

