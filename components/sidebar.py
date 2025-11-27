"""侧边栏组件"""
import dash_bootstrap_components as dbc
from dash import html
from language_manager import language_manager

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
    "borderRight": "1px solid #dee2e6",
}

CONTENT_STYLE = {
    "marginLeft": "18rem",
    "marginRight": "2rem",
    "padding": "2rem 1rem",
}


def create_sidebar():
    """创建侧边栏导航"""
    # 确保使用当前语言（从配置文件加载）
    current_lang = language_manager.get_language()
    texts = language_manager.get_all_texts(current_lang)
    
    return html.Div(
        [
            html.H3(texts["sidebar_title"], id="sidebar-title", className="mb-4", style={"color": "#2c3e50"}),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [html.I(className="fas fa-database me-2"), html.Span(texts["datasource_management"], id="nav-datasource")],
                        href="/datasource",
                        active="exact",
                        className="nav-link-custom",
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-chart-line me-2"), html.Span(texts["chart_designer"], id="nav-chart-designer")],
                        href="/chart-designer",
                        active="exact",
                        className="nav-link-custom",
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-tachometer-alt me-2"), html.Span(texts["dashboard"], id="nav-dashboard")],
                        href="/dashboard",
                        active="exact",
                        className="nav-link-custom",
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-cog me-2"), html.Span(texts["settings"], id="nav-settings")],
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
                    html.P([texts["version"], ": v1.0"], id="sidebar-version", className="text-muted small"),
                    html.P(texts["ui_only"], id="sidebar-ui-only", className="text-muted small"),
                ],
                style={"position": "absolute", "bottom": "2rem"}
            ),
        ],
        style=SIDEBAR_STYLE,
        id="sidebar-container",
    )

