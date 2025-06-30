import os
import traceback

import rapidjson as json
from PyQt5.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition

from Base.BaseLogic import BaseLogic, Event, Status


class Base(BaseLogic):

    # 事件列表
    EVENT = Event()

    # 状态列表
    STATUS = Status()

    # 多语言界面配置信息 (类变量)
    multilingual_interface_dict = {}

    # 当前语言 (类变量)
    current_interface_language = "简中"

    # 多语言配置路径
    translation_json_file = os.path.join(".", "Resource", "Localization")

    # UI文本翻译
    @classmethod # 类方法，因为要访问类变量
    def tra(cls, text): # 修改为 cls
        translation = cls.multilingual_interface_dict.get(text) # 使用 cls.multilingual_interface_dict
        if translation:
            translation_text = translation.get(cls.current_interface_language) # 使用 cls.current_interface_language
            if translation_text:
                return translation_text
        return text


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # 获取事件管理器单例
        # self.event_manager_singleton = EventManager()

        # 类变量
        Base.work_status = Base.STATUS.IDLE if not hasattr(Base, "work_status") else Base.work_status


    # 读取多语言配置信息方法
    def load_translations(cls, folder_path):
        combined_data = {}
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                filepath = os.path.join(folder_path, filename)
                try: 
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for top_level_key in data:
                            for key, value in data[top_level_key].items():
                                combined_data[key] = value
                except Exception as e:
                    print(f"[red]Error loading translation file {filename}: {e}[/red]")
                    traceback.print_exc() # 打印更详细的错误信息
        return combined_data

    def get_parent_window(self):
        """统一获取父窗口对象"""
        if hasattr(self, 'window'):
            if callable(self.window):
                return self.window()
            else:
                return self.window
        return None

    # Toast
    def info_toast(self, title: str, content: str) -> None:
        InfoBar.info(
            title = title,
            content = content,
            parent = self.get_parent_window(),
            duration = 2500,
            orient = Qt.Horizontal,
            position = InfoBarPosition.TOP,
            isClosable = True,
        )

    # Toast
    def error_toast(self, title: str, content: str) -> None:
        InfoBar.error(
            title = title,
            content = content,
            parent = self.get_parent_window(),
            duration = 2500,
            orient = Qt.Horizontal,
            position = InfoBarPosition.TOP,
            isClosable = True,
        )
    
    # Toast
    def success_toast(self, title: str, content: str) -> None:
        InfoBar.success(
            title = title,
            content = content,
            parent = self.get_parent_window(),
            duration = 2500,
            orient = Qt.Horizontal,
            position = InfoBarPosition.TOP,
            isClosable = True,
        )

    # Toast
    def warning_toast(self, title: str, content: str) -> None:
        InfoBar.warning(
            title = title,
            content = content,
            parent = self.get_parent_window(),
            duration = 2500,
            orient = Qt.Horizontal,
            position = InfoBarPosition.TOP,
            isClosable = True,
        )