"""
BI Visual Analytics Platform - 主应用入口
Plotly Dash 交互式仪表盘应用
"""

import os
import base64
import io
from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd

from bi_visual_analytics.adapters import CSVAdapter, DatabaseAdapter, APIAdapter
from bi_visual_analytics.charts.chart_engine import ChartEngine
from bi_visual_analytics.utils.config_manager import ConfigManager
from bi_visual_analytics.utils.logger import setup_logger
from bi_visual_analytics.dashboard.layout_manager import LayoutManager
from bi_visual_analytics.dashboard.export_handler import ExportHandler
from bi_visual_analytics.components.datasource_ui import (
    create_datasource_config_ui,
    create_csv_config,
    create_database_config,
    create_api_config,
)
from bi_visual_analytics.components.chart_designer import (
    create_chart_designer,
    create_field_item,
)
from bi_visual_analytics.components.filter_panel import (
    create_filter_panel,
    create_global_filter_bar,
)

# 初始化日志
logger = setup_logger("bi_dashboard_app")

# 初始化 Dash 应用
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
)

app.title = "BI Visual Analytics Platform"

# 全局变量
current_datasource = None
current_data = None
chart_engine = ChartEngine()
config_manager = ConfigManager()
layout_manager = LayoutManager()
export_handler = ExportHandler()

# 应用布局
app.layout = dbc.Container(
    [
        # 导航栏
        dbc.Navbar(
            dbc.Container(
                [
                    dbc.NavbarBrand(
                        [
                            html.I(className="fas fa-chart-line me-2"),
                            "BI Visual Analytics Platform",
                        ],
                        className="fs-4",
                    ),
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dbc.NavLink("数据源", href="#", id="nav-datasource")
                            ),
                            dbc.NavItem(
                                dbc.NavLink("图表设计", href="#", id="nav-charts")
                            ),
                            dbc.NavItem(
                                dbc.NavLink("仪表盘", href="#", id="nav-dashboard")
                            ),
                            dbc.NavItem(
                                dbc.NavLink("导出", href="#", id="nav-export")
                            ),
                        ],
                        navbar=True,
                    ),
                ],
                fluid=True,
            ),
            color="primary",
            dark=True,
            className="mb-4",
        ),
        # 主内容区域
        dcc.Store(id="datasource-store"),  # 存储数据源配置
        dcc.Store(id="data-store"),  # 存储数据
        dcc.Store(id="chart-store"),  # 存储图表配置
        html.Div(id="main-content"),
    ],
    fluid=True,
)


# 回调：切换页面
@app.callback(
    Output("main-content", "children"),
    [
        Input("nav-datasource", "n_clicks"),
        Input("nav-charts", "n_clicks"),
        Input("nav-dashboard", "n_clicks"),
        Input("nav-export", "n_clicks"),
    ],
    prevent_initial_call=False,
)
def switch_page(ds_clicks, ch_clicks, db_clicks, ex_clicks):
    """根据导航栏点击切换页面"""
    ctx = callback_context

    if not ctx.triggered:
        # 默认显示欢迎页面
        return create_welcome_page()

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "nav-datasource":
        return create_datasource_config_ui()
    elif button_id == "nav-charts":
        return create_chart_designer()
    elif button_id == "nav-dashboard":
        return create_dashboard_page()
    elif button_id == "nav-export":
        return create_export_page()
    else:
        return create_welcome_page()


def create_welcome_page():
    """创建欢迎页面"""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H1(
                                        "🎯 欢迎使用 BI Visual Analytics Platform",
                                        className="text-center mb-4",
                                    ),
                                    html.P(
                                        "轻量级 BI 数据可视化与分析平台",
                                        className="text-center text-muted fs-5 mb-5",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                create_feature_card(
                                                    "📊",
                                                    "多数据源接入",
                                                    "支持 CSV、Excel、PostgreSQL、MySQL、REST API",
                                                ),
                                                md=6,
                                                lg=3,
                                            ),
                                            dbc.Col(
                                                create_feature_card(
                                                    "🎨",
                                                    "拖拽式配置",
                                                    "无需编程，拖拽字段即可生成专业图表",
                                                ),
                                                md=6,
                                                lg=3,
                                            ),
                                            dbc.Col(
                                                create_feature_card(
                                                    "⚡",
                                                    "交互分析",
                                                    "图表联动、时间筛选、数据下钻",
                                                ),
                                                md=6,
                                                lg=3,
                                            ),
                                            dbc.Col(
                                                create_feature_card(
                                                    "💾",
                                                    "多格式导出",
                                                    "支持导出为 PNG、PDF、HTML",
                                                ),
                                                md=6,
                                                lg=3,
                                            ),
                                        ],
                                        className="g-4",
                                    ),
                                    html.Hr(className="my-5"),
                                    html.H4("🚀 快速开始", className="mb-4"),
                                    dbc.ListGroup(
                                        [
                                            dbc.ListGroupItem(
                                                [
                                                    html.Strong("1. 配置数据源："),
                                                    " 点击 '数据源' 菜单，上传 CSV 文件或连接数据库",
                                                ]
                                            ),
                                            dbc.ListGroupItem(
                                                [
                                                    html.Strong("2. 设计图表："),
                                                    " 进入 '图表设计'，拖拽字段创建可视化图表",
                                                ]
                                            ),
                                            dbc.ListGroupItem(
                                                [
                                                    html.Strong("3. 构建仪表盘："),
                                                    " 在 '仪表盘' 中组织多个图表，配置筛选器",
                                                ]
                                            ),
                                            dbc.ListGroupItem(
                                                [
                                                    html.Strong("4. 导出分享："),
                                                    " 通过 '导出' 功能生成报告或分享链接",
                                                ]
                                            ),
                                        ],
                                        className="mb-4",
                                    ),
                                ],
                                className="py-5",
                            )
                        ],
                        width=12,
                    )
                ]
            )
        ],
        className="mt-5",
    )


