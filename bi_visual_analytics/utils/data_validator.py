"""
数据验证工具
提供数据质量检查和验证功能
"""

import pandas as pd
from typing import Dict, Any, List, Tuple


class DataValidator:
    """数据验证器"""

    @staticmethod
    def check_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
        """
        检查缺失值

        Args:
            df: DataFrame

        Returns:
            dict: 每列的缺失值统计
        """
        missing_stats = {}

        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_ratio = missing_count / len(df) if len(df) > 0 else 0

            missing_stats[col] = {
                "count": int(missing_count),
                "ratio": round(missing_ratio, 4),
            }

        return missing_stats

    @staticmethod
    def check_duplicates(df: pd.DataFrame) -> int:
        """
        检查重复行

        Args:
            df: DataFrame

        Returns:
            int: 重复行数量
        """
        return df.duplicated().sum()

    @staticmethod
    def check_data_types(df: pd.DataFrame) -> Dict[str, str]:
        """
        检查数据类型

        Args:
            df: DataFrame

        Returns:
            dict: 列名到数据类型的映射
        """
        return {str(col): str(dtype) for col, dtype in df.dtypes.items()}

    @staticmethod
    def detect_outliers(
        df: pd.DataFrame, column: str, method: str = "iqr"
    ) -> Tuple[List[int], pd.Series]:
        """
        检测异常值

        Args:
            df: DataFrame
            column: 列名
            method: 检测方法 ('iqr' 或 'zscore')

        Returns:
            tuple: (异常值索引列表, 异常值 Series)
        """
        if method == "iqr":
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]

        elif method == "zscore":
            mean = df[column].mean()
            std = df[column].std()
            z_scores = (df[column] - mean) / std
            outliers = df[abs(z_scores) > 3]

        else:
            raise ValueError(f"不支持的检测方法: {method}")

        return outliers.index.tolist(), outliers[column]

    @staticmethod
    def validate_chart_config(config: Dict[str, Any], df: pd.DataFrame) -> List[str]:
        """
        验证图表配置是否与数据匹配

        Args:
            config: 图表配置
            df: DataFrame

        Returns:
            list: 错误信息列表
        """
        errors = []

        # 检查 X 轴字段
        if "x" in config and config["x"] not in df.columns:
            errors.append(f"X 轴字段 '{config['x']}' 不存在于数据中")

        # 检查 Y 轴字段
        if "y" in config:
            y_fields = config["y"] if isinstance(config["y"], list) else [config["y"]]
            for field in y_fields:
                if field not in df.columns:
                    errors.append(f"Y 轴字段 '{field}' 不存在于数据中")

        # 检查分组字段
        if "group_by" in config and config["group_by"] not in df.columns:
            errors.append(f"分组字段 '{config['group_by']}' 不存在于数据中")

        return errors

    @staticmethod
    def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取数据摘要统计

        Args:
            df: DataFrame

        Returns:
            dict: 数据摘要信息
        """
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": DataValidator.check_data_types(df),
            "missing_values": DataValidator.check_missing_values(df),
            "duplicate_rows": DataValidator.check_duplicates(df),
            "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB",
        }

        # 数值列统计
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if numeric_cols:
            summary["numeric_summary"] = df[numeric_cols].describe().to_dict()

        return summary
