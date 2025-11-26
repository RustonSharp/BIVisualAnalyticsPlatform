"""
语言管理模块
负责管理应用的语言设置（中文/英文）
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

# 语言配置文件路径
LANGUAGE_CONFIG_FILE = Path("config/language.json")

# 默认语言
DEFAULT_LANGUAGE = "zh"

# 语言文本字典
LANGUAGE_TEXTS = {
    "zh": {
        # 通用
        "loading": "加载中...",
        "save": "保存",
        "cancel": "取消",
        "delete": "删除",
        "edit": "编辑",
        "add": "新增",
        "close": "关闭",
        "confirm": "确认",
        "test": "测试",
        "success": "成功",
        "error": "错误",
        "warning": "警告",
        
        # 侧边栏
        "sidebar_title": "BI Platform",
        "datasource_management": "数据源管理",
        "chart_designer": "图表设计器",
        "dashboard": "仪表盘",
        "settings": "设置",
        "version": "版本",
        "ui_only": "仅 UI 界面",
        
        # 设置页面
        "general_settings": "通用设置",
        "auto_refresh_interval": "自动刷新间隔",
        "off": "关闭",
        "minutes": "分钟",
        "hour": "小时",
        "default_chart_theme": "默认图表主题",
        "default": "默认",
        "business_blue": "商务蓝",
        "vibrant_orange": "活力橙",
        "natural_green": "自然绿",
        "save_settings": "保存设置",
        "settings_saved": "设置已保存成功！",
        "datasource_config": "数据源配置",
        "export_config": "导出配置",
        "export_all_datasource_config": "导出所有数据源配置",
        "import_config": "导入配置",
        "import_datasource_config": "导入数据源配置",
        "language_settings": "语言设置",
        "select_language": "选择语言",
        "chinese": "中文",
        "english": "English",
        "language_changed": "语言已切换成功！",
        
        # 数据源页面
        "datasource_management_title": "数据源管理",
        "datasource_list": "数据源列表",
        "add_datasource": "+ 新增数据源",
        "upload_file": "上传文件",
        "upload_file_button": "上传文件",
        "supported_formats": "支持 CSV、Excel (.xls, .xlsx)",
        "datasource_name": "数据源名称",
        "datasource_name_placeholder": "例如: 销售数据",
        "local_file": "本地文件 (CSV/Excel)",
        "database": "数据库",
        "rest_api": "REST API",
        "database_type": "数据库类型",
        "database_host": "主机地址",
        "database_port": "端口",
        "database_name": "数据库名",
        "database_user": "用户名",
        "database_password": "密码",
        "sql_query": "SQL 查询",
        "table_name": "表名",
        "api_url": "API 地址",
        "request_method": "请求方法",
        "test_connection": "测试连接",
        "connection_success": "连接成功！",
        "connection_failed": "连接失败",
        
        # 图表设计器页面
        "chart_designer_title": "图表设计器",
        "select_datasource": "选择数据源",
        "field_list": "字段列表（可拖拽）",
        "select_datasource_first": "请选择数据源后查看字段",
        "chart_type": "图表类型",
        "line_chart": "折线图",
        "bar_chart": "柱状图",
        "pie_chart": "饼图",
        "table": "表格",
        "combo_chart": "组合图",
        "chart_config": "图表配置",
        "x_axis": "X 轴",
        "y_axis": "Y 轴",
        "group": "分组",
        "chart_title": "图表标题",
        "color_theme": "颜色主题",
        "show_labels": "显示数据标签",
        "show_legend": "显示图例",
        "aggregation_function": "聚合函数",
        "preview": "预览",
        "save_chart": "保存图表",
        
        # 仪表盘页面
        "dashboard_title": "仪表盘",
        "select_dashboard": "选择仪表盘",
        "create_dashboard": "创建仪表盘",
        "dashboard_name": "仪表盘名称",
        "dashboard_description": "描述",
        "time_filter": "时间筛选",
        "today": "今天",
        "last_7_days": "近7天",
        "last_30_days": "近30天",
        "last_90_days": "近90天",
        "this_month": "本月",
        "last_month": "上月",
        "custom_range": "自定义范围",
        "export": "导出",
        "refresh": "刷新",
    },
    "en": {
        # 通用
        "loading": "Loading...",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "edit": "Edit",
        "add": "Add",
        "close": "Close",
        "confirm": "Confirm",
        "test": "Test",
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        
        # 侧边栏
        "sidebar_title": "BI Platform",
        "datasource_management": "Datasource Management",
        "chart_designer": "Chart Designer",
        "dashboard": "Dashboard",
        "settings": "Settings",
        "version": "Version",
        "ui_only": "UI Only",
        
        # 设置页面
        "general_settings": "General Settings",
        "auto_refresh_interval": "Auto Refresh Interval",
        "off": "Off",
        "minutes": "minutes",
        "hour": "hour",
        "default_chart_theme": "Default Chart Theme",
        "default": "Default",
        "business_blue": "Business Blue",
        "vibrant_orange": "Vibrant Orange",
        "natural_green": "Natural Green",
        "save_settings": "Save Settings",
        "settings_saved": "Settings saved successfully!",
        "datasource_config": "Datasource Configuration",
        "export_config": "Export Configuration",
        "export_all_datasource_config": "Export All Datasource Configurations",
        "import_config": "Import Configuration",
        "import_datasource_config": "Import Datasource Configuration",
        "language_settings": "Language Settings",
        "select_language": "Select Language",
        "chinese": "中文",
        "english": "English",
        "language_changed": "Language changed successfully!",
        
        # 数据源页面
        "datasource_management_title": "Datasource Management",
        "datasource_list": "Datasource List",
        "add_datasource": "+ Add Datasource",
        "upload_file": "Upload File",
        "upload_file_button": "Upload File",
        "supported_formats": "Supports CSV, Excel (.xls, .xlsx)",
        "datasource_name": "Datasource Name",
        "datasource_name_placeholder": "e.g.: Sales Data",
        "local_file": "Local File (CSV/Excel)",
        "database": "Database",
        "rest_api": "REST API",
        "database_type": "Database Type",
        "database_host": "Host",
        "database_port": "Port",
        "database_name": "Database Name",
        "database_user": "Username",
        "database_password": "Password",
        "sql_query": "SQL Query",
        "table_name": "Table Name",
        "api_url": "API URL",
        "request_method": "Request Method",
        "test_connection": "Test Connection",
        "connection_success": "Connection successful!",
        "connection_failed": "Connection failed",
        
        # 图表设计器页面
        "chart_designer_title": "Chart Designer",
        "select_datasource": "Select Datasource",
        "field_list": "Field List (Draggable)",
        "select_datasource_first": "Please select a datasource to view fields",
        "chart_type": "Chart Type",
        "line_chart": "Line Chart",
        "bar_chart": "Bar Chart",
        "pie_chart": "Pie Chart",
        "table": "Table",
        "combo_chart": "Combo Chart",
        "chart_config": "Chart Configuration",
        "x_axis": "X Axis",
        "y_axis": "Y Axis",
        "group": "Group",
        "chart_title": "Chart Title",
        "color_theme": "Color Theme",
        "show_labels": "Show Labels",
        "show_legend": "Show Legend",
        "aggregation_function": "Aggregation Function",
        "preview": "Preview",
        "save_chart": "Save Chart",
        
        # 仪表盘页面
        "dashboard_title": "Dashboard",
        "select_dashboard": "Select Dashboard",
        "create_dashboard": "Create Dashboard",
        "dashboard_name": "Dashboard Name",
        "dashboard_description": "Description",
        "time_filter": "Time Filter",
        "today": "Today",
        "last_7_days": "Last 7 Days",
        "last_30_days": "Last 30 Days",
        "last_90_days": "Last 90 Days",
        "this_month": "This Month",
        "last_month": "Last Month",
        "custom_range": "Custom Range",
        "export": "Export",
        "refresh": "Refresh",
    }
}


class LanguageManager:
    """语言管理器"""
    
    def __init__(self):
        """初始化语言管理器"""
        self.config_file = LANGUAGE_CONFIG_FILE
        self.config_file.parent.mkdir(exist_ok=True)
        self._current_language = self.load_language()
    
    def load_language(self) -> str:
        """从配置文件加载语言设置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('language', DEFAULT_LANGUAGE)
            except Exception as e:
                print(f"Error loading language config: {e}")
                return DEFAULT_LANGUAGE
        return DEFAULT_LANGUAGE
    
    def save_language(self, language: str) -> bool:
        """保存语言设置到配置文件"""
        try:
            config = {'language': language}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self._current_language = language
            return True
        except Exception as e:
            print(f"Error saving language config: {e}")
            return False
    
    def get_language(self) -> str:
        """获取当前语言"""
        return self._current_language
    
    def get_text(self, key: str, language: str = None) -> str:
        """获取指定语言的文本"""
        lang = language or self._current_language
        return LANGUAGE_TEXTS.get(lang, LANGUAGE_TEXTS[DEFAULT_LANGUAGE]).get(key, key)
    
    def get_all_texts(self, language: str = None) -> Dict[str, str]:
        """获取指定语言的所有文本"""
        lang = language or self._current_language
        return LANGUAGE_TEXTS.get(lang, LANGUAGE_TEXTS[DEFAULT_LANGUAGE])


# 全局语言管理器实例
language_manager = LanguageManager()