def create_feature_card(icon, title, description):
    """创建功能卡片"""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2(icon, className="text-center mb-3"),
                html.H5(title, className="text-center mb-2"),
                html.P(description, className="text-center text-muted small"),
            ]
        ),
        className="h-100 shadow-sm",
    )


def create_dashboard_page():
    """创建仪表盘页面"""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col([html.H3("我的仪表盘", className="mb-4")], width=12),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_filter_panel(),
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            create_global_filter_bar(),
                            html.Div(id="dashboard-charts-area"),
                            dbc.Button(
                                "+ 添加图表",
                                id="add-chart-btn",
                                color="primary",
                                className="mt-3",
                            ),
                        ],
                        width=9,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


def create_export_page():
    """创建导出页面"""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H3("导出与分享", className="mb-4"),
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5("选择导出格式"),
                                        dbc.RadioItems(
                                            id="export-format",
                                            options=[
                                                {"label": "PNG 图片", "value": "png"},
                                                {"label": "PDF 文档", "value": "pdf"},
                                                {
                                                    "label": "静态 HTML",
                                                    "value": "html",
                                                },
                                                {"label": "CSV 数据", "value": "csv"},
                                            ],
                                            value="png",
                                            className="mb-3",
                                        ),
                                        dbc.Input(
                                            id="export-filename",
                                            placeholder="输入文件名",
                                            className="mb-3",
                                        ),
                                        dbc.Button(
                                            "导出",
                                            id="export-btn",
                                            color="success",
                                            className="w-100",
                                        ),
                                        html.Div(id="export-feedback", className="mt-3"),
                                    ]
                                )
                            ),
                        ],
                        width=6,
                    )
                ]
            )
        ],
        fluid=True,
    )


# 回调：动态显示数据源配置表单
@app.callback(
    Output("datasource-config-area", "children"),
    Input("datasource-type", "value"),
)
def update_datasource_config(datasource_type):
    """根据数据源类型显示不同的配置表单"""
    if datasource_type == "csv":
        return create_csv_config()
    elif datasource_type == "database":
        return create_database_config()
    elif datasource_type == "api":
        return create_api_config()
    return html.Div()


# 回调：处理 CSV/Excel 文件上传
@app.callback(
    [
        Output("csv-upload-status", "children"),
        Output("csv-file-path", "value"),
    ],
    Input("csv-file-upload", "contents"),
    State("csv-file-upload", "filename"),
    prevent_initial_call=True,
)
def handle_file_upload(contents, filename):
    """处理文件上传"""
    if contents is None:
        return "", ""

    try:
        # 解析上传的文件内容
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)

        # 根据文件扩展名判断文件类型
        if filename.endswith(".csv"):
            # 保存为临时文件
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(decoded)
            
            status_msg = dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"文件上传成功: {filename}",
                ],
                color="success",
                className="mb-0",
            )
            return status_msg, file_path

        elif filename.endswith((".xls", ".xlsx")):
            # Excel 文件
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(decoded)
            
            status_msg = dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Excel 文件上传成功: {filename}",
                ],
                color="success",
                className="mb-0",
            )
            return status_msg, file_path

        else:
            status_msg = dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"不支持的文件格式: {filename}",
                ],
                color="warning",
                className="mb-0",
            )
            return status_msg, ""

    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        status_msg = dbc.Alert(
            [
                html.I(className="fas fa-times-circle me-2"),
                f"文件上传失败: {str(e)}",
            ],
            color="danger",
            className="mb-0",
        )
        return status_msg, ""


if __name__ == "__main__":
    logger.info("启动 BI Visual Analytics Platform...")
    # host="127.0.0.1" 只允许本地访问
    # host="0.0.0.0" 允许局域网其他设备访问
    app.run(debug=True, host="127.0.0.1", port=8050)
