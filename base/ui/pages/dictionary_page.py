from playwright.sync_api import Page, expect

from base.ui.pages.base_page import BasePage
from core.log import get_logger

logger = get_logger(__name__)


class DictionaryPage(BasePage):
    """
    门户字典页面
    """
    def __init__(self, page: Page):
        super().__init__(page)
        logger.info("Panji Dictionary Page initialized")
        # 查询
        self.filter_dictionary = page.get_by_role("textbox", name="字典名称")
        self.btn_search_dictionary = page.get_by_role("button", name="查询")

        self.link_plane = page.get_by_role("cell", name="PLANE").locator("a") #PLANE 字典
        self.link_cell = page.get_by_role("cell", name="CELL").locator("a") #CELL 字典

        #新增字典数据
        self.add_dict_btn= page.get_by_role("button", name="新增")
        self.menu_dictionary=page.get_by_role("main").get_by_text("门户字典")

        #新增plane
        self.plane_name_input = page.get_by_role("textbox", name="请输入平面名称")
        self.plane_code_input = page.get_by_role("textbox", name="请输入平面编码")
        #新增cell
        self.cell_name_input = page.get_by_role("textbox", name="请输入单元名称")
        self.cell_code_input = page.get_by_role("textbox", name="请输入单元编码")
        self.plane_code_dropdown = page.get_by_role("textbox", name="请选择平面编码")
        self.env_code_dropdown = page.get_by_role("textbox", name="请选择环境编码")

        self.confirm_btn = page.get_by_role("button", name="确定")
        self.cancel_btn = page.get_by_role("button", name="取消")
        self.alert= page.locator(".el-message__content").first  #

        # 删除按钮
        self.delete_confirm_btn = page.get_by_role("button", name="删除")

    def search_plane_and_click(self):
        """
        search_plane
        """
        self.filter_dictionary.fill("平面")
        self.btn_search_dictionary.click()
        expect(self.link_plane).to_be_visible()
        self.link_plane.click()
        expect(self.page.get_by_text("字典数据")).to_be_visible()
        self.page.wait_for_load_state(state="load")
        logger.info("进入字典数据页面")

    def search_cell_and_click(self):
        """
        search_cell
        """
        self.filter_dictionary.fill("单元")
        self.btn_search_dictionary.click()
        expect(self.link_cell).to_be_visible()
        self.link_cell.click()
        expect(self.page.get_by_text("字典数据")).to_be_visible()
        self.page.wait_for_load_state(state="load")
        logger.info("进入字典数据页面")

    def add_plane(self, plane_name: str, plane_code: str):
        """
        新增平面字典数据
        """
        logger.info("点击【新增】")
        self.add_dict_btn.click()
        logger.info("进入新增平面页面")
        self.page.wait_for_load_state(state="load")
        logger.info("自定义填写平面名称、平面编码，点击【确定】")
        self.plane_name_input.fill(plane_name)
        self.plane_code_input.fill(plane_code)
        self.confirm_btn.click()

    def add_cell(self, cell_name: str, cell_code: str, plane_name: str, plane_code: str):
        """
        新增单元字典数据
        """
        if self.page.get_by_text("cellname").count() > 0:
            logger.info(plane_name + "单元已存在，不能重复添加")
        else:
            logger.info("点击【新增】")
            self.add_dict_btn.click()
            logger.info("进入新增单元页面")
            self.page.wait_for_load_state(state="load")
            logger.info("自定义填写单元名称、单元编码，选择平面编码（前面创建的）、环境编码，点击【确定】")
            self.cell_name_input.fill(cell_name)
            self.cell_code_input.fill(cell_code)
            self.plane_code_dropdown.click()
            self.page.get_by_text(plane_name + plane_code).click()
            self.env_code_dropdown.click()
            self.page.get_by_text("生产环境PROD").click()
            self.confirm_btn.click()

    def delete_plane(self, plane_name: str, plane_code: str):
        """
        删除平面数据
        """
        self.page.get_by_role("row", name=plane_name + " " + plane_code + " " + "1  ").locator("i").nth(1).click()
        self.delete_confirm_btn.click()

    def delete_cell(self, cell_name: str, cell_code: str):
        """
        删除单元数据
        """
        self.page.get_by_role("row", name=cell_name + " " + cell_code + " ").locator("i").nth(1).click()
        self.delete_confirm_btn.click()