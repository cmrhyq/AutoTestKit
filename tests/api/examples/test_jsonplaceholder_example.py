"""
JSONPlaceholder API 测试示例

该测试文件演示了如何使用测试框架进行完整的 API 测试，包括：
- 使用 BaseService 和自定义服务类
- 数据提取和缓存功能
- 请求/响应日志记录
- Allure 报告集成
- 测试数据依赖管理
"""

import pytest
import allure
from base.api.services.jsonplaceholder_service import JSONPlaceholderService
from core.log.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.api
@allure.feature("JSONPlaceholder API")
@allure.story("用户管理")
class TestUserAPI:
    """用户相关 API 测试"""
    
    @pytest.fixture(scope="class")
    def json_service(self):
        """创建 JSONPlaceholder 服务实例"""
        service = JSONPlaceholderService(logger=logger)
        yield service
        service.close()
    
    @allure.title("测试获取所有用户列表")
    @allure.description("验证能够成功获取所有用户列表，并检查返回数据的结构")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_users(self, json_service):
        """测试获取所有用户列表"""
        with allure.step("发送 GET 请求获取所有用户"):
            users = json_service.get_all_users()
        
        with allure.step("验证响应数据"):
            assert isinstance(users, list), "响应应该是列表类型"
            assert len(users) > 0, "用户列表不应为空"
            
            # 验证第一个用户的数据结构
            first_user = users[0]
            assert "id" in first_user, "用户对象应包含 id 字段"
            assert "name" in first_user, "用户对象应包含 name 字段"
            assert "email" in first_user, "用户对象应包含 email 字段"
            assert "username" in first_user, "用户对象应包含 username 字段"
        
        logger.info(f"成功获取 {len(users)} 个用户")
        allure.attach(
            f"用户总数: {len(users)}",
            name="用户统计",
            attachment_type=allure.attachment_type.TEXT
        )
    
    @allure.title("测试根据 ID 获取用户信息")
    @allure.description("验证能够根据用户 ID 获取特定用户的详细信息")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user_by_id(self, json_service, api_cache):
        """测试根据 ID 获取用户信息，并缓存用户数据"""
        user_id = 1
        
        with allure.step(f"发送 GET 请求获取用户 ID: {user_id}"):
            user = json_service.get_user_by_id(user_id)
        
        with allure.step("验证用户数据"):
            assert user["id"] == user_id, f"用户 ID 应该是 {user_id}"
            assert "name" in user, "用户应该有 name 字段"
            assert "email" in user, "用户应该有 email 字段"
            assert "address" in user, "用户应该有 address 字段"
            assert "company" in user, "用户应该有 company 字段"
        
        with allure.step("缓存用户数据供后续测试使用"):
            api_cache.set("test_user", user)
            api_cache.set("test_user_id", user["id"])
            logger.info(f"已缓存用户: {user['name']} (ID: {user['id']})")
        
        allure.attach(
            str(user),
            name="用户详细信息",
            attachment_type=allure.attachment_type.JSON
        )
    
    @allure.title("测试获取用户的文章列表")
    @allure.description("验证能够获取指定用户发布的所有文章")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_user_posts(self, json_service, api_cache):
        """测试获取用户的文章列表"""
        # 从缓存中获取用户 ID
        user_id = api_cache.get("test_user_id", 1)
        
        with allure.step(f"发送 GET 请求获取用户 {user_id} 的文章"):
            posts = json_service.get_user_posts(user_id)
        
        with allure.step("验证文章列表"):
            assert isinstance(posts, list), "响应应该是列表类型"
            assert len(posts) > 0, "用户应该有文章"
            
            # 验证文章数据结构
            first_post = posts[0]
            assert "id" in first_post, "文章应包含 id 字段"
            assert "userId" in first_post, "文章应包含 userId 字段"
            assert "title" in first_post, "文章应包含 title 字段"
            assert "body" in first_post, "文章应包含 body 字段"
            assert first_post["userId"] == user_id, f"文章的 userId 应该是 {user_id}"
        
        logger.info(f"用户 {user_id} 共有 {len(posts)} 篇文章")
        allure.attach(
            f"文章总数: {len(posts)}",
            name="文章统计",
            attachment_type=allure.attachment_type.TEXT
        )
    
    @allure.title("测试获取用户的待办事项")
    @allure.description("验证能够获取指定用户的所有待办事项")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_user_todos(self, json_service, api_cache):
        """测试获取用户的待办事项"""
        user_id = api_cache.get("test_user_id", 1)
        
        with allure.step(f"发送 GET 请求获取用户 {user_id} 的待办事项"):
            todos = json_service.get_user_todos(user_id)
        
        with allure.step("验证待办事项列表"):
            assert isinstance(todos, list), "响应应该是列表类型"
            assert len(todos) > 0, "用户应该有待办事项"
            
            # 验证待办事项数据结构
            first_todo = todos[0]
            assert "id" in first_todo, "待办事项应包含 id 字段"
            assert "userId" in first_todo, "待办事项应包含 userId 字段"
            assert "title" in first_todo, "待办事项应包含 title 字段"
            assert "completed" in first_todo, "待办事项应包含 completed 字段"
            assert first_todo["userId"] == user_id, f"待办事项的 userId 应该是 {user_id}"
        
        # 统计完成和未完成的待办事项
        completed_count = sum(1 for todo in todos if todo["completed"])
        incomplete_count = len(todos) - completed_count
        
        logger.info(
            f"用户 {user_id} 共有 {len(todos)} 个待办事项 "
            f"(已完成: {completed_count}, 未完成: {incomplete_count})"
        )
        
        allure.attach(
            f"总数: {len(todos)}\n已完成: {completed_count}\n未完成: {incomplete_count}",
            name="待办事项统计",
            attachment_type=allure.attachment_type.TEXT
        )


