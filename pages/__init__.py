"""页面模块"""
from .datasource_page import create_datasource_page, register_datasource_callbacks
from .chart_designer_page import create_chart_designer_page, register_chart_designer_callbacks
from .dashboard_page import create_dashboard_page, register_dashboard_callbacks
from .settings_page import create_settings_page, register_settings_callbacks

__all__ = [
    'create_datasource_page',
    'register_datasource_callbacks',
    'create_chart_designer_page',
    'register_chart_designer_callbacks',
    'create_dashboard_page',
    'register_dashboard_callbacks',
    'create_settings_page',
    'register_settings_callbacks',
]

