"""
REST API 适配器
支持从 REST API 获取 JSON/XML 数据
"""

from typing import Dict, Any, Optional
import pandas as pd
import requests
from bi_visual_analytics.adapters.base import DataSourceAdapter


class APIAdapter(DataSourceAdapter):
    """REST API 数据适配器"""

    def __init__(self):
        super().__init__()
        self.url = None
        self.df = None

    def connect(self, config: Dict[str, Any]) -> bool:
        """
        连接到 API 并获取数据

        Args:
            config: 配置字典，包含：
                - url: API 地址
                - method: 请求方法 (GET/POST)
                - headers: 请求头
                - params: 请求参数
                - data: POST 请求体
                - auth: 认证信息 (username, password) 或 (api_key,)
                - json_path: JSON 数据路径（可选）

        Returns:
            bool: 连接是否成功
        """
        try:
            self.url = config.get("url")
            if not self.url:
                raise ValueError("未提供 API URL")

            method = config.get("method", "GET").upper()
            headers = config.get("headers", {})
            params = config.get("params", {})
            data = config.get("data")

            # 处理认证
            auth = None
            if "auth" in config:
                auth_config = config["auth"]
                if "api_key" in auth_config:
                    headers["Authorization"] = f"Bearer {auth_config['api_key']}"
                elif "username" in auth_config and "password" in auth_config:
                    auth = (auth_config["username"], auth_config["password"])

            # 发送请求
            if method == "GET":
                response = requests.get(
                    self.url, headers=headers, params=params, auth=auth, timeout=30
                )
            elif method == "POST":
                response = requests.post(
                    self.url,
                    headers=headers,
                    params=params,
                    json=data,
                    auth=auth,
                    timeout=30,
                )
            else:
                raise ValueError(f"不支持的请求方法: {method}")

            response.raise_for_status()

            # 解析响应
            content_type = response.headers.get("Content-Type", "")

            if "json" in content_type:
                json_data = response.json()

                # 如果指定了 JSON 路径，提取数据
                if "json_path" in config:
                    for key in config["json_path"].split("."):
                        json_data = json_data[key]

                # 转换为 DataFrame
                if isinstance(json_data, list):
                    self.df = pd.json_normalize(json_data)
                elif isinstance(json_data, dict):
                    self.df = pd.json_normalize([json_data])
                else:
                    raise ValueError("无法解析的 JSON 数据格式")

            else:
                raise ValueError(f"不支持的响应格式: {content_type}")

            self.config = config
            self.connected = True
            self.schema = self._infer_column_types(self.df)

            return True

        except Exception as e:
            print(f"API 连接失败: {str(e)}")
            self.connected = False
            return False

    def fetch_data(self, query: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        获取数据

        Args:
            query: 查询条件（可选）

        Returns:
            pd.DataFrame: 数据结果
        """
        if not self.connected or self.df is None:
            raise RuntimeError("未连接到 API")

        result = self.df.copy()

        if query:
            # 列筛选
            if "columns" in query and query["columns"]:
                result = result[query["columns"]]

            # 行数限制
            if "limit" in query:
                result = result.head(query["limit"])

        return result

    def get_schema(self) -> Dict[str, Any]:
        """
        获取字段信息

        Returns:
            dict: 字段名称和类型的映射
        """
        if not self.connected or self.df is None:
            raise RuntimeError("未连接到 API")

        return {
            "columns": list(self.df.columns),
            "types": self.schema,
            "row_count": len(self.df),
        }

    def refresh(self) -> bool:
        """
        刷新数据（重新请求 API）

        Returns:
            bool: 刷新是否成功
        """
        if not self.config:
            return False

        return self.connect(self.config)
