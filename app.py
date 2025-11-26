"""
BI 数据可视化与分析平台 - 主应用入口（重构版）
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from pathlib import Path

# 导入核心模块
from config_manager import ConfigManager
from data_adapter import DataSourceManager
from chart_engine import ChartEngine

# 导入页面模块
from pages import (
    create_datasource_page,
    register_datasource_callbacks,
    create_chart_designer_page,
    register_chart_designer_callbacks,
    create_dashboard_page,
    register_dashboard_callbacks,
    create_settings_page,
)

# 导入组件和样式
from components import create_sidebar, CONTENT_STYLE
from styles.custom import get_index_string

# ==========================================
# 初始化 Dash 应用
# ==========================================
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True
)

app.title = "BI 数据可视化与分析平台"

# 设置自定义 index_string
app.index_string = get_index_string()

# ==========================================
# 初始化核心模块
# ==========================================
config_manager = ConfigManager()
data_source_manager = DataSourceManager()
chart_engine = ChartEngine()

# 创建必要的目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

# ==========================================
# 主布局
# ==========================================
# 导入语言管理器
from language_manager import language_manager

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="datasource-save-success", data=False),
        dcc.Store(id="global-refresh-interval-setting", data="off"),  # 全局刷新间隔设置
        dcc.Store(id="global-language-setting", data=language_manager.get_language()),  # 全局语言设置
        create_sidebar(),
        html.Div(id="page-content", style=CONTENT_STYLE),
    ]
)

# ==========================================
# 路由回调
# ==========================================
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    """根据路径显示对应页面"""
    if pathname == "/" or pathname == "/datasource":
        return create_datasource_page()
    elif pathname == "/chart-designer":
        return create_chart_designer_page()
    elif pathname == "/dashboard":
        return create_dashboard_page()
    elif pathname == "/settings":
        return create_settings_page()
    else:
        # 默认跳转到数据源页面
        return create_datasource_page()

# ==========================================
# 注册所有页面的回调函数
# ==========================================
# 注册数据源页面回调
register_datasource_callbacks(app, config_manager, data_source_manager, UPLOAD_DIR)

# 注册图表设计器页面回调
register_chart_designer_callbacks(app, config_manager, data_source_manager, chart_engine, EXPORT_DIR)

# 注册仪表盘页面回调
register_dashboard_callbacks(app, config_manager, data_source_manager, chart_engine, EXPORT_DIR)

# 注册设置页面回调
from pages.settings_page import register_settings_callbacks
register_settings_callbacks(app)

# ==========================================
# 语言切换全局回调
# ==========================================
@app.callback(
    [Output("sidebar-title", "children", allow_duplicate=True),
     Output("nav-datasource", "children", allow_duplicate=True),
     Output("nav-chart-designer", "children", allow_duplicate=True),
     Output("nav-dashboard", "children", allow_duplicate=True),
     Output("nav-settings", "children", allow_duplicate=True),
     Output("sidebar-version", "children", allow_duplicate=True),
     Output("sidebar-ui-only", "children", allow_duplicate=True),
     Output("page-content", "children", allow_duplicate=True)],
    [Input("global-language-setting", "data")],
    [State("url", "pathname")],
    prevent_initial_call=True
)
def update_all_pages_on_language_change(language, pathname):
    """语言变化时更新所有页面和侧边栏"""
    texts = language_manager.get_all_texts(language)
    
    # 更新侧边栏
    sidebar_title = texts["sidebar_title"]
    nav_datasource = texts["datasource_management"]
    nav_chart_designer = texts["chart_designer"]
    nav_dashboard = texts["dashboard"]
    nav_settings = texts["settings"]
    sidebar_version = [texts["version"], ": v1.0"]
    sidebar_ui_only = texts["ui_only"]
    
    # 更新当前页面
    if pathname == "/" or pathname == "/datasource":
        page_content = create_datasource_page()
    elif pathname == "/chart-designer":
        page_content = create_chart_designer_page()
    elif pathname == "/dashboard":
        page_content = create_dashboard_page()
    elif pathname == "/settings":
        page_content = create_settings_page()
    else:
        page_content = create_datasource_page()
    
    return (sidebar_title, nav_datasource, nav_chart_designer, nav_dashboard, 
            nav_settings, sidebar_version, sidebar_ui_only, page_content)

# ==========================================
# 启动应用
# ==========================================
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