@pytest.mark.api
@allure.feature("JSONPlaceholder API")
@allure.story("文章管理")
class TestPostAPI:
    """文章相关 API 测试"""
    
    @pytest.fixture(scope="class")
    def json_service(self):
        """创建 JSONPlaceholder 服务实例"""
        service = JSONPlaceholderService(logger=logger)
        yield service
        service.close()
    
    @allure.title("测试创建新文章")
    @allure.description("验证能够成功创建新文章，并缓存文章 ID 供后续测试使用")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_post(self, json_service, api_cache):
        """测试创建新文章并缓存文章 ID"""
        user_id = 1
        title = "测试文章标题"
        body = "这是一篇测试文章的内容，用于演示 API 测试框架的功能。"
        
        with allure.step("发送 POST 请求创建新文章"):
            post = json_service.create_post(
                user_id=user_id,
                title=title,
                body=body
            )
        
        with allure.step("验证创建的文章数据"):
            assert "id" in post, "响应应包含文章 ID"
            assert post["userId"] == user_id, f"文章的 userId 应该是 {user_id}"
            assert post["title"] == title, "文章标题应该匹配"
            assert post["body"] == body, "文章内容应该匹配"
        
        with allure.step("缓存文章 ID 供后续测试使用"):
            api_cache.set("created_post_id", post["id"])
            api_cache.set("created_post", post)
            logger.info(f"已创建并缓存文章 ID: {post['id']}")
        
        allure.attach(
            str(post),
            name="创建的文章信息",
            attachment_type=allure.attachment_type.JSON
        )
    
    @allure.title("测试获取文章详情")
    @allure.description("验证能够根据文章 ID 获取文章的详细信息")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_post_by_id(self, json_service):
        """测试根据 ID 获取文章详情"""
        post_id = 1
        
        with allure.step(f"发送 GET 请求获取文章 ID: {post_id}"):
            post = json_service.get_post_by_id(post_id)
        
        with allure.step("验证文章数据"):
            assert post["id"] == post_id, f"文章 ID 应该是 {post_id}"
            assert "userId" in post, "文章应包含 userId 字段"
            assert "title" in post, "文章应包含 title 字段"
            assert "body" in post, "文章应包含 body 字段"
            assert len(post["title"]) > 0, "文章标题不应为空"
            assert len(post["body"]) > 0, "文章内容不应为空"
        
        logger.info(f"成功获取文章: {post['title']}")
        allure.attach(
            str(post),
            name="文章详细信息",
            attachment_type=allure.attachment_type.JSON
        )
    
    @allure.title("测试更新文章")
    @allure.description("验证能够更新已存在的文章信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_post(self, json_service):
        """测试更新文章（使用已存在的文章 ID）"""
        # 使用已存在的文章 ID（JSONPlaceholder 有 100 篇文章，ID 1-100）
        post_id = 1
        new_title = "更新后的文章标题"
        new_body = "更新后的文章内容"
        
        with allure.step(f"发送 PUT 请求更新文章 ID: {post_id}"):
            updated_post = json_service.update_post(
                post_id=post_id,
                user_id=1,
                title=new_title,
                body=new_body
            )
        
        with allure.step("验证更新后的文章数据"):
            assert updated_post["id"] == post_id, f"文章 ID 应该保持为 {post_id}"
            assert updated_post["title"] == new_title, "文章标题应该已更新"
            assert updated_post["body"] == new_body, "文章内容应该已更新"
        
        logger.info(f"成功更新文章 ID: {post_id}")
        allure.attach(
            str(updated_post),
            name="更新后的文章信息",
            attachment_type=allure.attachment_type.JSON
        )
    
    @allure.title("测试部分更新文章")
    @allure.description("验证能够部分更新文章的某些字段")
    @allure.severity(allure.severity_level.NORMAL)
    def test_patch_post(self, json_service):
        """测试部分更新文章"""
        post_id = 1
        new_title = "通过 PATCH 更新的标题"
        
        with allure.step(f"发送 PATCH 请求部分更新文章 ID: {post_id}"):
            patched_post = json_service.patch_post(
                post_id=post_id,
                title=new_title
            )
        
        with allure.step("验证部分更新后的文章数据"):
            assert patched_post["id"] == post_id, f"文章 ID 应该保持为 {post_id}"
            assert patched_post["title"] == new_title, "文章标题应该已更新"
        
        logger.info(f"成功部分更新文章 ID: {post_id}")
        allure.attach(
            str(patched_post),
            name="部分更新后的文章信息",
            attachment_type=allure.attachment_type.JSON
        )
    
    @allure.title("测试删除文章")
    @allure.description("验证能够删除指定的文章")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_post(self, json_service, api_cache):
        """测试删除文章"""
        post_id = api_cache.get("created_post_id", 1)
        
        with allure.step(f"发送 DELETE 请求删除文章 ID: {post_id}"):
            result = json_service.delete_post(post_id)
        
        with allure.step("验证删除操作结果"):
            assert result is True, "删除操作应该成功"
        
        logger.info(f"成功删除文章 ID: {post_id}")
        allure.attach(
            f"已删除文章 ID: {post_id}",
            name="删除结果",
            attachment_type=allure.attachment_type.TEXT
        )
    
    @allure.title("测试获取文章的评论")
    @allure.description("验证能够获取指定文章的所有评论")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_post_comments(self, json_service):
        """测试获取文章的评论"""
        post_id = 1
        
        with allure.step(f"发送 GET 请求获取文章 {post_id} 的评论"):
            comments = json_service.get_post_comments(post_id)
        
        with allure.step("验证评论列表"):
            assert isinstance(comments, list), "响应应该是列表类型"
            assert len(comments) > 0, "文章应该有评论"
            
            # 验证评论数据结构
            first_comment = comments[0]
            assert "id" in first_comment, "评论应包含 id 字段"
            assert "postId" in first_comment, "评论应包含 postId 字段"
            assert "name" in first_comment, "评论应包含 name 字段"
            assert "email" in first_comment, "评论应包含 email 字段"
            assert "body" in first_comment, "评论应包含 body 字段"
            assert first_comment["postId"] == post_id, f"评论的 postId 应该是 {post_id}"
        
        logger.info(f"文章 {post_id} 共有 {len(comments)} 条评论")
        allure.attach(
            f"评论总数: {len(comments)}",
            name="评论统计",
            attachment_type=allure.attachment_type.TEXT
        )


@pytest.mark.api
@allure.feature("JSONPlaceholder API")
@allure.story("数据提取和缓存")
class TestDataExtractionAndCaching:
    """数据提取和缓存功能测试"""
    
    @pytest.fixture(scope="class")
    def json_service(self):
        """创建 JSONPlaceholder 服务实例"""
        service = JSONPlaceholderService(logger=logger)
        yield service
        service.close()
    
    @pytest.fixture(autouse=True)
    def clear_cache(self, api_cache):
        """每个测试前清理缓存"""
        api_cache.clear()
        yield
        api_cache.clear()
    
    @allure.title("测试提取并缓存用户 ID")
    @allure.description("验证能够从 API 响应中提取特定字段并缓存")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_extract_and_cache_user_id(self, json_service, api_cache):
        """测试提取并缓存用户 ID"""
        user_id = 5
        
        with allure.step(f"获取用户 {user_id} 并缓存 ID"):
            cached_id = json_service.get_and_cache_user_id(user_id)
        
        with allure.step("验证缓存的用户 ID"):
            assert cached_id == user_id, f"缓存的 ID 应该是 {user_id}"
            
            # 从缓存中直接获取
            retrieved_id = api_cache.get("user_id")
            assert retrieved_id == user_id, "从缓存获取的 ID 应该匹配"
        
        logger.info(f"成功提取并缓存用户 ID: {cached_id}")
        allure.attach(
            f"缓存的用户 ID: {cached_id}",
            name="缓存数据",
            attachment_type=allure.attachment_type.TEXT
        )
    
    @allure.title("测试提取并缓存完整用户对象")
    @allure.description("验证能够缓存完整的 API 响应对象")
    @allure.severity(allure.severity_level.NORMAL)
    def test_extract_and_cache_full_user(self, json_service, api_cache):
        """测试提取并缓存完整用户对象"""
        user_id = 3
        
        with allure.step(f"获取用户 {user_id} 并缓存完整对象"):
            user_data = json_service.get_and_cache_user(user_id, "full_user")
        
        with allure.step("验证缓存的用户对象"):
            assert user_data["id"] == user_id, f"用户 ID 应该是 {user_id}"
            assert "name" in user_data, "用户对象应包含 name 字段"
            assert "email" in user_data, "用户对象应包含 email 字段"
            
            # 从缓存中获取
            cached_user = api_cache.get("full_user")
            assert cached_user == user_data, "缓存的用户对象应该匹配"
        
        logger.info(f"成功缓存完整用户对象: {user_data['name']}")
        allure.attach(
            str(user_data),
            name="缓存的用户对象",
            attachment_type=allure.attachment_type.JSON
        )
    
    @allure.title("测试创建文章并缓存")
    @allure.description("验证能够创建资源并立即缓存返回的数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_and_cache_post(self, json_service, api_cache):
        """测试创建文章并缓存"""
        user_id = 1
        title = "缓存测试文章"
        body = "这是用于测试缓存功能的文章内容"
        
        with allure.step("创建文章并缓存"):
            post_data = json_service.create_and_cache_post(
                user_id=user_id,
                title=title,
                body=body,
                cache_key="new_post"
            )
        
        with allure.step("验证缓存的文章数据"):
            assert post_data["userId"] == user_id, f"用户 ID 应该是 {user_id}"
            assert post_data["title"] == title, "标题应该匹配"
            assert post_data["body"] == body, "内容应该匹配"
            
            # 从缓存中获取
            cached_post = api_cache.get("new_post")
            assert cached_post == post_data, "缓存的文章对象应该匹配"
        
        logger.info(f"成功创建并缓存文章 ID: {post_data.get('id')}")
        allure.attach(
            str(post_data),
            name="缓存的文章对象",
            attachment_type=allure.attachment_type.JSON
        )
    
    @allure.title("测试跨测试用例的数据共享")
    @allure.description("验证缓存的数据能够在不同测试用例之间共享")
    @allure.severity(allure.severity_level.NORMAL)
    def test_data_sharing_between_tests(self, json_service, api_cache):
        """测试跨测试用例的数据共享"""
        # 第一步：创建并缓存数据
        with allure.step("步骤 1: 创建并缓存用户 ID"):
            user_id = json_service.get_and_cache_user_id(2)
            api_cache.set("shared_user_id", user_id)
        
        # 第二步：使用缓存的数据
        with allure.step("步骤 2: 使用缓存的用户 ID 获取文章"):
            cached_user_id = api_cache.get("shared_user_id")
            assert cached_user_id == user_id, "缓存的用户 ID 应该匹配"
            
            posts = json_service.get_user_posts(cached_user_id)
            assert len(posts) > 0, "用户应该有文章"
        
        # 第三步：缓存文章 ID
        with allure.step("步骤 3: 缓存第一篇文章的 ID"):
            first_post_id = posts[0]["id"]
            api_cache.set("shared_post_id", first_post_id)
        
        # 第四步：使用缓存的文章 ID
        with allure.step("步骤 4: 使用缓存的文章 ID 获取评论"):
            cached_post_id = api_cache.get("shared_post_id")
            assert cached_post_id == first_post_id, "缓存的文章 ID 应该匹配"
            
            comments = json_service.get_post_comments(cached_post_id)
            assert len(comments) > 0, "文章应该有评论"
        
        logger.info(
            f"成功演示数据共享: 用户 {user_id} -> 文章 {first_post_id} -> {len(comments)} 条评论"
        )
        
        allure.attach(
            f"用户 ID: {user_id}\n文章 ID: {first_post_id}\n评论数: {len(comments)}",
            name="数据共享流程",
            attachment_type=allure.attachment_type.TEXT
        )


@pytest.mark.api
@allure.feature("JSONPlaceholder API")
@allure.story("错误处理")
class TestErrorHandling:
    """API 错误处理测试"""
    
    @pytest.fixture(scope="class")
    def json_service(self):
        """创建 JSONPlaceholder 服务实例"""
        service = JSONPlaceholderService(logger=logger)
        yield service
        service.close()
    
    @allure.title("测试处理不存在的资源")
    @allure.description("验证当请求不存在的资源时，能够正确处理 404 错误")
    @allure.severity(allure.severity_level.NORMAL)
    def test_handle_not_found_error(self, json_service):
        """测试处理 404 错误"""
        invalid_id = 99999
        
        with allure.step(f"请求不存在的用户 ID: {invalid_id}"):
            with pytest.raises(Exception) as exc_info:
                json_service.get_user_by_id(invalid_id)
        
        logger.info(f"成功捕获 404 错误: {str(exc_info.value)}")
        allure.attach(
            str(exc_info.value),
            name="错误信息",
            attachment_type=allure.attachment_type.TEXT
        )
    
    @allure.title("测试状态码验证")
    @allure.description("验证状态码验证功能能够正确工作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_status_code_validation(self, json_service):
        """测试状态码验证功能"""
        with allure.step("发送请求并验证状态码"):
            response = json_service.get("/users/1")
            
            # 验证正确的状态码
            is_valid = json_service.validate_status_code(response, 200)
            assert is_valid is True, "状态码 200 应该验证通过"
            
            # 验证错误的状态码
            is_invalid = json_service.validate_status_code(response, 404)
            assert is_invalid is False, "状态码 404 应该验证失败"
            
            # 验证多个状态码
            is_valid_multi = json_service.validate_status_code(response, [200, 201])
            assert is_valid_multi is True, "状态码 200 应该在 [200, 201] 中"
        
        logger.info("状态码验证功能测试通过")
        allure.attach(
            "状态码验证功能正常工作",
            name="验证结果",
            attachment_type=allure.attachment_type.TEXT
        )
