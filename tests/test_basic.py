"""
测试脚本：验证核心功能
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from bi_visual_analytics.adapters import CSVAdapter
from bi_visual_analytics.charts import ChartEngine
from bi_visual_analytics.utils import ConfigManager


class TestCSVAdapter(unittest.TestCase):
    """测试 CSV 适配器"""

    def setUp(self):
        self.adapter = CSVAdapter()

    def test_connect_success(self):
        """测试成功连接"""
        result = self.adapter.connect({"file_path": "data/sample_sales.csv"})
        self.assertTrue(result)
        self.assertTrue(self.adapter.connected)

    def test_connect_failure(self):
        """测试连接失败"""
        result = self.adapter.connect({"file_path": "nonexistent.csv"})
        self.assertFalse(result)

    def test_fetch_data(self):
        """测试数据获取"""
        self.adapter.connect({"file_path": "data/sample_sales.csv"})
        data = self.adapter.fetch_data()
        self.assertIsInstance(data, pd.DataFrame)
        self.assertGreater(len(data), 0)

    def test_get_schema(self):
        """测试获取结构"""
        self.adapter.connect({"file_path": "data/sample_sales.csv"})
        schema = self.adapter.get_schema()
        self.assertIn("columns", schema)
        self.assertIn("types", schema)
        self.assertIn("row_count", schema)


class TestChartEngine(unittest.TestCase):
    """测试图表引擎"""

    def setUp(self):
        self.engine = ChartEngine()
        # 创建测试数据
        self.test_data = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=10),
                "sales": [100, 150, 120, 200, 180, 220, 190, 210, 230, 250],
                "category": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"],
            }
        )

    def test_create_line_chart(self):
        """测试创建折线图"""
        fig = self.engine.create_chart(
            self.test_data, {"type": "line", "x": "date", "y": "sales"}
        )
        self.assertIsNotNone(fig)

    def test_create_bar_chart(self):
        """测试创建柱状图"""
        fig = self.engine.create_chart(
            self.test_data, {"type": "bar", "x": "category", "y": "sales"}
        )
        self.assertIsNotNone(fig)

    def test_aggregate_data(self):
        """测试数据聚合"""
        result = self.engine.aggregate_data(
            self.test_data, {"group_by": "category", "agg_func": "sum", "y": "sales"}
        )
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # A 和 B 两个类别

    def test_apply_filters(self):
        """测试数据筛选"""
        filtered = self.engine.apply_filters(
            self.test_data, {"category": {"category": ["A"]}}
        )
        self.assertEqual(len(filtered), 5)  # 应该只有类别 A 的数据


class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""

    def setUp(self):
        self.manager = ConfigManager()

    def test_validate_csv_config(self):
        """测试 CSV 配置验证"""
        valid_config = {"type": "csv", "file_path": "data.csv"}
        result = self.manager.validate_datasource_config(valid_config)
        self.assertTrue(result)

    def test_validate_invalid_config(self):
        """测试无效配置"""
        invalid_config = {"type": "csv"}  # 缺少 file_path
        with self.assertRaises(ValueError):
            self.manager.validate_datasource_config(invalid_config)


if __name__ == "__main__":
    print("运行单元测试...\n")
    unittest.main(verbosity=2)
