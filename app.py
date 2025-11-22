"""
BI 数据可视化与分析平台
完整的 BI 数据可视化与分析平台，支持多数据源、图表生成、仪表盘管理
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import base64
import io
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# 导入核心模块
from config_manager import ConfigManager
from data_adapter import DataSourceAdapter, DataSourceManager
from chart_engine import ChartEngine
from load_data import load_from_file, DBConfig, load_from_database, load_from_api

# 初始化 Dash 应用，使用 Bootstrap 主题
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"],
    suppress_callback_exceptions=True
)

app.title = "BI 数据可视化与分析平台"

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

# 全局状态存储
store = dcc.Store(id="global-store", data={"datasources": {}, "charts": {}, "filters": {}})

# ==========================================
# 辅助函数
# ==========================================
def create_table_from_dataframe(df: pd.DataFrame, **kwargs) -> dbc.Table:
    """从 DataFrame 创建 Bootstrap 表格"""
    # 转换 DataFrame 为 HTML 表格格式
    thead = html.Thead([
        html.Tr([html.Th(col) for col in df.columns])
    ])
    tbody = html.Tbody([
        html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
        for i in range(len(df))
    ])
    
    # 创建表格
    table = dbc.Table(
        [thead, tbody],
        **kwargs
    )
    return table

# ==========================================
# 自定义样式
# ==========================================
CUSTOM_CSS = """
.nav-link-custom {
    padding: 0.75rem 1rem;
    margin-bottom: 0.25rem;
    border-radius: 0.25rem;
    color: #495057;
    transition: all 0.2s;
}

.nav-link-custom:hover {
    background-color: #e9ecef;
    color: #007bff;
}

.nav-link-custom.active {
    background-color: #007bff;
    color: white;
}

.drop-zone {
    transition: all 0.3s;
}

.drop-zone:hover {
    background-color: #f8f9fa;
    border-color: #007bff !important;
}

.card {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border: none;
}

.card-header {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    font-weight: 600;
}

.badge {
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
}

