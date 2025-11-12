"""
BI Visual Analytics Platform
轻量级 BI 数据可视化与分析平台

支持多数据源接入、拖拽式图表配置、交互式仪表盘生成
"""

__version__ = "1.0.0"
__author__ = "BI Platform Team"

from bi_visual_analytics.adapters.base import DataSourceAdapter
from bi_visual_analytics.charts.chart_engine import ChartEngine
from bi_visual_analytics.utils.config_manager import ConfigManager

__all__ = [
    "DataSourceAdapter",
    "ChartEngine",
    "ConfigManager",
]
