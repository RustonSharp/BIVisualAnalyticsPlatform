"""
CSV/Excel 文件适配器
支持本地文件上传和解析
"""

import os
from typing import Dict, Any, Optional
import pandas as pd
from bi_visual_analytics.adapters.base import DataSourceAdapter


class CSVAdapter(DataSourceAdapter):
    """CSV/Excel 文件适配器"""

    def __init__(self):
        super().__init__()
        self.file_path = None
        self.df = None

    def connect(self, config: Dict[str, Any]) -> bool:
        """
        连接到 CSV/Excel 文件

        Args:
            config: 配置字典，包含 file_path 和可选的 encoding、separator 等

        Returns:
            bool: 连接是否成功
        """
        try:
            self.file_path = config.get("file_path")
            if not self.file_path or not os.path.exists(self.file_path):
                raise FileNotFoundError(f"文件不存在: {self.file_path}")

            file_ext = os.path.splitext(self.file_path)[1].lower()

            # 读取文件
            if file_ext == ".csv":
                encoding = config.get("encoding", "utf-8")
                separator = config.get("separator", ",")
                self.df = pd.read_csv(
                    self.file_path, encoding=encoding, sep=separator
                )
            elif file_ext in [".xls", ".xlsx"]:
                sheet_name = config.get("sheet_name", 0)
                self.df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")

            self.config = config
            self.connected = True
            self.schema = self._infer_column_types(self.df)

            return True

        except Exception as e:
            print(f"连接失败: {str(e)}")
            self.connected = False
            return False

    def fetch_data(self, query: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        获取数据

        Args:
            query: 查询条件，支持：
                - columns: 要返回的列名列表
                - limit: 返回行数限制
                - filters: 筛选条件

        Returns:
            pd.DataFrame: 数据结果
        """
        if not self.connected or self.df is None:
            raise RuntimeError("未连接到数据源")

        result = self.df.copy()

        if query:
            # 列筛选
            if "columns" in query and query["columns"]:
                result = result[query["columns"]]

            # 数据筛选
            if "filters" in query:
                for filter_condition in query["filters"]:
                    col = filter_condition.get("column")
                    op = filter_condition.get("operator")
                    value = filter_condition.get("value")

                    if op == "==":
                        result = result[result[col] == value]
                    elif op == "!=":
                        result = result[result[col] != value]
                    elif op == ">":
                        result = result[result[col] > value]
                    elif op == ">=":
                        result = result[result[col] >= value]
                    elif op == "<":
                        result = result[result[col] < value]
                    elif op == "<=":
                        result = result[result[col] <= value]

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
            raise RuntimeError("未连接到数据源")

        return {
            "columns": list(self.df.columns),
            "types": self.schema,
            "row_count": len(self.df),
        }

    def preview_data(self, rows: int = 10) -> pd.DataFrame:
        """
        预览数据

        Args:
            rows: 预览行数

        Returns:
            pd.DataFrame: 预览数据
        """
        if not self.connected or self.df is None:
            raise RuntimeError("未连接到数据源")

        return self.df.head(rows)
