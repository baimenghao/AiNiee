print('[DEBUG] import start TaskConfig.py')
import os
import re
import threading
import urllib

import rapidjson as json

from Base.BaseLogic import BaseLogic
from ModuleFolders.TaskConfig.TaskType import TaskType
print('[DEBUG] import end TaskConfig.py')

print('[DEBUG] class TaskConfig definition')
# 接口请求器
class TaskConfig(BaseLogic):

    # 打印时的类型过滤器
    TYPE_FILTER = (int, str, bool, float, list, dict, tuple)

    def __init__(self) -> None:
        print('[DEBUG] TaskConfig.__init__ start')
        super().__init__()
        self.init_local_config()
        print('[DEBUG] TaskConfig.__init__ end')

    def init_local_config(self) -> None:
        print('[DEBUG] TaskConfig.init_local_config start')
        # 只做本地变量、配置文件的初始化，不做任何网络请求
        self._config_lock = threading.Lock()
        self._api_key_lock = threading.Lock()
        self.apikey_index = 0
        self.apikey_list = []
        self.label_output_path = "./output"
        self.polishing_output_path = "./polish_output"
        self.auto_set_output_path = True
        self.output_filename_suffix = "_translated"
        self.bilingual_text_order = "translation_first"
        self.response_conversion_toggle = False
        self.opencc_preset = "s2t"
        self.keep_original_encoding = False
        self.lines_limit_switch = False
        self.tokens_limit_switch = True
        self.lines_limit = 10
        self.tokens_limit = 512
        self.user_thread_counts = 0
        self.request_timeout = 120
        self.round_limit = 10
        self.translation_project = "AutoType"
        self.source_language = "auto"
        self.target_language = "chinese_simplified"
        self.model = ""
        self.target_platform = ""
        self.api_settings = {}
        self.platforms = {}
        self.label_input_path = ""
        self.actual_thread_counts = 1
        self.pre_line_counts = 1
        self.polishing_mode_selection = "source_text_polish"
        self.polishing_pre_line_counts = 1
        self.polishing_prompt_selection = {"last_selected_id": None, "prompt_content": ""}
        self.pre_translation_data = []
        self.post_translation_data = []
        self.exclusion_list_data = []
        self.prompt_dictionary_data = []
        self.pre_translation_switch = False
        self.post_translation_switch = False
        self.exclusion_list_switch = False
        self.prompt_dictionary_switch = False
        self.auto_process_text_code_segment = False
        self.few_shot_and_example_switch = False
        self.translation_example_switch = False
        self.characterization_switch = False
        self.writing_style_switch = False
        self.world_building_switch = False
        self.polishing_style_switch = False
        self.writing_style_content = ""
        self.world_building_content = ""
        self.translation_example_data = []
        self.translation_prompt_selection = {"last_selected_id": None, "prompt_content": ""}
        self.translation_user_prompt_data = []
        self.characterization_data = []
        self.polishing_style_content = ""
        self.polishing_user_prompt_data = []
        self.polishing_prompt_selection = {"last_selected_id": None, "prompt_content": ""}
        self.plugins_enable = {}
        self.proxy_url = ""
        self.proxy_enable = False
        self.font_hinting = False
        self.scale_factor = "100%"
        self.interface_language_setting = "auto"
        self.auto_check_update = True
        self.response_check_switch = {
            "newline_character_count_check": False,
            "html_tag_check": False,
            "markdown_check": False,
            "code_block_check": False,
            "image_check": False,
            "table_check": False,
            "list_check": False,
            "link_check": False,
            "check_all": False
        }
        
        print('[DEBUG] TaskConfig.init_local_config end')

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self.get_vars()})"
        )

    def get_vars(self) -> dict:
        return {
            k:v
            for k, v in vars(self).items()
            if isinstance(v, __class__.TYPE_FILTER)
        }

    def get_next_apikey(self) -> str:
        """
        线程安全的轮询获取 API Key
        """
        with self._api_key_lock:
            if not self.apikey_list:
                return "no_key_required"
            
            # 边界检查
            if self.apikey_index >= len(self.apikey_list):
                self.apikey_index = 0

            key = self.apikey_list[self.apikey_index]

            # 更新索引（如果还有下一个 key，则递增，否则归零）
            if len(self.apikey_list) > 1:
                self.apikey_index = (self.apikey_index + 1) % len(self.apikey_list)

            return key

    # 读取配置文件
    def initialize(self) -> None:
        # 读取配置文件
        config = self.load_config()

        # 将字典中的每一项赋值到类中的同名属性
        for key, value in config.items():
            setattr(self, key, value)

    # 准备翻译
    def prepare_for_translation(self, mode, from_api=False) -> None:
        print(f"[prepare_for_translation] 进入方法, mode={mode}")
        # 只打印接口传递的 api_settings 参数
        print(f"[prepare_for_translation] 参数 api_settings: {getattr(self, 'api_settings', None)}")
        # 获取目标平台
        if mode == TaskType.TRANSLATION:
            print("[prepare_for_translation] 获取翻译平台 ...")
            self.target_platform = self.api_settings["translate"]
        elif mode == TaskType.POLISH:
            print("[prepare_for_translation] 获取润色平台 ...")
            self.target_platform = self.api_settings["polish"]
        elif mode == TaskType.FORMAT:
            print("[prepare_for_translation] 获取格式化平台 ...")
            self.target_platform = self.api_settings["format"]
        print(f"[prepare_for_translation] 目标平台: {self.target_platform}")

        # 获取模型类型
        platform_conf = self.platforms.get(self.target_platform)
        if platform_conf is None:
            example = f'{{"{self.target_platform}": {{...}}}}'
            raise ValueError(f"platforms 参数缺少 {self.target_platform} 的配置，请检查 API 传参。platforms 应包含如: {example}")
        print("[prepare_for_translation] 获取模型类型 ...")
        self.model = platform_conf.get("model")
        print(f"[prepare_for_translation] 模型: {self.model}")

        # 分割密钥字符串
        print("[prepare_for_translation] 获取API Key ...")
        api_key = self.platforms.get(self.target_platform).get("api_key")
        if api_key == "":
            self.apikey_list = ["no_key_required"]
            self.apikey_index = 0
        else:
            self.apikey_list = re.sub(r"\s+","", api_key).split(",")
            self.apikey_index = 0
        print(f"[prepare_for_translation] apikey_list: {self.apikey_list}")

        # 获取接口地址并自动补全
        print("[prepare_for_translation] 获取接口地址 ...")
        self.base_url = self.platforms.get(self.target_platform).get("api_url")
        auto_complete = self.platforms.get(self.target_platform).get("auto_complete")

        if (self.target_platform == "sakura" or self.target_platform == "LocalLLM") and not self.base_url.endswith("/v1"):
            self.base_url += "/v1"
        elif auto_complete:
            version_suffixes = ["/v1", "/v2", "/v3", "/v4"]
            if not any(self.base_url.endswith(suffix) for suffix in version_suffixes):
                self.base_url += "/v1"
        print(f"[prepare_for_translation] base_url: {self.base_url}")

        # 获取接口限额
        print("[prepare_for_translation] 获取接口限额 ...")
        self.rpm_limit = self.platforms.get(self.target_platform).get("rpm_limit", 4096)
        self.tpm_limit = self.platforms.get(self.target_platform).get("tpm_limit", 10000000)
        print(f"[prepare_for_translation] rpm_limit: {self.rpm_limit}, tpm_limit: {self.tpm_limit}")

        # 根据密钥数量给 RPM 和 TPM 限额翻倍
        self.rpm_limit = self.rpm_limit * len(self.apikey_list)
        self.tpm_limit = self.tpm_limit * len(self.apikey_list)
        print(f"[prepare_for_translation] 限额乘以密钥数: rpm_limit={self.rpm_limit}, tpm_limit={self.tpm_limit}")

        # 如果开启自动设置输出文件夹功能，设置为输入文件夹的平级目录
        if self.auto_set_output_path == True:
            print("[prepare_for_translation] 自动设置输出路径 ...")
            abs_input_path = os.path.abspath(self.label_input_path)
            parent_dir = os.path.dirname(abs_input_path)
            output_folder_name = "AiNieeOutput"
            self.label_output_path = os.path.join(parent_dir, output_folder_name)

            # 润色文本输出路径
            abs_input_path = os.path.abspath(self.label_input_path)
            parent_dir = os.path.dirname(abs_input_path)
            output_folder_name = "PolishingOutput"
            self.polishing_output_path = os.path.join(parent_dir, output_folder_name)
            print(f"[prepare_for_translation] label_output_path: {self.label_output_path}, polishing_output_path: {self.polishing_output_path}")

        # 只在非API场景下保存全局配置
        if not from_api:
            config = self.load_config()
            print("[prepare_for_translation] 保存新配置前 config:", config)
            print(f"[prepare_for_translation] label_output_path: {self.label_output_path}, polishing_output_path: {self.polishing_output_path}")
            config["label_output_path"] = self.label_output_path
            config["polishing_output_path"] = self.polishing_output_path
            self.save_config(config)
            print("[prepare_for_translation] 保存新配置后")

        # 计算实际线程数
        print("[prepare_for_translation] 计算实际线程数 ...")
        self.actual_thread_counts = self.thread_counts_setting(self.user_thread_counts,self.target_platform,self.rpm_limit)
        print(f"[prepare_for_translation] actual_thread_counts: {self.actual_thread_counts}")

    # 自动计算实际请求线程数
    def thread_counts_setting(self,user_thread_counts,target_platform,rpm_limit) -> None:
        # 如果用户指定了线程数，则使用用户指定的线程数
        if user_thread_counts > 0:
            actual_thread_counts = user_thread_counts

        # 如果是本地类接口，尝试访问slots数
        elif target_platform in ("sakura","LocalLLM"):
            num = self.get_llama_cpp_slots_num(self.platforms.get(target_platform).get("api_url"))
            actual_thread_counts = num if num > 0 else 4
            self.info(f"根据 llama.cpp 接口信息，自动设置同时执行的翻译任务数量为 {actual_thread_counts} 个 ...")

        # 如果用户没有指定线程数，则自动计算
        else :
            actual_thread_counts = self.calculate_thread_count(rpm_limit)
            self.info(f"根据账号类型和接口限额，自动设置同时执行的翻译任务数量为 {actual_thread_counts} 个 ...")

        return actual_thread_counts

    # 获取 llama.cpp 的 slots 数量，获取失败则返回 -1
    def get_llama_cpp_slots_num(self,url: str) -> int:
        try:
            num = -1
            url = url.replace("/v1", "") if url.endswith("/v1") else url
            # 增加timeout，防止阻塞
            with urllib.request.urlopen(f"{url}/slots", timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                num = len(data) if data != None and len(data) > 0 else num
        except Exception:
            pass
        finally:
            return num
        
    # 线性计算并发线程数
    def calculate_thread_count(self,rpm_limit):

        min_rpm = 1
        max_rpm = 10000
        min_threads = 1
        max_threads = 100

        if rpm_limit <= min_rpm:
            rpm_threads = min_threads
        elif rpm_limit >= max_rpm:
            rpm_threads = max_threads
        else:
            # 线性插值计算 RPM 对应的线程数
            rpm_threads = min_threads + (rpm_limit - min_rpm) * (max_threads - min_threads) / (max_rpm - min_rpm)

        rpm_threads = int(round(rpm_threads)) # 四舍五入取整

        # 确保线程数在 1-100 范围内，并使用 CPU 核心数作为辅助上限 
        # 更简洁的方式是直接限制在 1-100 范围内，因为 100 通常已经足够高
        actual_thread_counts = max(1, min(100, rpm_threads)) # 限制在 1-100

        return actual_thread_counts


    # 获取接口配置信息包
    def get_platform_configuration(self,platform_type):

        if platform_type == "translationReq":
            target_platform = self.api_settings["translate"]
        elif platform_type == "polishingReq":
            target_platform = self.api_settings["polish"]
        elif platform_type == "formatReq":
            target_platform = self.api_settings["format"]

        api_url = self.base_url
        api_key = self.get_next_apikey()
        api_format = self.platforms.get(target_platform).get("api_format")
        model_name = self.model
        region = self.platforms.get(target_platform).get("region",'')
        access_key = self.platforms.get(target_platform).get("access_key",'')
        secret_key = self.platforms.get(target_platform).get("secret_key",'')
        request_timeout = self.request_timeout
        temperature = self.platforms.get(target_platform).get("temperature")
        top_p = self.platforms.get(target_platform).get("top_p")
        presence_penalty = self.platforms.get(target_platform).get("presence_penalty")
        frequency_penalty = self.platforms.get(target_platform).get("frequency_penalty")
        extra_body = self.platforms.get(target_platform).get("extra_body",{})
        think_switch = self.platforms.get(target_platform).get("think_switch")
        think_depth = self.platforms.get(target_platform).get("think_depth")

        params = {
            "target_platform": target_platform,
            "api_url": api_url,
            "api_key": api_key,
            "api_format": api_format,
            "model_name": model_name,
            "region": region,
            "access_key": access_key,
            "secret_key": secret_key,
            "request_timeout": request_timeout,
            "temperature": temperature,
            "top_p": top_p,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "extra_body": extra_body,
            "think_switch": think_switch,
            "think_depth": think_depth
        }



        return params

    def init_api_config(self, mode, from_api=False) -> None:
        """
        由GUI或API线程调用，做API相关的初始化和检测。
        """
        self.prepare_for_translation(mode, from_api=from_api)



