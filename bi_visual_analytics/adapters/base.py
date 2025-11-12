"""
数据源适配器基类
定义统一的数据源接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class DataSourceAdapter(ABC):
    """数据源适配器抽象基类"""

    def __init__(self):
        self.connected = False
        self.config = {}
        self.schema = {}

    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        建立数据源连接

        Args:
            config: 连接配置字典

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    def fetch_data(self, query: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        获取数据

        Args:
            query: 查询条件（可选）

        Returns:
            pd.DataFrame: 数据结果
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        获取数据源的字段信息

        Returns:
            dict: 字段名称和类型的映射
        """
        pass

    def disconnect(self):
        """断开连接"""
        self.connected = False

    def test_connection(self) -> bool:
        """
        测试连接是否正常

        Returns:
            bool: 连接状态
        """
        return self.connected

    def _infer_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        自动识别列的数据类型

        Args:
            df: DataFrame

        Returns:
            dict: 列名到类型的映射 (numeric/datetime/text)
        """
        column_types = {}

        for col in df.columns:
            dtype = df[col].dtype

            if pd.api.types.is_numeric_dtype(dtype):
                column_types[col] = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                column_types[col] = "datetime"
            else:
                # 尝试转换为日期
                try:
                    pd.to_datetime(df[col].dropna().head(100))
                    column_types[col] = "datetime"
                except (ValueError, TypeError):
                    column_types[col] = "text"

        return column_types
