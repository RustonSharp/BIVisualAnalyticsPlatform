"""
配置管理器
负责读写和验证配置文件
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """配置文件管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为项目根目录的 config 文件夹
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 默认使用项目根目录的 config 文件夹
            self.config_dir = Path(__file__).parent.parent.parent / "config"

        self.config_dir.mkdir(exist_ok=True)

    def load_datasource_config(self, path: str) -> Dict[str, Any]:
        """
        加载数据源配置

        Args:
            path: 配置文件路径（支持相对路径和绝对路径）

        Returns:
            dict: 配置内容
        """
        file_path = self._resolve_path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        # 根据文件扩展名选择解析方式
        ext = file_path.suffix.lower()

        if ext in [".yaml", ".yml"]:
            with open(file_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            raise ValueError(f"不支持的配置文件格式: {ext}")

        # 验证配置
        self.validate_datasource_config(config)

        return config

    def save_datasource_config(self, config: Dict[str, Any], path: str):
        """
        保存数据源配置

        Args:
            config: 配置内容
            path: 保存路径
        """
        file_path = self._resolve_path(path)

        # 验证配置
        self.validate_datasource_config(config)

        # 创建目录
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 根据文件扩展名选择保存方式
        ext = file_path.suffix.lower()

        if ext in [".yaml", ".yml"]:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        elif ext == ".json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的配置文件格式: {ext}")

    def load_dashboard_config(self, path: str) -> Dict[str, Any]:
        """
        加载仪表盘配置

        Args:
            path: 配置文件路径

        Returns:
            dict: 仪表盘配置
        """
        file_path = self._resolve_path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 验证配置
        self.validate_dashboard_config(config)

        return config

    def save_dashboard_config(self, config: Dict[str, Any], path: str):
        """
        保存仪表盘配置

        Args:
            config: 仪表盘配置
            path: 保存路径
        """
        file_path = self._resolve_path(path)

        # 验证配置
        self.validate_dashboard_config(config)

        # 创建目录
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def validate_datasource_config(self, config: Dict[str, Any]) -> bool:
        """
        验证数据源配置

        Args:
            config: 数据源配置

        Returns:
            bool: 验证是否通过

        Raises:
            ValueError: 配置格式错误
        """
        if not isinstance(config, dict):
            raise ValueError("配置必须是字典格式")

        # 检查必需字段
        if "type" not in config:
            raise ValueError("配置中缺少 'type' 字段")

        datasource_type = config["type"]

        # 根据类型验证特定字段
        if datasource_type == "csv":
            if "file_path" not in config:
                raise ValueError("CSV 配置中缺少 'file_path' 字段")

        elif datasource_type == "database":
            required_fields = ["host", "database", "username", "password"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"数据库配置中缺少 '{field}' 字段")

        elif datasource_type == "api":
            if "url" not in config:
                raise ValueError("API 配置中缺少 'url' 字段")

        else:
            raise ValueError(f"不支持的数据源类型: {datasource_type}")

        return True

    def validate_dashboard_config(self, config: Dict[str, Any]) -> bool:
        """
        验证仪表盘配置

        Args:
            config: 仪表盘配置

        Returns:
            bool: 验证是否通过

        Raises:
            ValueError: 配置格式错误
        """
        if not isinstance(config, dict):
            raise ValueError("配置必须是字典格式")

        # 检查必需字段
        if "title" not in config:
            raise ValueError("仪表盘配置中缺少 'title' 字段")

        if "charts" not in config or not isinstance(config["charts"], list):
            raise ValueError("仪表盘配置中缺少 'charts' 字段或格式错误")

        # 验证每个图表配置
        for i, chart in enumerate(config["charts"]):
            if "id" not in chart:
                raise ValueError(f"图表 {i} 缺少 'id' 字段")
            if "type" not in chart:
                raise ValueError(f"图表 {i} 缺少 'type' 字段")

        return True

    def _resolve_path(self, path: str) -> Path:
        """
        解析路径（支持相对路径和绝对路径）

        Args:
            path: 文件路径

        Returns:
            Path: 解析后的路径对象
        """
        path_obj = Path(path)

        # 如果是绝对路径，直接返回
        if path_obj.is_absolute():
            return path_obj

        # 如果是相对路径，相对于配置目录
        return self.config_dir / path_obj

    def create_default_datasource_config(self, datasource_type: str, path: str):
        """
        创建默认数据源配置模板

        Args:
            datasource_type: 数据源类型 (csv/database/api)
            path: 保存路径
        """
        if datasource_type == "csv":
            config = {
                "name": "示例 CSV 数据源",
                "type": "csv",
                "file_path": "data/sample.csv",
                "encoding": "utf-8",
                "separator": ",",
            }
        elif datasource_type == "database":
            config = {
                "name": "示例数据库",
                "type": "database",
                "db_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "mydb",
                "username": "user",
                "password": "password",
                "table": "sales",
            }
        elif datasource_type == "api":
            config = {
                "name": "示例 API",
                "type": "api",
                "url": "https://api.example.com/data",
                "method": "GET",
                "headers": {"Content-Type": "application/json"},
                "json_path": "data.results",
            }
        else:
            raise ValueError(f"不支持的数据源类型: {datasource_type}")

        self.save_datasource_config(config, path)

    def create_default_dashboard_config(self, path: str):
        """
        创建默认仪表盘配置模板

        Args:
            path: 保存路径
        """
        config = {
            "title": "示例仪表盘",
            "description": "这是一个示例仪表盘配置",
            "layout": {"columns": 12, "row_height": 100},
            "charts": [
                {
                    "id": "chart1",
                    "type": "line",
                    "title": "趋势图",
                    "datasource": "sales_data",
                    "x": "date",
                    "y": "revenue",
                    "position": {"x": 0, "y": 0, "w": 6, "h": 4},
                },
                {
                    "id": "chart2",
                    "type": "bar",
                    "title": "对比图",
                    "datasource": "sales_data",
                    "x": "category",
                    "y": "amount",
                    "agg_func": "sum",
                    "position": {"x": 6, "y": 0, "w": 6, "h": 4},
                },
            ],
            "filters": [
                {
                    "type": "date_range",
                    "label": "时间范围",
                    "column": "date",
                    "default": "last_30_days",
                }
            ],
        }

        self.save_dashboard_config(config, path)
