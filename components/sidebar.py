"""侧边栏组件"""
import dash_bootstrap_components as dbc
from dash import html

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "border-right": "1px solid #dee2e6",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}


def create_sidebar():
    """创建侧边栏导航"""
    return html.Div(
        [
            html.H3("BI Platform", className="mb-4", style={"color": "#2c3e50"}),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [html.I(className="fas fa-database me-2"), "数据源管理"],
                        href="/datasource",
                        active="exact",
                        className="nav-link-custom",
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-chart-line me-2"), "图表设计器"],
                        href="/chart-designer",
                        active="exact",
                        className="nav-link-custom",
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-tachometer-alt me-2"), "仪表盘"],
                        href="/dashboard",
                        active="exact",
                        className="nav-link-custom",
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-cog me-2"), "设置"],
                        href="/settings",
                        active="exact",
                        className="nav-link-custom",
                    ),
                ],
                vertical=True,
                pills=True,
            ),
            html.Hr(className="my-4"),
            html.Div(
                [
                    html.P("版本: v1.0", className="text-muted small"),
                    html.P("仅 UI 界面", className="text-muted small"),
                ],
                style={"position": "absolute", "bottom": "2rem"}
            ),
        ],
        style=SIDEBAR_STYLE,
    )

