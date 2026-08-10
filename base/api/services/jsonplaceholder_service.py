"""
JSONPlaceholder API 服务类

该模块封装了 JSONPlaceholder 公共 API 的接口调用。
JSONPlaceholder 是一个免费的在线 REST API，用于测试和原型开发。

API 文档: https://jsonplaceholder.typicode.com/

Requirements: 10.3
"""

from typing import Optional, List, Dict, Any
from base.api.services.base_service import BaseService
from core.log import get_logger

logger = get_logger(__name__)


class JSONPlaceholderService(BaseService):
    """
    JSONPlaceholder API 服务类
    
    提供对 JSONPlaceholder API 的封装，包括：
    - 用户管理（Users）
    - 文章管理（Posts）
    - 评论管理（Comments）
    - 待办事项（Todos）
    
    使用示例：
        service = JSONPlaceholderService()
        users = service.get_all_users()
        user = service.get_user_by_id(1)
        new_post = service.create_post(user_id=1, title="Test", body="Content")
    """
    
    def __init__(self, base_url: str = None):
        """
        初始化 JSONPlaceholder 服务
        
        Args:
            base_url: API 基础 URL，默认使用 JSONPlaceholder 官方地址
        """
        super().__init__(
            base_url=base_url,
        )
        logger.info(f"Initialized JSONPlaceholderService with URL: {self.base_url}")
    
    # ==================== 用户相关接口 ====================
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        获取所有用户列表
        
        Returns:
            List[Dict]: 用户列表
        """
        logger.info("Fetching all users")
        response = self.get("/users")
        return response.json()
    
    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """
        根据 ID 获取用户信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            Dict: 用户信息
        """
        logger.info(f"Fetching user with ID: {user_id}")
        response = self.get(f"/users/{user_id}")
        return response.json()
    
    def get_user_posts(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取指定用户的所有文章
        
        Args:
            user_id: 用户 ID
            
        Returns:
            List[Dict]: 文章列表
        """
        logger.info(f"Fetching posts for user ID: {user_id}")
        response = self.get(f"/users/{user_id}/posts")
        return response.json()
    
    def get_user_todos(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取指定用户的所有待办事项
        
        Args:
            user_id: 用户 ID
            
        Returns:
            List[Dict]: 待办事项列表
        """
        logger.info(f"Fetching todos for user ID: {user_id}")
        response = self.get(f"/users/{user_id}/todos")
        return response.json()
    
    # ==================== 文章相关接口 ====================
    
    def get_all_posts(self) -> List[Dict[str, Any]]:
        """
        获取所有文章列表
        
        Returns:
            List[Dict]: 文章列表
        """
        logger.info("Fetching all posts")
        response = self.get("/posts")
        return response.json()
    
    def get_post_by_id(self, post_id: int) -> Dict[str, Any]:
        """
        根据 ID 获取文章详情
        
        Args:
            post_id: 文章 ID
            
        Returns:
            Dict: 文章详情
        """
        logger.info(f"Fetching post with ID: {post_id}")
        response = self.get(f"/posts/{post_id}")
        return response.json()
    
    def create_post(
        self,
        user_id: int,
        title: str,
        body: str
    ) -> Dict[str, Any]:
        """
        创建新文章
        
        Args:
            user_id: 用户 ID
            title: 文章标题
            body: 文章内容
            
        Returns:
            Dict: 创建的文章信息（包含生成的 ID）
        """
        logger.info(f"Creating post for user ID: {user_id}")
        payload = {
            "userId": user_id,
            "title": title,
            "body": body
        }
        response = self.post("/posts", json=payload)
        return response.json()
    
    def update_post(
        self,
        post_id: int,
        user_id: Optional[int] = None,
        title: Optional[str] = None,
        body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新文章（完整更新）
        
        Args:
            post_id: 文章 ID
            user_id: 用户 ID（可选）
            title: 文章标题（可选）
            body: 文章内容（可选）
            
        Returns:
            Dict: 更新后的文章信息
        """
        logger.info(f"Updating post with ID: {post_id}")
        payload = {}
        if user_id is not None:
            payload["userId"] = user_id
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        
        response = self.put(f"/posts/{post_id}", json=payload)
        return response.json()
    
    def patch_post(
        self,
        post_id: int,
        **fields
    ) -> Dict[str, Any]:
        """
        部分更新文章
        
        Args:
            post_id: 文章 ID
            **fields: 要更新的字段
            
        Returns:
            Dict: 更新后的文章信息
        """
        logger.info(f"Patching post with ID: {post_id}")
        response = self.patch(f"/posts/{post_id}", json=fields)
        return response.json()
    
    def delete_post(self, post_id: int) -> bool:
        """
        删除文章
        
        Args:
            post_id: 文章 ID
            
        Returns:
            bool: 删除是否成功
        """
        logger.info(f"Deleting post with ID: {post_id}")
        response = self.delete(f"/posts/{post_id}")
        return response.status_code == 200
    
    def get_post_comments(self, post_id: int) -> List[Dict[str, Any]]:
        """
        获取文章的所有评论
        
        Args:
            post_id: 文章 ID
            
        Returns:
            List[Dict]: 评论列表
        """
        logger.info(f"Fetching comments for post ID: {post_id}")
        response = self.get(f"/posts/{post_id}/comments")
        return response.json()
    
    # ==================== 评论相关接口 ====================
    
    def get_all_comments(self) -> List[Dict[str, Any]]:
        """
        获取所有评论列表
        
        Returns:
            List[Dict]: 评论列表
        """
        logger.info("Fetching all comments")
        response = self.get("/comments")
        return response.json()
    
    def get_comment_by_id(self, comment_id: int) -> Dict[str, Any]:
        """
        根据 ID 获取评论详情
        
        Args:
            comment_id: 评论 ID
            
        Returns:
            Dict: 评论详情
        """
        logger.info(f"Fetching comment with ID: {comment_id}")
        response = self.get(f"/comments/{comment_id}")
        return response.json()
    
    def get_comments_by_post(self, post_id: int) -> List[Dict[str, Any]]:
        """
        根据文章 ID 获取评论列表（使用查询参数）
        
        Args:
            post_id: 文章 ID
            
        Returns:
            List[Dict]: 评论列表
        """
        logger.info(f"Fetching comments for post ID: {post_id} (via query)")
        response = self.get("/comments", params={"postId": post_id})
        return response.json()
    
    # ==================== 待办事项相关接口 ====================
    
    def get_all_todos(self) -> List[Dict[str, Any]]:
        """
        获取所有待办事项列表
        
        Returns:
            List[Dict]: 待办事项列表
        """
        logger.info("Fetching all todos")
        response = self.get("/todos")
        return response.json()
    
    def get_todo_by_id(self, todo_id: int) -> Dict[str, Any]:
        """
        根据 ID 获取待办事项详情
        
        Args:
            todo_id: 待办事项 ID
            
        Returns:
            Dict: 待办事项详情
        """
        logger.info(f"Fetching todo with ID: {todo_id}")
        response = self.get(f"/todos/{todo_id}")
        return response.json()
    
    def create_todo(
        self,
        user_id: int,
        title: str,
        completed: bool = False
    ) -> Dict[str, Any]:
        """
        创建新待办事项
        
        Args:
            user_id: 用户 ID
            title: 待办事项标题
            completed: 是否已完成
            
        Returns:
            Dict: 创建的待办事项信息
        """
        logger.info(f"Creating todo for user ID: {user_id}")
        payload = {
            "userId": user_id,
            "title": title,
            "completed": completed
        }
        response = self.post("/todos", json=payload)
        return response.json()
    
    # ==================== 数据提取和缓存辅助方法 ====================
    
    def get_and_cache_user(self, user_id: int, cache_key: str = "current_user") -> Dict[str, Any]:
        """
        获取用户信息并缓存
        
        Args:
            user_id: 用户 ID
            cache_key: 缓存键名
            
        Returns:
            Dict: 用户信息
        """
        response = self.get(f"/users/{user_id}")
        user_data = self.extract_and_cache(response, cache_key)
        return user_data
    
    def get_and_cache_user_id(self, user_id: int) -> int:
        """
        获取用户信息并缓存用户 ID
        
        Args:
            user_id: 用户 ID
            
        Returns:
            int: 用户 ID
        """
        response = self.get(f"/users/{user_id}")
        cached_id = self.extract_and_cache(response, "user_id", "id")
        return cached_id
    
    def get_and_cache_post_id(self, post_id: int) -> int:
        """
        获取文章信息并缓存文章 ID
        
        Args:
            post_id: 文章 ID
            
        Returns:
            int: 文章 ID
        """
        response = self.get(f"/posts/{post_id}")
        cached_id = self.extract_and_cache(response, "post_id", "id")
        return cached_id
    
    def create_and_cache_post(
        self,
        user_id: int,
        title: str,
        body: str,
        cache_key: str = "created_post"
    ) -> Dict[str, Any]:
        """
        创建文章并缓存
        
        Args:
            user_id: 用户 ID
            title: 文章标题
            body: 文章内容
            cache_key: 缓存键名
            
        Returns:
            Dict: 创建的文章信息
        """
        response = self.post(
            "/posts",
            json={"userId": user_id, "title": title, "body": body}
        )
        post_data = self.extract_and_cache(response, cache_key)
        return post_data