body {
    background-color: #ffffff;
}
"""

app.index_string = f"""
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            {CUSTOM_CSS}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
"""

# ==========================================
# 自定义样式变量
# ==========================================
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

# ==========================================
# 导航栏组件
# ==========================================
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

# ==========================================
# 数据源管理页面
# ==========================================
def create_datasource_page():
    """创建数据源管理页面"""
    return dbc.Container(
        [
            html.H2("数据源管理", className="mb-4"),
            
            # 数据源列表卡片
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.H5("数据源列表", className="mb-0"),
                                        dbc.Button("+ 新增数据源", color="primary", size="sm", className="float-end", id="btn-add-datasource"),
                                    ],
                                    className="d-flex justify-content-between align-items-center",
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(id="datasource-list", children=[
                                            html.P("加载中...", className="text-muted text-center py-5"),
                                        ]),
                                    ]
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=12,
                    ),
                ]
            ),
            
            # 新增/编辑数据源模态框
            dbc.Modal(
                [
                    dbc.ModalHeader(id="modal-datasource-header"),
                    dcc.Store(id="current-datasource-id", data=None),  # 存储当前编辑的数据源ID
                    dcc.Store(id="current-uploaded-file", data=None),  # 存储当前上传的文件名
                    html.Div(id="test-connection-status", className="m-3"),  # 测试连接状态显示
                    dbc.ModalBody(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        [
                                            html.Div([
                                                html.Label("上传文件", className="form-label mt-3"),
                                                dcc.Upload(
                                                    id="upload-file",
                                                    children=html.Div([
                                                        html.I(className="fas fa-cloud-upload-alt fa-3x mb-2"),
                                                        html.P("拖拽文件到此处或点击选择", className="text-muted"),
                                                        html.P("支持 CSV、Excel (.xls, .xlsx)", className="small text-muted"),
                                                    ]),
                                                    style={
                                                        "width": "100%",
                                                        "height": "200px",
                                                        "lineHeight": "200px",
                                                        "borderWidth": "2px",
                                                        "borderStyle": "dashed",
                                                        "borderRadius": "5px",
                                                        "textAlign": "center",
                                                        "cursor": "pointer",
                                                    },
                                                    multiple=False,
                                                ),
                                                html.Div(id="file-upload-status", className="mt-2"),
                                                html.Label("数据源名称", className="form-label mt-3"),
                                                dbc.Input(id="datasource-name-file", placeholder="例如: 销售数据", type="text"),
                                            ]),
                                        ],
                                        label="本地文件 (CSV/Excel)",
                                        tab_id="tab-file",
                                    ),
                                    dbc.Tab(
                                        [
                                            html.Div([
                                                html.Label("数据库类型", className="form-label mt-3"),
                                                dbc.Select(
                                                    id="db-type",
                                                    options=[
                                                        {"label": "PostgreSQL", "value": "postgresql"},
                                                        {"label": "MySQL", "value": "mysql"},
                                                    ],
                                                    value="postgresql",
                                                ),
                                                html.Label("主机地址", className="form-label mt-3"),
                                                dbc.Input(id="db-host", placeholder="localhost", type="text"),
                                                html.Label("端口", className="form-label mt-3"),
                                                dbc.Input(id="db-port", placeholder="5432", type="number"),
                                                html.Label("数据库名", className="form-label mt-3"),
                                                dbc.Input(id="db-database", placeholder="mydb", type="text"),
                                                html.Label("用户名", className="form-label mt-3"),
                                                dbc.Input(id="db-user", placeholder="user", type="text"),
                                                html.Label("密码", className="form-label mt-3"),
                                                dbc.Input(id="db-password", placeholder="password", type="password"),
                                                html.Label("SQL 查询语句", className="form-label mt-3"),
                                                dbc.Textarea(
                                                    id="db-sql",
                                                    placeholder="SELECT * FROM your_table LIMIT 100",
                                                    rows=3,
                                                    value="SELECT * FROM table_name LIMIT 100"
                                                ),
                                                html.Label("数据源名称", className="form-label mt-3"),
                                                dbc.Input(id="datasource-name-db", placeholder="例如: 生产数据库", type="text"),
                                            ]),
                                        ],
                                        label="数据库 (PostgreSQL/MySQL)",
                                        tab_id="tab-database",
                                    ),
                                    dbc.Tab(
                                        [
                                            html.Div([
                                                html.Label("API 地址", className="form-label mt-3"),
                                                dbc.Input(id="api-url", placeholder="https://api.example.com/data", type="text"),
                                                html.Label("请求方法", className="form-label mt-3"),
                                                dbc.Select(
                                                    id="api-method",
                                                    options=[
                                                        {"label": "GET", "value": "GET"},
                                                        {"label": "POST", "value": "POST"},
                                                    ],
                                                    value="GET",
                                                ),
                                                html.Label("请求头 (JSON 格式)", className="form-label mt-3"),
                                                dbc.Textarea(id="api-headers", placeholder='{"Authorization": "Bearer token"}', rows=3),
                                                html.Label("请求参数 (JSON 格式)", className="form-label mt-3"),
                                                dbc.Textarea(id="api-params", placeholder='{"page": 1, "limit": 100}', rows=3),
                                                html.Label("数据源名称", className="form-label mt-3"),
                                                dbc.Input(id="datasource-name-api", placeholder="例如: API 数据源", type="text"),
                                            ]),
                                        ],
                                        label="REST API",
                                        tab_id="tab-api",
                                    ),
                                ],
                                id="datasource-tabs",
                                active_tab="tab-file",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("取消", id="btn-cancel-datasource", color="secondary", className="me-2"),
                            dbc.Button("测试连接", id="btn-test-connection", color="info", className="me-2"),
                            dbc.Button("保存", id="btn-save-datasource", color="primary"),
                        ]
                    ),
                ],
                id="modal-datasource",
                is_open=False,
                size="lg",
            ),
            
            # 数据预览区域
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("数据预览"),
                                dbc.CardBody(
                                    [
                                        html.Div(id="data-preview", children=[
                                            html.P("请选择一个数据源查看预览", className="text-muted text-center py-5"),
                                        ]),
                                    ]
                                ),
                            ],
                        ),
                        width=12,
                    ),
                ],
                className="mt-4",
            ),
        ],
        fluid=True,
    )

# ==========================================
# 图表设计器页面
# ==========================================
def create_chart_designer_page():
    """创建图表设计器页面"""
    return dbc.Container(
        [
            html.H2("图表设计器", className="mb-4"),
            
            dbc.Row(
                [
                    # 左侧：字段列表和配置区
                    dbc.Col(
                        [
                            # 数据源选择
                            dbc.Card(
                                [
                                    dbc.CardHeader("选择数据源"),
                                    dbc.CardBody(
                                        [
                                            dbc.Select(
                                                id="chart-datasource-select",
                                                options=[
                                                    {"label": "销售数据_CSV", "value": "datasource1"},
                                                ],
                                                value="datasource1",
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                            
                            # 字段列表
                            dbc.Card(
                                [
                                    dbc.CardHeader("字段列表（可拖拽）"),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Badge("date (日期)", color="primary", className="m-1 p-2", style={"cursor": "grab"}),
                                                    dbc.Badge("value (数值)", color="success", className="m-1 p-2", style={"cursor": "grab"}),
                                                    dbc.Badge("category (文本)", color="info", className="m-1 p-2", style={"cursor": "grab"}),
                                                ],
                                                id="field-list",
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                            
                            # 图表类型选择
                            dbc.Card(
                                [
                                    dbc.CardHeader("图表类型"),
                                    dbc.CardBody(
                                        [
                                            dbc.RadioItems(
                                                id="chart-type",
                                                options=[
                                                    {"label": "折线图", "value": "line"},
                                                    {"label": "柱状图", "value": "bar"},
                                                    {"label": "饼图", "value": "pie"},
                                                    {"label": "表格", "value": "table"},
                                                    {"label": "组合图", "value": "combo"},
                                                ],
                                                value="line",
                                                inline=True,
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                            
                            # 拖拽配置区
                            dbc.Card(
                                [
                                    dbc.CardHeader("图表配置"),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.Label("X 轴", className="form-label fw-bold"),
                                                    html.Div(
                                                        id="drop-x-axis",
                                                        children=[
                                                            html.P("拖拽字段到此处", className="text-muted text-center py-3 border border-dashed rounded"),
                                                        ],
                                                        style={"min-height": "60px", "margin-bottom": "15px"},
                                                        className="drop-zone",
                                                    ),
                                                    html.Label("Y 轴", className="form-label fw-bold"),
                                                    html.Div(
                                                        id="drop-y-axis",
                                                        children=[
                                                            html.P("拖拽字段到此处", className="text-muted text-center py-3 border border-dashed rounded"),
                                                        ],
                                                        style={"min-height": "60px", "margin-bottom": "15px"},
                                                        className="drop-zone",
                                                    ),
                                                    html.Label("分组/颜色", className="form-label fw-bold"),
                                                    html.Div(
                                                        id="drop-group",
                                                        children=[
                                                            html.P("拖拽字段到此处", className="text-muted text-center py-3 border border-dashed rounded"),
                                                        ],
                                                        style={"min-height": "60px", "margin-bottom": "15px"},
                                                        className="drop-zone",
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                            
                            # 聚合函数
                            dbc.Card(
                                [
                                    dbc.CardHeader("聚合函数"),
                                    dbc.CardBody(
                                        [
                                            dbc.Select(
                                                id="agg-function",
                                                options=[
                                                    {"label": "求和 (SUM)", "value": "sum"},
                                                    {"label": "平均值 (AVG)", "value": "avg"},
                                                    {"label": "计数 (COUNT)", "value": "count"},
                                                    {"label": "最大值 (MAX)", "value": "max"},
                                                    {"label": "最小值 (MIN)", "value": "min"},
                                                ],
                                                value="sum",
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                            
                            # 样式配置
                            dbc.Card(
                                [
                                    dbc.CardHeader("样式配置"),
                                    dbc.CardBody(
                                        [
                                            html.Label("图表标题", className="form-label"),
                                            dbc.Input(id="chart-title", placeholder="请输入图表标题", type="text", className="mb-3"),
                                            html.Label("颜色主题", className="form-label"),
                                            dbc.Select(
                                                id="color-theme",
                                                options=[
                                                    {"label": "默认", "value": "default"},
                                                    {"label": "商务蓝", "value": "blue"},
                                                    {"label": "活力橙", "value": "orange"},
                                                    {"label": "自然绿", "value": "green"},
                                                    {"label": "优雅紫", "value": "purple"},
                                                ],
                                                value="default",
                                                className="mb-3",
                                            ),
                                            dbc.Checklist(
                                                options=[
                                                    {"label": "显示数据标签", "value": "show-labels"},
                                                    {"label": "显示图例", "value": "show-legend"},
                                                ],
                                                value=["show-legend"],
                                                id="chart-options",
                                            ),
                                        ]
                                    ),
                                ],
                            ),
                        ],
                        width=3,
                    ),
                    
                    # 右侧：图表预览
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.Span("图表预览", className="me-auto"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button("保存图表", color="success", size="sm"),
                                                    dbc.Button("导出图片", color="info", size="sm"),
                                                ],
                                                className="float-end",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="chart-preview", children=[
                                                # 示例图表预览（使用示例数据）
                                                dcc.Graph(
                                                    figure=px.line(
                                                        pd.DataFrame({
                                                            'date': pd.date_range('2025-01-01', periods=10),
                                                            'value': [10, 12, 15, 13, 18, 20, 17, 19, 22, 21]
                                                        }),
                                                        x='date',
                                                        y='value',
                                                        title='示例折线图预览'
                                                    ).update_layout(template='plotly_white', height=500),
                                                    id="preview-chart"
                                                ),
                                                html.P("配置图表参数后，预览将自动更新", className="text-muted text-center small"),
                                            ]),
                                        ]
                                    ),
                                ],
                                style={"height": "100%"},
                            ),
                        ],
                        width=9,
                    ),
                ]
            ),
        ],
        fluid=True,
    )

# ==========================================
# 仪表盘页面
# ==========================================
def create_dashboard_page():
    """创建仪表盘页面"""
    # 尝试从已保存的仪表盘加载图表，如果没有则使用示例数据
    dashboards = config_manager.load_dashboards()
    charts = config_manager.load_charts()
    
    # 如果有已保存的图表，使用它们
    if charts:
        # 稍后通过回调动态加载
        return create_dashboard_page_content(dynamic=True)
    else:
        # 使用示例数据
        return create_dashboard_page_content(dynamic=False)

def create_dashboard_page_content(dynamic=False):
    """创建仪表盘页面内容"""
    # 创建示例图表数据
    sample_data = pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=10),
        'value': [10, 12, 15, 13, 18, 20, 17, 19, 22, 21],
        'category': ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C', 'A']
    })
    
    # 折线图示例
    fig_line = px.line(sample_data, x='date', y='value', title='销售额趋势', markers=True)
    fig_line.update_layout(template='plotly_white', height=300)
    
    # 柱状图示例
    fig_bar = px.bar(sample_data.groupby('category')['value'].sum().reset_index(), 
                     x='category', y='value', title='分类销售额对比')
    fig_bar.update_layout(template='plotly_white', height=300)
    
    # 饼图示例
    fig_pie = px.pie(sample_data.groupby('category')['value'].sum().reset_index(),
                     values='value', names='category', title='分类占比')
    fig_pie.update_layout(template='plotly_white', height=300)
    
    return dbc.Container(
        [
            # 顶部工具栏
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("我的仪表盘", className="mb-0"),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.ButtonGroup(
                                [
                                    dbc.Button([html.I(className="fas fa-plus me-1"), "新建仪表盘"], color="primary", size="sm"),
                                    dbc.Button([html.I(className="fas fa-edit me-1"), "编辑"], color="secondary", size="sm"),
                                    dbc.Button([html.I(className="fas fa-download me-1"), "导出"], color="success", size="sm"),
                                    dbc.DropdownMenu(
                                        [
                                            dbc.DropdownMenuItem("导出为 PNG", id="export-png"),
                                            dbc.DropdownMenuItem("导出为 PDF", id="export-pdf"),
                                            dbc.DropdownMenuItem("导出为 HTML", id="export-html"),
                                        ],
                                        label="更多",
                                        size="sm",
                                        color="info",
                                    ),
                                ],
                                className="float-end",
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="mb-4",
            ),
            
            # 筛选器工具栏
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Label("时间范围", className="form-label"),
                                            dbc.RadioItems(
                                                id="time-filter",
                                                options=[
                                                    {"label": "今天", "value": "today"},
                                                    {"label": "近7天", "value": "7days"},
                                                    {"label": "近30天", "value": "30days"},
                                                    {"label": "本月", "value": "month"},
                                                    {"label": "自定义", "value": "custom"},
                                                ],
                                                value="30days",
                                                inline=True,
                                            ),
                                            html.Div(id="custom-date-range", style={"display": "none"}, children=[
                                                html.Label("起始日期", className="form-label mt-2"),
                                                dcc.DatePickerSingle(id="start-date", className="mb-2"),
                                                html.Label("结束日期", className="form-label"),
                                                dcc.DatePickerSingle(id="end-date"),
                                            ]),
                                        ]
                                    ),
                                ],
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            
            # 图表网格布局
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.Span("销售额趋势", className="me-auto"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(html.I(className="fas fa-ellipsis-v"), color="link", size="sm"),
                                                ],
                                                className="float-end",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(figure=fig_line, id="chart-1"),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.Span("分类销售额对比", className="me-auto"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(html.I(className="fas fa-ellipsis-v"), color="link", size="sm"),
                                                ],
                                                className="float-end",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(figure=fig_bar, id="chart-2"),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("分类占比"),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(figure=fig_pie, id="chart-3"),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("数据明细表"),
                                    dbc.CardBody(
                                        [
                                            create_table_from_dataframe(
                                                sample_data.head(10),
                                                striped=True,
                                                bordered=True,
                                                hover=True,
                                                responsive=True,
                                                className="table-sm",
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ],
                        width=8,
                    ),
                ]
            ),
        ],
        fluid=True,
    )

# ==========================================
# 设置页面
# ==========================================
def create_settings_page():
    """创建设置页面"""
    return dbc.Container(
        [
            html.H2("设置", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("通用设置"),
                                    dbc.CardBody(
                                        [
                                            html.Label("自动刷新间隔", className="form-label"),
                                            dbc.Select(
                                                id="refresh-interval",
                                                options=[
                                                    {"label": "关闭", "value": "off"},
                                                    {"label": "5 分钟", "value": "5"},
                                                    {"label": "10 分钟", "value": "10"},
                                                    {"label": "30 分钟", "value": "30"},
                                                    {"label": "1 小时", "value": "60"},
                                                ],
                                                value="off",
                                                className="mb-3",
                                            ),
                                            html.Label("默认图表主题", className="form-label"),
                                            dbc.Select(
                                                id="default-theme",
                                                options=[
                                                    {"label": "默认", "value": "default"},
                                                    {"label": "商务蓝", "value": "blue"},
                                                    {"label": "活力橙", "value": "orange"},
                                                    {"label": "自然绿", "value": "green"},
                                                ],
                                                value="default",
                                                className="mb-3",
                                            ),
                                            dbc.Button("保存设置", color="primary"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            
                            dbc.Card(
                                [
                                    dbc.CardHeader("数据源配置"),
                                    dbc.CardBody(
                                        [
                                            html.Label("导出配置", className="form-label"),
                                            dbc.Button("导出所有数据源配置", color="info", className="mb-3"),
                                            html.Label("导入配置", className="form-label"),
                                            dbc.Button("导入数据源配置", color="warning"),
                                        ]
                                    ),
                                ],
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )

# ==========================================
# 主布局
# ==========================================
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="datasource-save-success", data=False),  # 标记保存成功，用于关闭模态框
        create_sidebar(),
        html.Div(id="page-content", style=CONTENT_STYLE),
    ]
)

# ==========================================
# 路由回调
# ==========================================
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    """根据路径显示对应页面"""
    if pathname == "/datasource":
        return create_datasource_page()
    elif pathname == "/chart-designer":
        return create_chart_designer_page()
    elif pathname == "/dashboard":
        return create_dashboard_page()
    elif pathname == "/settings":
        return create_settings_page()
    else:
        # 默认跳转到仪表盘
        return create_dashboard_page()

# ==========================================
# 数据源管理回调函数
# ==========================================

@app.callback(
    Output("datasource-list", "children", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call='initial_duplicate'  # 允许初始调用和重复回调
)
def load_datasource_list(pathname):
    """页面加载时自动加载数据源列表"""
    if pathname == "/datasource":
        datasources = config_manager.load_datasources()
        return create_datasource_table(datasources)
    # 如果是其他页面，返回 no_update
    return dash.no_update

@app.callback(
    [Output("modal-datasource", "is_open", allow_duplicate=True),
     Output("datasource-tabs", "active_tab", allow_duplicate=True),
     Output("modal-datasource-header", "children", allow_duplicate=True),
     Output("current-datasource-id", "data", allow_duplicate=True),
     Output("current-uploaded-file", "data", allow_duplicate=True),
     Output("test-connection-status", "children", allow_duplicate=True)],
    [Input("btn-add-datasource", "n_clicks"),
     Input("btn-cancel-datasource", "n_clicks"),
     Input({"type": "edit-datasource", "index": ALL}, "n_clicks")],
    [State("modal-datasource", "is_open"),
     State("datasource-tabs", "active_tab"),
     State("current-datasource-id", "data"),
     State("current-uploaded-file", "data")],
    prevent_initial_call=True
)
def toggle_datasource_modal(open_clicks, close_clicks, edit_clicks, is_open, current_tab, current_id, current_file):
    """打开/关闭数据源配置模态框 - 只处理新增、取消、编辑按钮"""
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"]
    trigger_str = str(trigger_id)
    
    # 明确排除测试连接和保存按钮，这些按钮不应该触发这个回调
    if "btn-test-connection" in trigger_str or "btn-save-datasource" in trigger_str:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # 只处理特定按钮，明确检查按钮 ID
    # 新增数据源
    if trigger_str == "btn-add-datasource.n_clicks":
        return True, "tab-file", "新增数据源", None, None, ""
    
    # 取消按钮 - 关闭模态框
    elif trigger_str == "btn-cancel-datasource.n_clicks":
        return False, current_tab or "tab-file", "新增数据源", None, None, ""
    
    # 编辑数据源 - 检查是否是字典类型的 prop_id
    elif isinstance(trigger_id, dict):
        try:
            if trigger_id.get("type") == "edit-datasource" and "index" in trigger_id:
                datasource_id = trigger_id["index"]
                ds_config = config_manager.get_datasource(datasource_id)
                if ds_config:
                    ds_type = ds_config.get('type', 'file')
                    if ds_type == 'file':
                        tab = "tab-file"
                    elif ds_type == 'database':
                        tab = "tab-database"
                    else:
                        tab = "tab-api"
                    return True, tab, f"编辑数据源: {ds_config.get('name', 'Unnamed')}", datasource_id, None, ""
        except (KeyError, TypeError, AttributeError):
            pass
    
    # 其他所有情况都不处理，返回 no_update
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output("file-upload-status", "children"),
     Output("current-uploaded-file", "data"),
     Output("data-preview", "children", allow_duplicate=True)],
    Input("upload-file", "contents"),
    State("upload-file", "filename"),
    prevent_initial_call=True
)
def handle_file_upload(contents, filename):
    """处理文件上传"""
    if contents is None:
        return "", None, dash.no_update
    
    try:
        # 解析 base64 编码的文件
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # 保存文件
        file_path = UPLOAD_DIR / filename
        with open(file_path, 'wb') as f:
            f.write(decoded)
        
        # 读取数据预览
        try:
            df = load_from_file(str(file_path))
            
            # 获取字段信息
            schema_info = []
            for col in df.columns:
                dtype = df[col].dtype
                if pd.api.types.is_numeric_dtype(dtype):
                    schema_info.append(f"{col} (数值)")
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    schema_info.append(f"{col} (日期)")
                else:
                    schema_info.append(f"{col} (文本)")
            
            status_alert = dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    html.Strong("文件上传成功！"),
                    html.Br(),
                    html.Small(f"文件名：{filename}"),
                    html.Br(),
                    html.Small(f"数据量：{len(df)} 行 × {len(df.columns)} 列"),
                    html.Br(),
                    html.Small(f"字段：{', '.join(schema_info[:5])}{'...' if len(schema_info) > 5 else ''}")
                ],
                color="success",
                className="mt-2"
            )
            
            # 显示数据预览
            preview_table = create_table_from_dataframe(
                df.head(10),
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                className="table-sm"
            )
            
            return status_alert, filename, preview_table
            
        except Exception as e:
            error_alert = dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"文件解析失败：{str(e)}"
                ],
                color="danger",
                className="mt-2"
            )
            return error_alert, None, dash.no_update
    except Exception as e:
        error_alert = dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"上传失败：{str(e)}"
            ],
            color="danger",
            className="mt-2"
        )
        return error_alert, None, dash.no_update

@app.callback(
    [Output("datasource-list", "children"),
     Output("test-connection-status", "children"),
     Output("datasource-save-success", "data")],
    [Input("btn-save-datasource", "n_clicks"),
     Input("btn-test-connection", "n_clicks")],
    [State("datasource-tabs", "active_tab"),
     State("current-datasource-id", "data"),
     State("current-uploaded-file", "data"),
     State("upload-file", "filename"),
     State("datasource-name-file", "value"),
     State("db-type", "value"),
     State("db-host", "value"),
     State("db-port", "value"),
     State("db-database", "value"),
     State("db-user", "value"),
     State("db-password", "value"),
     State("db-sql", "value"),
     State("datasource-name-db", "value"),
     State("api-url", "value"),
     State("api-method", "value"),
     State("api-headers", "value"),
     State("api-params", "value"),
     State("datasource-name-api", "value")],
    prevent_initial_call=True
)
def save_datasource(test_clicks, save_clicks, active_tab, current_id, current_file, filename, name_file, 
                    db_type, db_host, db_port, db_database, db_user, db_password, db_sql, name_db,
                    api_url, api_method, api_headers, api_params, name_api):
    """保存或测试数据源配置"""
    ctx = callback_context
    if not ctx.triggered:
        datasources = config_manager.load_datasources()
        return create_datasource_table(datasources), "", False
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # 只处理测试连接和保存按钮，其他情况不处理
    if button_id not in ["btn-test-connection", "btn-save-datasource"]:
        datasources = config_manager.load_datasources()
        return create_datasource_table(datasources), "", False
    
    try:
        # 使用当前上传的文件名，如果没有则使用新的文件名
        used_filename = current_file or filename
        
        if active_tab == "tab-file":
            if not used_filename:
                datasources = config_manager.load_datasources()
                return create_datasource_table(datasources), dbc.Alert("请先上传文件", color="warning", className="m-3"), False
            
            file_path = str(UPLOAD_DIR / used_filename)
            name = name_file or used_filename.replace('.csv', '').replace('.xlsx', '').replace('.xls', '')
            
            if button_id == "btn-test-connection":
                try:
                    df = load_from_file(file_path)
                    adapter = DataSourceAdapter({"type": "file", "file_path": file_path})
                    schema = adapter.get_schema()
                    
                    fields_list = [
                        html.Li(f"{col['name']} ({col['type']})")
                        for col in schema['columns'][:10]
                    ]
                    if len(schema['columns']) > 10:
                        fields_list.append(html.Li("..."))
                    
                    fields_info = html.Ul(fields_list)
                    
                    status_msg = dbc.Alert(
                        [
                            html.I(className="fas fa-check-circle me-2"),
                            html.Strong("连接成功！"),
                            html.Br(),
                            html.Small(f"数据量：{len(df)} 行 × {len(df.columns)} 列"),
                            html.Hr(),
                            html.Strong("字段信息：", className="small"),
                            fields_info
                        ],
                        color="success",
                        className="m-3"
                    )
                    datasources = config_manager.load_datasources()
                    # 测试连接时保持模态框打开，不修改 is_open 状态
                    return create_datasource_table(datasources), status_msg, False
                except Exception as e:
                    datasources = config_manager.load_datasources()
                    # 测试连接失败时也保持模态框打开
                    return create_datasource_table(datasources), dbc.Alert(f"连接失败：{str(e)}", color="danger", className="m-3"), False
            
            config = {
                "type": "file",
                "name": name,
                "file_path": file_path
            }
            if current_id:
                config["id"] = current_id
            
        elif active_tab == "tab-database":
            if not all([db_host, db_database, db_user, db_password]):
                datasources = config_manager.load_datasources()
                return create_datasource_table(datasources), dbc.Alert("请填写完整的数据库信息", color="warning", className="m-3"), False
            
            name = name_db or f"{db_type}_{db_database}"
            port = int(db_port) if db_port else (5432 if db_type == "postgresql" else 3306)
            sql = db_sql or "SELECT * FROM table_name LIMIT 100"
            
            if button_id == "btn-test-connection":
                db_config = DBConfig(
                    engine=db_type,
                    host=db_host,
                    port=port,
                    user=db_user,
                    password=db_password,
                    database=db_database
                )
                try:
                    # 测试连接
                    load_from_database(db_config, "SELECT 1")
                    
                    # 测试 SQL 查询（如果提供了）
                    if sql and "SELECT" in sql.upper():
                        df = load_from_database(db_config, sql)
                        status_msg = dbc.Alert(
                            [
                                html.I(className="fas fa-check-circle me-2"),
                                html.Strong("数据库连接成功！"),
                                html.Br(),
                                html.Small(f"SQL 查询返回：{len(df)} 行 × {len(df.columns)} 列")
                            ],
                            color="success",
                            className="m-3"
                        )
                    else:
                        status_msg = dbc.Alert(
                            [
                                html.I(className="fas fa-check-circle me-2"),
                                html.Strong("数据库连接成功！")
                            ],
                            color="success",
                            className="m-3"
                        )
                    datasources = config_manager.load_datasources()
                    # 测试连接时保持模态框打开，不修改 is_open 状态
                    return create_datasource_table(datasources), status_msg, False
                except Exception as e:
                    datasources = config_manager.load_datasources()
                    # 测试连接失败时也保持模态框打开
                    return create_datasource_table(datasources), dbc.Alert(f"连接失败：{str(e)}", color="danger", className="m-3"), False
            
            config = {
                "type": "database",
                "name": name,
                "engine": db_type,
                "host": db_host,
                "port": port,
                "database": db_database,
                "user": db_user,
                "password": db_password,
                "sql": sql,
            }
            if current_id:
                config["id"] = current_id
            
        elif active_tab == "tab-api":
            if not api_url:
                datasources = config_manager.load_datasources()
                return create_datasource_table(datasources), dbc.Alert("请填写 API 地址", color="warning", className="m-3"), False
            
            name = name_api or "API数据源"
            headers = {}
            params = {}
            
            try:
                if api_headers:
                    headers = json.loads(api_headers)
            except json.JSONDecodeError:
                datasources = config_manager.load_datasources()
                return create_datasource_table(datasources), dbc.Alert("请求头格式错误，请输入有效的 JSON", color="danger", className="m-3"), False
            
            try:
                if api_params:
                    params = json.loads(api_params)
            except json.JSONDecodeError:
                datasources = config_manager.load_datasources()
                return create_datasource_table(datasources), dbc.Alert("请求参数格式错误，请输入有效的 JSON", color="danger", className="m-3"), False
            
            if button_id == "btn-test-connection":
                try:
                    df = load_from_api(api_url, method=api_method or "GET", 
                                     headers=headers if headers else None,
                                     params=params if params else None)
                    
                    adapter = DataSourceAdapter({"type": "api", "url": api_url})
                    schema = adapter.get_schema()
                    
                    status_msg = dbc.Alert(
                        [
                            html.I(className="fas fa-check-circle me-2"),
                            html.Strong("API 连接成功！"),
                            html.Br(),
                            html.Small(f"数据量：{len(df)} 行 × {len(df.columns)} 列"),
                            html.Br(),
                            html.Small(f"字段：{', '.join([col['name'] for col in schema['columns'][:5]])}{'...' if len(schema['columns']) > 5 else ''}")
                        ],
                        color="success",
                        className="m-3"
                    )
                    datasources = config_manager.load_datasources()
                    # 测试连接时保持模态框打开，不修改 is_open 状态
                    return create_datasource_table(datasources), status_msg, False
                except Exception as e:
                    datasources = config_manager.load_datasources()
                    # 测试连接失败时也保持模态框打开
                    return create_datasource_table(datasources), dbc.Alert(f"连接失败：{str(e)}", color="danger", className="m-3"), False
            
            config = {
                "type": "api",
                "name": name,
                "url": api_url,
                "method": api_method or "GET",
                "headers": headers,
                "params": params,
            }
            if current_id:
                config["id"] = current_id
        
        # 保存配置
        if button_id == "btn-save-datasource":
            config_manager.save_datasource(config)
            datasources = config_manager.load_datasources()
            # 保存成功提示
            return create_datasource_table(datasources), dbc.Alert("数据源保存成功！", color="success", className="m-3"), True
        
        # 测试连接后的状态返回
        datasources = config_manager.load_datasources()
        return create_datasource_table(datasources), "", False
        
    except Exception as e:
        datasources = config_manager.load_datasources()
        return create_datasource_table(datasources), dbc.Alert(f"操作失败：{str(e)}", color="danger", className="m-3"), False

@app.callback(
    [Output("modal-datasource", "is_open", allow_duplicate=True),
     Output("datasource-save-success", "data", allow_duplicate=True)],
    Input("datasource-save-success", "data"),
    prevent_initial_call=True
)
def close_modal_on_save(save_success):
    """保存成功后关闭模态框并重置标志"""
    if save_success:
        # 关闭模态框并重置标志
        return False, False
    return dash.no_update, dash.no_update

def create_datasource_table(datasources):
    """创建数据源列表表格"""
    if not datasources:
        return html.P("暂无数据源，请点击 '新增数据源' 添加", className="text-muted text-center py-5")
    
    rows = []
    for ds in datasources:
        status_color = "success" if ds.get('status') == 'connected' else "secondary"
        status_text = "已连接" if ds.get('status') == 'connected' else "未连接"
        ds_type = ds.get('type', 'unknown').upper()
        
        rows.append(
            html.Tr([
                html.Td(ds.get('name', 'Unnamed')),
                html.Td(html.Span(ds_type, className=f"badge bg-info")),
                html.Td(html.Span(status_text, className=f"badge bg-{status_color}")),
                html.Td(ds.get('updated_at', 'Unknown')[:19] if ds.get('updated_at') else 'Unknown'),
                html.Td([
                    dbc.Button("测试", size="sm", color="secondary", className="me-1", 
                             id={"type": "test-datasource", "index": ds.get('id')}),
                    dbc.Button("编辑", size="sm", color="warning", className="me-1",
                             id={"type": "edit-datasource", "index": ds.get('id')}),
                    dbc.Button("删除", size="sm", color="danger",
                             id={"type": "delete-datasource", "index": ds.get('id')}),
                ]),
            ])
        )
    
    return dbc.Table(
        [
            html.Thead(
                html.Tr([
                    html.Th("名称"),
                    html.Th("类型"),
                    html.Th("状态"),
                    html.Th("最后更新"),
                    html.Th("操作"),
                ])
            ),
            html.Tbody(rows),
        ],
        bordered=True,
        hover=True,
        responsive=True,
    )

@app.callback(
    [Output("data-preview", "children"),
     Output("datasource-list", "children", allow_duplicate=True)],
    [Input({"type": "test-datasource", "index": ALL}, "n_clicks"),
     Input({"type": "delete-datasource", "index": ALL}, "n_clicks")],
    prevent_initial_call=True
)
def handle_datasource_actions(test_clicks, delete_clicks):
    """处理数据源操作（测试/删除）"""
    ctx = callback_context
    if not ctx.triggered:
        return html.P("请选择一个数据源查看预览", className="text-muted text-center py-5"), dash.no_update
    
    button_info = ctx.triggered[0]["prop_id"]
    
    # 删除数据源
    if "delete-datasource" in str(button_info):
        datasource_id = button_info["index"]
        try:
            config_manager.delete_datasource(datasource_id)
            datasources = config_manager.load_datasources()
            table = create_datasource_table(datasources)
            return dbc.Alert("数据源已删除", color="success"), table
        except Exception as e:
            datasources = config_manager.load_datasources()
            table = create_datasource_table(datasources)
            return dbc.Alert(f"删除失败：{str(e)}", color="danger"), table
    
    # 测试/预览数据源
    elif "test-datasource" in str(button_info):
        datasource_id = button_info["index"]
        ds_config = config_manager.get_datasource(datasource_id)
        
        if not ds_config:
            return dbc.Alert("数据源不存在", color="danger"), dash.no_update
        
        try:
            adapter = DataSourceAdapter(ds_config)
            df = adapter.fetch_data(limit=100)
            
            if df.empty:
                return dbc.Alert("数据为空", color="warning"), dash.no_update
            
            # 显示更详细的信息
            schema = adapter.get_schema()
            info_card = dbc.Card(
                [
                    dbc.CardHeader([
                        html.Strong("数据预览"),
                        html.Span(f" {ds_config.get('name', 'Unnamed')}", className="text-muted")
                    ]),
                    dbc.CardBody([
                        html.P([
                            html.Strong("数据量："),
                            f"{schema.get('row_count', len(df))} 行 × {len(df.columns)} 列"
                        ], className="mb-2"),
                        html.P([
                            html.Strong("字段信息："),
                            html.Ul([
                                html.Li(f"{col['name']} ({col['type']})")
                                for col in schema.get('columns', [])[:10]
                            ])
                        ], className="mb-3"),
                        create_table_from_dataframe(
                            df.head(10),
                            striped=True,
                            bordered=True,
                            hover=True,
                            responsive=True,
                            className="table-sm"
                        )
                    ])
                ],
                className="mb-3"
            )
            return info_card, dash.no_update
        except Exception as e:
            return dbc.Alert(f"预览失败：{str(e)}", color="danger"), dash.no_update
    
    return html.P("请选择一个数据源查看预览", className="text-muted text-center py-5"), dash.no_update

@app.callback(
    [Output("upload-file", "filename", allow_duplicate=True),
     Output("datasource-name-file", "value", allow_duplicate=True),
     Output("db-type", "value", allow_duplicate=True),
     Output("db-host", "value", allow_duplicate=True),
     Output("db-port", "value", allow_duplicate=True),
     Output("db-database", "value", allow_duplicate=True),
     Output("db-user", "value", allow_duplicate=True),
     Output("db-password", "value", allow_duplicate=True),
     Output("db-sql", "value", allow_duplicate=True),
     Output("datasource-name-db", "value", allow_duplicate=True),
     Output("api-url", "value", allow_duplicate=True),
     Output("api-method", "value", allow_duplicate=True),
     Output("api-headers", "value", allow_duplicate=True),
     Output("api-params", "value", allow_duplicate=True),
     Output("datasource-name-api", "value", allow_duplicate=True),
     Output("current-uploaded-file", "data", allow_duplicate=True),
     Output("test-connection-status", "children", allow_duplicate=True)],
    Input("current-datasource-id", "data"),
    prevent_initial_call=True
)
def load_datasource_for_edit(datasource_id):
    """加载数据源配置到编辑表单"""
    if not datasource_id:
        # 清空表单
        return (None, None, "postgresql", None, None, None, None, None, 
                "SELECT * FROM table_name LIMIT 100", None, None, "GET", None, None, None, None, "")
    
    ds_config = config_manager.get_datasource(datasource_id)
    if not ds_config:
        return (None, None, "postgresql", None, None, None, None, None,
                "SELECT * FROM table_name LIMIT 100", None, None, "GET", None, None, None, None, "")
    
    ds_type = ds_config.get('type', 'file')
    
    if ds_type == 'file':
        file_path = ds_config.get('file_path', '')
        filename = Path(file_path).name if file_path else None
        return (
            filename,  # upload-file filename
            ds_config.get('name', ''),  # datasource-name-file
            "postgresql",  # db-type (default)
            None, None, None, None, None,  # db fields
            "SELECT * FROM table_name LIMIT 100",  # db-sql
            None,  # datasource-name-db
            None, None, None, None, None,  # api fields
            filename,  # current-uploaded-file
            ""  # test-connection-status
        )
    elif ds_type == 'database':
        return (
            None, None,  # file fields
            ds_config.get('engine', 'postgresql'),  # db-type
            ds_config.get('host', ''),  # db-host
            ds_config.get('port', 5432),  # db-port
            ds_config.get('database', ''),  # db-database
            ds_config.get('user', ''),  # db-user
            ds_config.get('password', ''),  # db-password
            ds_config.get('sql', 'SELECT * FROM table_name LIMIT 100'),  # db-sql
            ds_config.get('name', ''),  # datasource-name-db
            None, None, None, None, None,  # api fields
            None,  # current-uploaded-file
            ""  # test-connection-status
        )
    else:  # api
        headers = ds_config.get('headers', {})
        params = ds_config.get('params', {})
        return (
            None, None,  # file fields
            "postgresql", None, None, None, None, None,  # db fields
            "SELECT * FROM table_name LIMIT 100", None,  # db-sql, datasource-name-db
            ds_config.get('url', ''),  # api-url
            ds_config.get('method', 'GET'),  # api-method
            json.dumps(headers, indent=2) if headers else '',  # api-headers
            json.dumps(params, indent=2) if params else '',  # api-params
            ds_config.get('name', ''),  # datasource-name-api
            None,  # current-uploaded-file
            ""  # test-connection-status
        )

# ==========================================
# 图表设计器回调函数
# ==========================================

@app.callback(
    Output("chart-datasource-select", "options"),
    Input("url", "pathname")
)
def load_chart_datasource_options(pathname):
    """加载图表设计器的数据源选项"""
    if pathname == "/chart-designer":
        datasources = config_manager.load_datasources()
        options = [
            {"label": ds.get('name', 'Unnamed'), "value": ds.get('id')}
            for ds in datasources
        ]
        return options if options else [{"label": "请先添加数据源", "value": None}]
    return []

@app.callback(
    Output("chart-preview", "children"),
    [Input("chart-datasource-select", "value"),
     Input("chart-type", "value"),
     Input("drop-x-axis", "children"),
     Input("drop-y-axis", "children"),
     Input("drop-group", "children"),
     Input("agg-function", "value"),
     Input("chart-title", "value"),
     Input("color-theme", "value"),
     Input("chart-options", "value")],
    prevent_initial_call=False
)
def update_chart_preview(datasource_id, chart_type, x_axis, y_axis, group, 
                         agg_function, title, color_theme, options):
    """更新图表预览"""
    try:
        if not datasource_id:
            return html.P("请选择数据源", className="text-muted text-center py-5")
        
        # 获取数据源配置
        ds_config = config_manager.get_datasource(datasource_id)
        if not ds_config:
            return html.P("数据源不存在", className="text-muted text-center py-5")
        
        # 获取数据
        adapter = data_source_manager.get_adapter(datasource_id, ds_config)
        if not adapter:
            adapter = DataSourceAdapter(ds_config)
        
        df = adapter.fetch_data(limit=1000)
        
        if df is None or len(df) == 0:
            return html.P("数据为空，无法生成图表", className="text-muted text-center py-5")
        
        # 从拖拽区域提取字段名（简化处理）
        x_field = None
        y_field = None
        group_field = None
        
        # 尝试从 UI 组件中提取字段（简化版，实际需要更复杂的解析）
        # 这里假设用户已手动配置了字段
        schema = adapter.get_schema()
        available_fields = [col['name'] for col in schema['columns']]
        
        # 使用第一个日期字段作为 X 轴，第一个数值字段作为 Y 轴
        if chart_type in ['line', 'bar']:
            for col in schema['columns']:
                if col['type'] == 'date' and not x_field:
                    x_field = col['name']
                if col['type'] in ['numeric', 'integer'] and not y_field:
                    y_field = col['name']
                    break
        
        if not x_field or not y_field:
            # 如果没有找到合适的字段，使用示例数据
            if len(df.columns) >= 2:
                x_field = str(df.columns[0])
                if len(df.columns) >= 2 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
                    y_field = str(df.columns[1])
                elif len(df.columns) >= 3 and pd.api.types.is_numeric_dtype(df[df.columns[2]]):
                    y_field = str(df.columns[2])
                else:
                    y_field = None
        
        if x_field is None or y_field is None:
            return html.P("请配置 X 轴和 Y 轴字段", className="text-muted text-center py-5")
        
        # 构建图表配置
        chart_config = {
            "type": chart_type or "line",
            "x": x_field,
            "y": y_field,
            "group": group_field,
            "title": title or "图表预览",
            "color_theme": color_theme or "default",
            "show_labels": "show-labels" in (options or []),
            "show_legend": "show-legend" in (options or []),
            "agg_function": agg_function or "sum",
        }
        
        # 生成图表
        fig = chart_engine.create_chart(df, chart_config)
        
        return dcc.Graph(figure=fig, id="preview-chart")
        
    except Exception as e:
        return dbc.Alert(f"生成图表失败：{str(e)}", color="danger")

# ==========================================
# 仪表盘回调函数
# ==========================================

@app.callback(
    Output("custom-date-range", "style"),
    Input("time-filter", "value")
)
def toggle_custom_date_range(filter_value):
    """显示/隐藏自定义日期范围选择器"""
    if filter_value == "custom":
        return {"display": "block"}
    return {"display": "none"}

# ==========================================
# 启动应用
# ==========================================
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)

