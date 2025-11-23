"""
BI 数据可视化与分析平台
完整的 BI 数据可视化与分析平台，支持多数据源、图表生成、仪表盘管理
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL, clientside_callback, ClientsideFunction
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

# JavaScript拖拽功能代码
# type: ignore
DRAG_DROP_SCRIPT = """
<script>
// 拖拽功能实现
(function() {
    let draggedElement = null;
    
    // 延迟初始化，等待Dash应用加载完成
    function initDragDrop() {
        // 处理字段拖拽开始
        document.addEventListener('dragstart', function(e) {
            const field = e.target.closest('.draggable-field');
            if (field) {
                draggedElement = field;
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', '');
                field.style.opacity = '0.5';
            }
        }, true);
        
        // 处理拖拽结束
        document.addEventListener('dragend', function(e) {
            if (draggedElement) {
                draggedElement.style.opacity = '1';
                draggedElement = null;
            }
        }, true);
        
        // 处理放置区域的拖拽悬停
        document.addEventListener('dragover', function(e) {
            const dropZone = e.target.closest('.drop-zone');
            if (dropZone && draggedElement) {
                e.preventDefault();
                e.stopPropagation();
                e.dataTransfer.dropEffect = 'move';
                dropZone.style.backgroundColor = '#e3f2fd';
                dropZone.style.borderColor = '#2196f3';
            }
        }, true);
        
        // 处理离开放置区域
        document.addEventListener('dragleave', function(e) {
            const dropZone = e.target.closest('.drop-zone');
            if (dropZone) {
                dropZone.style.backgroundColor = '';
                dropZone.style.borderColor = '';
            }
        }, true);
        
        // 处理放置事件
        document.addEventListener('drop', function(e) {
            const dropZone = e.target.closest('.drop-zone');
            if (dropZone && draggedElement) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.style.backgroundColor = '';
                dropZone.style.borderColor = '';
                
                const fieldName = draggedElement.getAttribute('data-field');
                const targetId = dropZone.id;
                
                // 更新隐藏输入框的值
                const eventData = JSON.stringify({
                    field: fieldName,
                    target: targetId
                });
                
                // 使用Dash的方式更新输入框并触发回调
                const dndInput = document.getElementById('dnd-last-event');
                if (dndInput) {
                    // 创建一个唯一的时间戳，确保Dash检测到变化
                    const timestamp = Date.now();
                    const newValue = eventData + '|' + timestamp;
                    
                    // 使用原生输入值设置器来触发React的onChange（Dash使用React）
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(dndInput, newValue);
                    
                    // 触发input事件（React会监听这个事件）
                    const inputEvent = new Event('input', { bubbles: true, cancelable: true });
                    dndInput.dispatchEvent(inputEvent);
                    
                    // 触发change事件
                    const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                    dndInput.dispatchEvent(changeEvent);
                    
                    // 尝试触发React的合成事件（如果Dash使用React）
                    const syntheticInputEvent = new Event('input', { bubbles: true });
                    Object.defineProperty(syntheticInputEvent, 'target', {
                        writable: false,
                        value: dndInput
                    });
                    dndInput.dispatchEvent(syntheticInputEvent);
                    
                    // 如果有Dash的客户端回调API，直接调用
                    if (window.dash_clientside && typeof window.dash_clientside.call_clientside_callback === 'function') {
                        try {
                            // 尝试调用客户端回调
                            window.dash_clientside.call_clientside_callback('dnd-last-event', 'value', newValue);
                        } catch (e) {
                            console.log('Could not call dash clientside callback directly');
                        }
                    }
                    
                    // 额外尝试：直接通过Dash的Props设置（如果可用）
                    if (window.dash && window.dash.setProps) {
                        try {
                            window.dash.setProps('dnd-last-event', { value: newValue });
                        } catch (e) {
                            console.log('Could not use dash.setProps');
                        }
                    }
                    
                    console.log('Drag drop event sent:', eventData);
                }
                
                draggedElement = null;
            }
        }, true);
    }
    
    // 等待DOM和Dash加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDragDrop);
    } else {
        // DOM已经加载完成，延迟一点确保Dash也加载完成
        setTimeout(initDragDrop, 100);
    }
})();
</script>
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
        {DRAG_DROP_SCRIPT}
    </body>
</html>
"""

def default_chart_assignments() -> Dict[str, Any]:
    """获取图表字段配置的默认结构"""
    return {"x": None, "y": [], "group": None, "table_columns": [], "table_rows": [], "table_orientation": "horizontal"}


def render_assigned_fields(value: Optional[Any], placeholder: str, multiple: bool = False):
    """根据当前字段配置渲染拖拽区域内容"""
    if multiple:
        items = value if isinstance(value, list) else ([] if value is None else [value])
    else:
        items = [value] if value else []
    if not items:
        return html.P(placeholder, className="text-muted text-center mb-0")
    badges = [
        dbc.Badge(
            str(item),
            color="secondary",
            pill=True,
            className="me-2 mb-2"
        )
        for item in items
    ]
    wrapper_class = "d-flex flex-wrap" if multiple and len(badges) > 1 else None
    return html.Div(badges, className=wrapper_class)

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
                            dcc.Store(id="chart-field-assignments", data=default_chart_assignments()),
                            dcc.Store(id="custom-colors-config", data={}),  # 存储自定义颜色配置
                            dcc.Input(id="dnd-last-event", type="text", value="", style={"display": "none"}),
            
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
                                                options=[],
                                                value=None,
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
                                                html.P("请选择数据源后查看字段", className="text-muted mb-0"),
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
                            
                            # 拖拽配置区 - 图表类型配置
                            html.Div(id="chart-config-area", children=[
                                dbc.Card(
                                    [
                                        dbc.CardHeader("图表配置"),
                                        dbc.CardBody(
                                            [
                                                # 普通图表配置（折线图、柱状图等）
                                                html.Div(id="chart-config-normal", children=[
                                                    html.Div(
                                                        [
                                                            # X 轴配置（饼图时隐藏）
                                                            html.Div(id="x-axis-config", children=[
                                                                html.Div(
                                                                    [
                                                                        html.Label("X 轴", className="form-label fw-bold mb-0"),
                                                                        dbc.Button("清空", id="btn-clear-x-axis", color="link", size="sm", className="p-0 ms-2"),
                                                                    ],
                                                                    className="d-flex align-items-center mb-2"
                                                                ),
                                                                html.Div(
                                                                    id="drop-x-axis",
                                                                    children=[
                                                                        html.P("拖拽字段到此处", className="text-muted text-center mb-0"),
                                                                    ],
                                                                    style={
                                                                        "min-height": "60px",
                                                                        "margin-bottom": "15px",
                                                                        "border": "2px dashed #ced4da",
                                                                        "borderRadius": "6px",
                                                                        "padding": "0.5rem"
                                                                    },
                                                                    className="drop-zone",
                                                                ),
                                                            ]),
                                                            # Y 轴配置（饼图时显示为"数值字段"）
                                                            html.Div(
                                                                [
                                                                    html.Label(id="y-axis-label", children="Y 轴", className="form-label fw-bold mb-0"),
                                                                    dbc.Button("清空", id="btn-clear-y-axis", color="link", size="sm", className="p-0 ms-2"),
                                                                ],
                                                                className="d-flex align-items-center mb-2"
                                                            ),
                                                            html.P(id="y-axis-hint", children="拖拽字段到此处", className="text-muted text-center mb-2 small"),
                                                            html.Div(
                                                                id="drop-y-axis",
                                                                children=[
                                                                    html.P("拖拽字段到此处", className="text-muted text-center mb-0"),
                                                                ],
                                                                style={
                                                                    "min-height": "60px",
                                                                    "margin-bottom": "15px",
                                                                    "border": "2px dashed #ced4da",
                                                                    "borderRadius": "6px",
                                                                    "padding": "0.5rem"
                                                                },
                                                                className="drop-zone",
                                                            ),
                                                            # 分组配置（饼图时显示为"分类字段（必需）"）
                                                            html.Div(
                                                                [
                                                                    html.Label(id="group-label", children="分组/颜色", className="form-label fw-bold mb-0"),
                                                                    dbc.Button("清空", id="btn-clear-group", color="link", size="sm", className="p-0 ms-2"),
                                                                ],
                                                                className="d-flex align-items-center mb-2"
                                                            ),
                                                            html.P(id="group-hint", children="拖拽字段到此处", className="text-muted text-center mb-2 small"),
                                                            html.Div(
                                                                id="drop-group",
                                                                children=[
                                                                    html.P("拖拽字段到此处", className="text-muted text-center mb-0"),
                                                                ],
                                                                style={
                                                                    "min-height": "60px",
                                                                    "margin-bottom": "15px",
                                                                    "border": "2px dashed #ced4da",
                                                                    "borderRadius": "6px",
                                                                    "padding": "0.5rem"
                                                                },
                                                                className="drop-zone",
                                                            ),
                                                        ]
                                                    ),
                                                ]),
                                                # 表格配置
                                                html.Div(id="chart-config-table", children=[
                                                    html.Div(
                                                        [
                                                            html.Label("展示方向", className="form-label fw-bold mb-2"),
                                                            dbc.RadioItems(
                                                                id="table-orientation",
                                                                options=[
                                                                    {"label": "横向展示（字段为列）", "value": "horizontal"},
                                                                    {"label": "纵向展示（字段为行）", "value": "vertical"},
                                                                ],
                                                                value="horizontal",
                                                                inline=False,
                                                            ),
                                                        ],
                                                        className="mb-3"
                                                    ),
                                                    html.Div(id="table-columns-config", children=[
                                                        html.Label("表格列配置", className="form-label fw-bold mb-2"),
                                                        html.P("拖拽字段到下方列区域以设置表格列", className="text-muted small mb-2"),
                                                        html.Div(id="table-columns-list", children=[
                                                            html.P("拖拽字段到此处作为第1列", className="text-muted text-center mb-2 small"),
                                                            html.Div(
                                                                id="drop-table-col-1",
                                                                children=[
                                                                    html.P("拖拽字段到此处", className="text-muted text-center mb-0"),
                                                                ],
                                                                style={
                                                                    "min-height": "50px",
                                                                    "margin-bottom": "10px",
                                                                    "border": "2px dashed #ced4da",
                                                                    "borderRadius": "6px",
                                                                    "padding": "0.5rem"
                                                                },
                                                                className="drop-zone",
                                                            ),
                                                        ]),
                                                        dbc.Button("添加列", id="btn-add-table-column", color="link", size="sm", className="p-0 mt-2"),
                                                    ]),
                                                    html.Div(id="table-rows-config", style={"display": "none"}, children=[
                                                        html.Label("表格行配置", className="form-label fw-bold mb-2"),
                                                        html.P("拖拽字段到下方行区域以设置表格行", className="text-muted small mb-2"),
                                                        html.Div(id="table-rows-list", children=[
                                                            html.P("拖拽字段到此处作为第1行", className="text-muted text-center mb-2 small"),
                                                            html.Div(
                                                                id="drop-table-row-1",
                                                                children=[
                                                                    html.P("拖拽字段到此处", className="text-muted text-center mb-0"),
                                                                ],
                                                                style={
                                                                    "min-height": "50px",
                                                                    "margin-bottom": "10px",
                                                                    "border": "2px dashed #ced4da",
                                                                    "borderRadius": "6px",
                                                                    "padding": "0.5rem"
                                                                },
                                                                className="drop-zone",
                                                            ),
                                                        ]),
                                                        dbc.Button("添加行", id="btn-add-table-row", color="link", size="sm", className="p-0 mt-2"),
                                                    ]),
                                                ]),
                                            ]
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                            ]),
                            
                            # 聚合函数（非表格图表使用）
                            html.Div(id="agg-function-card", children=[
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
                            ]),
                            
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
                                            # 自定义颜色配置（仅在有分组字段时显示）
                                            html.Div(id="custom-colors-section", children=[
                                                html.Hr(className="my-3"),
                                                html.Label("自定义颜色（每个分组使用不同颜色）", className="form-label fw-bold"),
                                                html.P("当有分组字段时，可以为每个分组设置自定义颜色。颜色将自动确保不重复。", className="text-muted small mb-3"),
                                                html.Div(id="custom-colors-list", children=[
                                                    html.P("请先设置分组字段", className="text-muted text-center py-3"),
                                                ]),
                                            ], style={"display": "none"}),
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
                                                    dbc.Button("保存图表", id="btn-save-chart", color="success", size="sm"),
                                                    dbc.Button("导出图片", id="btn-export-chart-image", color="info", size="sm"),
                                                ],
                                                className="float-end",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.CardBody(
                                        [
                                            # 保存当前图表配置的Store
                                            dcc.Store(id="current-chart-config", data=None),
                                            dcc.Store(id="current-chart-figure", data=None),
                                            html.Div(id="chart-save-status", children=[], className="mb-2"),
                                            html.Div(id="chart-preview", children=[
                                                html.P("请选择数据源并配置字段以生成预览", className="text-muted text-center py-5"),
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
    return dbc.Container(
        [
            # Store组件：存储当前选中的仪表盘ID和仪表盘配置
            dcc.Store(id="current-dashboard-id", data=None),
            dcc.Store(id="current-dashboard-config", data=None),
            dcc.Store(id="dashboard-refresh-trigger", data=0),
            
            # 顶部工具栏
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div([
                                html.H2(id="dashboard-title", children="我的仪表盘", className="mb-0 d-inline-block me-3"),
                                dbc.Select(
                                    id="dashboard-selector",
                                    placeholder="选择或创建仪表盘...",
                                    className="d-inline-block",
                                    style={"width": "300px", "verticalAlign": "middle"},
                                ),
                            ]),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.ButtonGroup(
                                [
                                    dbc.Button([html.I(className="fas fa-plus me-1"), "新建仪表盘"], 
                                              id="btn-new-dashboard", color="primary", size="sm"),
                                    dbc.Button([html.I(className="fas fa-edit me-1"), "编辑"], 
                                              id="btn-edit-dashboard", color="secondary", size="sm"),
                                    dbc.Button([html.I(className="fas fa-trash me-1"), "删除"], 
                                              id="btn-delete-dashboard", color="danger", size="sm"),
                                    dbc.Button([html.I(className="fas fa-plus me-1"), "添加图表"], 
                                              id="btn-add-chart-to-dashboard", color="success", size="sm"),
                                    dbc.DropdownMenu(
                                        [
                                            dbc.DropdownMenuItem("导出为 PNG", id="btn-export-dashboard-png"),
                                            dbc.DropdownMenuItem("导出为 PDF", id="btn-export-dashboard-pdf"),
                                            dbc.DropdownMenuItem("导出为 HTML", id="btn-export-dashboard-html"),
                                        ],
                                        label="导出",
                                        size="sm",
                                        color="info",
                                    ),
                                ],
                                className="float-end",
                            ),
                        ],
                        width=4,
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
            
            # 仪表盘图表区域
            html.Div(id="dashboard-charts-container", children=[
                html.P("请选择或创建一个仪表盘", className="text-muted text-center py-5"),
            ]),
            
            # 新建/编辑仪表盘模态框
            dbc.Modal(
                [
                    dbc.ModalHeader(id="dashboard-modal-header", children="新建仪表盘"),
                    dbc.ModalBody(
                        [
                            html.Label("仪表盘名称", className="form-label"),
                            dbc.Input(id="dashboard-name-input", placeholder="请输入仪表盘名称", className="mb-3"),
                            html.Label("描述", className="form-label"),
                            dbc.Textarea(id="dashboard-description-input", placeholder="请输入描述（可选）", rows=3),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("取消", id="btn-cancel-dashboard-modal", color="secondary", className="me-2"),
                            dbc.Button("保存", id="btn-save-dashboard-modal", color="primary"),
                        ]
                    ),
                ],
                id="modal-dashboard",
                is_open=False,
                size="lg",
            ),
            
            # 添加图表到仪表盘模态框
            dbc.Modal(
                [
                    dbc.ModalHeader("添加图表到仪表盘"),
                    dbc.ModalBody(
                        [
                            html.Label("选择图表", className="form-label"),
                            dbc.Select(id="chart-selector-for-dashboard", className="mb-3"),
                            html.Div(id="dashboard-add-chart-status", children=[]),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("取消", id="btn-cancel-add-chart", color="secondary", className="me-2"),
                            dbc.Button("添加", id="btn-confirm-add-chart", color="primary"),
                        ]
                    ),
                ],
                id="modal-add-chart-to-dashboard",
                is_open=False,
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
    
    triggered = ctx.triggered[0]["prop_id"]
    try:
        trigger_id = json.loads(triggered.split(".")[0])
    except json.JSONDecodeError:
        return dbc.Alert("操作标识解析失败", color="danger"), dash.no_update
    action_type = trigger_id.get("type")
    datasource_id = trigger_id.get("index")

    # 删除数据源
    if action_type == "delete-datasource":
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
    elif action_type == "test-datasource":
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
    [Output("chart-datasource-select", "options"),
     Output("chart-datasource-select", "value")],
    Input("url", "pathname")
)
def load_chart_datasource_options(pathname):
    """加载图表设计器的数据源选项"""
    if pathname == "/chart-designer":
        datasources = config_manager.load_datasources()
        options = [
            {"label": ds.get('name', 'Unnamed'), "value": ds.get('id')}
            for ds in datasources if ds.get('id')
        ]
        selected = options[0]["value"] if options else None
        if not options:
            options = [{"label": "请先添加数据源", "value": None, "disabled": True}]
        return options, selected
    return [], None


@app.callback(
    [Output("field-list", "children"),
     Output("chart-field-assignments", "data", allow_duplicate=True)],
    Input("chart-datasource-select", "value"),
    prevent_initial_call="initial_duplicate"
)
def load_datasource_fields(datasource_id):
    """根据数据源加载可拖拽字段列表"""
    assignments = default_chart_assignments()
    if not datasource_id:
        return html.P("请选择数据源后查看字段", className="text-muted mb-0"), assignments
    try:
        ds_config = config_manager.get_datasource(datasource_id)
        if not ds_config:
            return html.P("数据源不存在", className="text-danger mb-0"), assignments
        adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
        schema = adapter.get_schema()
        columns = schema.get('columns', []) if isinstance(schema, dict) else []
        if not columns:
            return html.P("未检测到字段，请检查数据源配置", className="text-muted mb-0"), assignments
        type_labels = {
            'date': '日期',
            'datetime64[ns]': '日期',
            'numeric': '数值',
            'integer': '整数',
            'text': '文本'
        }
        type_colors = {
            'date': 'primary',
            'datetime64[ns]': 'primary',
            'numeric': 'success',
            'integer': 'success',
            'text': 'info'
        }
        badges: List[Any] = []
        for col in columns:
            col_name = col.get('name')
            if not col_name:
                continue
            col_type = col.get('type', 'text')
            label = type_labels.get(col_type, '字段')
            color_class = type_colors.get(col_type, 'secondary')
            badge = html.Span(
                f"{col_name} ({label})",
                className=f"badge rounded-pill bg-{color_class} me-2 mb-2 draggable-field",
                style={"cursor": "grab"},
                **{"data-field": col_name, "data-type": col_type, "draggable": "true"}
            )
            badges.append(badge)
        if not badges:
            return html.P("未检测到字段，请检查数据源", className="text-muted mb-0"), assignments
        return html.Div(badges, className="d-flex flex-wrap"), assignments
    except Exception as exc:
        return dbc.Alert(f"加载字段失败：{exc}", color="danger"), assignments


@app.callback(
    [Output("chart-config-normal", "style"),
     Output("chart-config-table", "style"),
     Output("agg-function-card", "style"),
     Output("x-axis-config", "style"),
     Output("y-axis-label", "children"),
     Output("y-axis-hint", "children"),
     Output("group-label", "children"),
     Output("group-hint", "children")],
    Input("chart-type", "value")
)
def toggle_chart_config(chart_type):
    """根据图表类型显示/隐藏不同的配置界面，并调整标签文字"""
    if chart_type == "table":
        return {"display": "none"}, {"display": "block"}, {"display": "none"}, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    elif chart_type == "pie":
        # 饼图：隐藏 X 轴，调整 Y 轴和分组标签
        return (
            {"display": "block"},  # chart-config-normal
            {"display": "none"},   # chart-config-table
            {"display": "block"},  # agg-function-card
            {"display": "none"},   # x-axis-config (隐藏 X 轴)
            "数值字段（必需）",                      # y-axis-label
            "提示：拖拽数值字段到下方区域",          # y-axis-hint
            "分类字段（必需）",                      # group-label
            "提示：拖拽分类字段到下方区域"           # group-hint
        )
    else:
        # 其他图表类型：显示所有配置
        return (
            {"display": "block"},  # chart-config-normal
            {"display": "none"},   # chart-config-table
            {"display": "block"},  # agg-function-card
            {"display": "block"},  # x-axis-config (显示 X 轴)
            "Y 轴",                           # y-axis-label
            "提示：拖拽字段到下方区域",        # y-axis-hint
            "分组/颜色",                      # group-label
            "提示：拖拽字段到下方区域"         # group-hint
        )

@app.callback(
    [Output("table-columns-config", "style"),
     Output("table-rows-config", "style"),
     Output("chart-field-assignments", "data", allow_duplicate=True)],
    Input("table-orientation", "value"),
    State("chart-field-assignments", "data"),
    prevent_initial_call='initial_duplicate'
)
def toggle_table_orientation(orientation, assignments):
    """根据表格方向显示列或行配置，并更新assignments"""
    assignments = assignments or default_chart_assignments()
    new_assignments = {
        'x': assignments.get('x'),
        'y': list(assignments.get('y', [])),
        'group': assignments.get('group'),
        'table_columns': list(assignments.get('table_columns', [])),
        'table_rows': list(assignments.get('table_rows', [])),
        'table_orientation': orientation if orientation else 'horizontal'
    }
    
    if orientation == "horizontal":
        return {"display": "block"}, {"display": "none"}, new_assignments
    else:
        return {"display": "none"}, {"display": "block"}, new_assignments

@app.callback(
    [Output("drop-x-axis", "children"),
     Output("drop-y-axis", "children"),
     Output("drop-group", "children")],
    [Input("chart-field-assignments", "data"),
     Input("chart-type", "value")],
    prevent_initial_call=False
)
def sync_drop_zones(assignments, chart_type):
    """根据字段配置更新拖拽区域显示（非表格图表）"""
    if chart_type == "table":
        return dash.no_update, dash.no_update, dash.no_update
    assignments = assignments or default_chart_assignments()
    return (
        render_assigned_fields(assignments.get('x'), "拖拽字段到此处"),
        render_assigned_fields(assignments.get('y'), "拖拽字段到此处", multiple=True),
        render_assigned_fields(assignments.get('group'), "拖拽字段到此处"),
    )

@app.callback(
    [Output("custom-colors-section", "style"),
     Output("custom-colors-list", "children")],
    [Input("chart-field-assignments", "data"),
     Input("chart-datasource-select", "value"),
     Input("chart-type", "value")],
    State("custom-colors-config", "data"),
    prevent_initial_call=False
)
def update_custom_colors_ui(assignments, datasource_id, chart_type, custom_colors):
    """根据分组字段显示自定义颜色配置界面"""
    assignments = assignments or default_chart_assignments()
    group_field = assignments.get('group')
    
    # 如果没有分组字段，隐藏自定义颜色界面
    if not group_field or chart_type == "table":
        return {"display": "none"}, html.P("请先设置分组字段", className="text-muted text-center py-3")
    
    if not datasource_id:
        return {"display": "none"}, html.P("请先选择数据源", className="text-muted text-center py-3")
    
    try:
        # 获取数据源配置并加载数据
        from config_manager import ConfigManager
        from data_adapter import DataSourceAdapter, DataSourceManager
        config_manager = ConfigManager()
        data_source_manager = DataSourceManager()
        
        ds_config = config_manager.get_datasource(datasource_id)
        if not ds_config:
            return {"display": "none"}, html.P("数据源不存在", className="text-muted text-center py-3")
        
        adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
        df = adapter.fetch_data(limit=1000)
        
        if df is None or df.empty or group_field not in df.columns:
            return {"display": "none"}, html.P("无法加载分组数据", className="text-muted text-center py-3")
        
        # 获取唯一的分组值
        unique_groups = sorted(df[group_field].dropna().unique().tolist())
        custom_colors = custom_colors or {}
        
        # 为每个分组创建颜色选择器
        color_inputs = []
        default_colors = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]
        
        for i, group_val in enumerate(unique_groups):
            group_val_str = str(group_val)
            current_color = custom_colors.get(group_val_str, default_colors[i % len(default_colors)])
            
            color_inputs.append(
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Label(f"{group_val}", className="form-label mb-1 small"),
                        ], width=4),
                        dbc.Col([
                            dbc.Input(
                                id={"type": "custom-color-input", "group": group_val_str},
                                type="color",
                                value=current_color,
                                className="form-control form-control-color",
                                style={"width": "100%", "height": "38px"}
                            ),
                        ], width=6),
                        dbc.Col([
                            html.Div(
                                current_color,
                                id={"type": "color-value-display", "group": group_val_str},
                                className="small text-muted mt-2"
                            ),
                        ], width=2),
                    ], className="align-items-center mb-2"),
                ])
            )
        
        return {"display": "block"}, html.Div(color_inputs)
    
    except Exception as e:
        return {"display": "none"}, html.P(f"加载分组数据失败：{str(e)}", className="text-danger text-center py-3")

@app.callback(
    [Output("custom-colors-config", "data", allow_duplicate=True),
     Output({"type": "color-value-display", "group": ALL}, "children", allow_duplicate=True)],
    Input({"type": "custom-color-input", "group": ALL}, "value"),
    State("custom-colors-config", "data"),
    State({"type": "custom-color-input", "group": ALL}, "id"),
    prevent_initial_call=True
)
def update_custom_colors(color_values, current_colors, color_ids):
    """更新自定义颜色配置"""
    if not callback_context.triggered:
        raise dash.exceptions.PreventUpdate
    
    ctx = callback_context
    current_colors = current_colors or {}
    new_colors = current_colors.copy()
    
    # 更新颜色值
    for i, color_id in enumerate(color_ids):
        if i < len(color_values):
            group_val = color_id.get('group', '')
            if group_val and color_values[i]:
                new_colors[group_val] = color_values[i]
    
    # 更新显示的颜色值
    display_values = [new_colors.get(id.get('group', ''), '#000000') for id in color_ids]
    
    return new_colors, display_values


@app.callback(
    Output("chart-field-assignments", "data", allow_duplicate=True),
    Input("dnd-last-event", "value"),
    State("chart-field-assignments", "data"),
    prevent_initial_call=True
)
def handle_drag_drop_event(event_payload, assignments):
    """处理前端拖拽事件，更新字段配置"""
    if not event_payload:
        raise dash.exceptions.PreventUpdate
    
    # 处理带时间戳的事件数据
    event_str = event_payload
    if '|' in event_str:
        event_str = event_str.split('|')[0]
    
    try:
        event = json.loads(event_str)
    except json.JSONDecodeError:
        raise dash.exceptions.PreventUpdate
    
    field = event.get('field')
    target = event.get('target')
    
    assignments = assignments or default_chart_assignments()
    new_assignments = {
        'x': assignments.get('x'),
        'y': list(assignments.get('y', [])),
        'group': assignments.get('group'),
        'table_columns': list(assignments.get('table_columns', [])),
        'table_rows': list(assignments.get('table_rows', [])),
        'table_orientation': assignments.get('table_orientation', 'horizontal')
    }
    
    # 处理表格列/行的拖拽
    if target and target.startswith('drop-table-col-'):
        # 拖拽到表格列
        col_index_str = target.replace('drop-table-col-', '')
        try:
            col_index = int(col_index_str)  # 1-based索引（第几列）
            # 如果字段已存在，先移除
            if field in new_assignments['table_columns']:
                new_assignments['table_columns'].remove(field)
            # 插入或追加到指定位置
            col_pos = col_index - 1  # 转换为0-based索引
            if col_pos < len(new_assignments['table_columns']):
                new_assignments['table_columns'].insert(col_pos, field)
            else:
                new_assignments['table_columns'].append(field)
        except (ValueError, IndexError):
            pass
        return new_assignments
    elif target and target.startswith('drop-table-row-'):
        # 拖拽到表格行
        row_index_str = target.replace('drop-table-row-', '')
        try:
            row_index = int(row_index_str)  # 1-based索引（第几行）
            # 如果字段已存在，先移除
            if field in new_assignments['table_rows']:
                new_assignments['table_rows'].remove(field)
            # 插入或追加到指定位置
            row_pos = row_index - 1  # 转换为0-based索引
            if row_pos < len(new_assignments['table_rows']):
                new_assignments['table_rows'].insert(row_pos, field)
            else:
                new_assignments['table_rows'].append(field)
        except (ValueError, IndexError):
            pass
        return new_assignments
    
    # 处理普通图表的拖拽
    if not field or target not in {'drop-x-axis', 'drop-y-axis', 'drop-group'}:
        raise dash.exceptions.PreventUpdate
    
    if new_assignments.get('x') == field:
        new_assignments['x'] = None
    if field in new_assignments.get('y', []):
        new_assignments['y'] = [item for item in new_assignments['y'] if item != field]
    if new_assignments.get('group') == field:
        new_assignments['group'] = None
    if target == 'drop-x-axis':
        new_assignments['x'] = field
    elif target == 'drop-y-axis':
        if field not in new_assignments['y']:
            new_assignments['y'].append(field)
    elif target == 'drop-group':
        new_assignments['group'] = field
    return new_assignments


@app.callback(
    Output("chart-field-assignments", "data", allow_duplicate=True),
    [Input("btn-clear-x-axis", "n_clicks"),
     Input("btn-clear-y-axis", "n_clicks"),
     Input("btn-clear-group", "n_clicks")],
    State("chart-field-assignments", "data"),
    prevent_initial_call=True
)
def clear_axis_assignments(clear_x, clear_y, clear_group, assignments):
    """支持手动清空某个轴的字段配置"""
    if not callback_context.triggered:
        raise dash.exceptions.PreventUpdate
    triggered = callback_context.triggered[0]['prop_id'].split('.')[0]
    assignments = assignments or default_chart_assignments()
    new_assignments = {
        'x': assignments.get('x'),
        'y': list(assignments.get('y', [])),
        'group': assignments.get('group')
    }
    if triggered == "btn-clear-x-axis":
        new_assignments['x'] = None
    elif triggered == "btn-clear-y-axis":
        new_assignments['y'] = []
    elif triggered == "btn-clear-group":
        new_assignments['group'] = None
    else:
        raise dash.exceptions.PreventUpdate
    return new_assignments


@app.callback(
    [Output("table-columns-list", "children", allow_duplicate=True),
     Output("table-rows-list", "children", allow_duplicate=True)],
    [Input("chart-field-assignments", "data"),
     Input("chart-type", "value"),
     Input("btn-add-table-column", "n_clicks"),
     Input("btn-add-table-row", "n_clicks")],
    State("table-columns-list", "children"),
    prevent_initial_call=True
)
def sync_table_columns_rows(assignments, chart_type, add_col_clicks, add_row_clicks, current_cols_list):
    """同步表格列/行的显示"""
    ctx = callback_context
    if not ctx.triggered or chart_type != "table":
        return dash.no_update, dash.no_update
    
    assignments = assignments or default_chart_assignments()
    table_columns = assignments.get('table_columns', [])
    table_rows = assignments.get('table_rows', [])
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # 处理添加列/行按钮
    if trigger_id == "btn-add-table-column":
        # 添加新的列拖拽区域
        new_col_index = len(table_columns) + 1
        col_div = html.Div([
            html.P(f"拖拽字段到此处作为第{new_col_index}列", className="text-muted text-center mb-2 small"),
            html.Div(
                id={"type": "drop-table-col", "index": new_col_index},
                children=[html.P("拖拽字段到此处", className="text-muted text-center mb-0")],
                style={
                    "min-height": "50px",
                    "margin-bottom": "10px",
                    "border": "2px dashed #ced4da",
                    "borderRadius": "6px",
                    "padding": "0.5rem"
                },
                className="drop-zone",
            ),
        ])
        if not current_cols_list:
            current_cols_list = []
        current_cols_list.append(col_div)
        return current_cols_list, dash.no_update
    
    elif trigger_id == "btn-add-table-row":
        # 添加新的行拖拽区域
        new_row_index = len(table_rows) + 1
        row_div = html.Div([
            html.P(f"拖拽字段到此处作为第{new_row_index}行", className="text-muted text-center mb-2 small"),
            html.Div(
                id={"type": "drop-table-row", "index": new_row_index},
                children=[html.P("拖拽字段到此处", className="text-muted text-center mb-0")],
                style={
                    "min-height": "50px",
                    "margin-bottom": "10px",
                    "border": "2px dashed #ced4da",
                    "borderRadius": "6px",
                    "padding": "0.5rem"
                },
                className="drop-zone",
            ),
        ])
        return dash.no_update, [row_div]
    
    # 根据配置更新列/行显示
    cols_list = []
    for i, col in enumerate(table_columns):
        cols_list.append(html.Div([
            html.P(f"第{i+1}列: {col}", className="text-muted text-center mb-2 small"),
            html.Div(
                id=f"drop-table-col-{i+1}",
                children=[dbc.Badge(col, color="secondary", pill=True)],
                style={
                    "min-height": "50px",
                    "margin-bottom": "10px",
                    "border": "2px dashed #ced4da",
                    "borderRadius": "6px",
                    "padding": "0.5rem"
                },
                className="drop-zone",
            ),
        ]))
    # 总是添加一个空列区域，用于添加新列
    cols_list.append(html.Div([
        html.P(f"拖拽字段到此处作为第{len(table_columns)+1}列", className="text-muted text-center mb-2 small"),
        html.Div(
            id=f"drop-table-col-{len(table_columns)+1}",
            children=[html.P("拖拽字段到此处", className="text-muted text-center mb-0")],
            style={
                "min-height": "50px",
                "margin-bottom": "10px",
                "border": "2px dashed #ced4da",
                "borderRadius": "6px",
                "padding": "0.5rem"
            },
            className="drop-zone",
        ),
    ]))
    
    rows_list = []
    for i, row in enumerate(table_rows):
        rows_list.append(html.Div([
            html.P(f"第{i+1}行: {row}", className="text-muted text-center mb-2 small"),
            html.Div(
                id=f"drop-table-row-{i+1}",
                children=[dbc.Badge(row, color="secondary", pill=True)],
                style={
                    "min-height": "50px",
                    "margin-bottom": "10px",
                    "border": "2px dashed #ced4da",
                    "borderRadius": "6px",
                    "padding": "0.5rem"
                },
                className="drop-zone",
            ),
        ]))
    # 总是添加一个空行区域，用于添加新行
    rows_list.append(html.Div([
        html.P(f"拖拽字段到此处作为第{len(table_rows)+1}行", className="text-muted text-center mb-2 small"),
        html.Div(
            id=f"drop-table-row-{len(table_rows)+1}",
            children=[html.P("拖拽字段到此处", className="text-muted text-center mb-0")],
            style={
                "min-height": "50px",
                "margin-bottom": "10px",
                "border": "2px dashed #ced4da",
                "borderRadius": "6px",
                "padding": "0.5rem"
            },
            className="drop-zone",
        ),
    ]))
    
    return cols_list, rows_list

@app.callback(
    Output("chart-preview", "children"),
    [Input("chart-datasource-select", "value"),
     Input("chart-type", "value"),
     Input("chart-field-assignments", "data"),
     Input("agg-function", "value"),
     Input("chart-title", "value"),
     Input("color-theme", "value"),
     Input("chart-options", "value"),
     Input("table-orientation", "value"),
     Input("custom-colors-config", "data")],
    prevent_initial_call=False
)
def update_chart_preview(datasource_id, chart_type, assignments, agg_function, title, color_theme, options, table_orientation, custom_colors):
    """根据当前配置生成预览图表"""
    try:
        if not datasource_id:
            return html.P("请选择数据源", className="text-muted text-center py-5")
        ds_config = config_manager.get_datasource(datasource_id)
        if not ds_config:
            return html.P("数据源不存在", className="text-muted text-center py-5")
        adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
        df = adapter.fetch_data(limit=1000)
        if df is None or df.empty:
            return html.P("数据为空，无法生成图表", className="text-muted text-center py-5")
        assignments = assignments or default_chart_assignments()
        options = options or []
        
        if chart_type == 'table':
            # 表格类型：使用列或行配置
            table_columns = assignments.get('table_columns', []) if assignments else []
            table_rows = assignments.get('table_rows', []) if assignments else []
            # 使用最新的表格方向设置
            if table_orientation:
                # 更新assignments中的方向
                if assignments:
                    assignments['table_orientation'] = table_orientation
            else:
                table_orientation = assignments.get('table_orientation', 'horizontal') if assignments else 'horizontal'
            
            if table_orientation == 'horizontal':
                # 横向展示：使用列配置
                if not table_columns:
                    return html.P("请拖拽字段到表格列区域", className="text-muted text-center py-5")
                # 选择指定的列
                selected_columns = [col for col in table_columns if col in df.columns]
                if not selected_columns:
                    return html.P("所选字段不存在于数据中", className="text-muted text-center py-5")
                # 确保返回DataFrame（使用列表选择确保始终返回DataFrame，即使只有一个列）
                result = df[selected_columns]
                if isinstance(result, pd.Series):
                    table_df: pd.DataFrame = result.to_frame()
                else:
                    table_df = result
                # 确保是DataFrame类型
                assert isinstance(table_df, pd.DataFrame), "table_df must be a DataFrame"
            else:
                # 纵向展示：使用行配置（转置数据）
                if not table_rows:
                    return html.P("请拖拽字段到表格行区域", className="text-muted text-center py-5")
                selected_rows = [row for row in table_rows if row in df.columns]
                if not selected_rows:
                    return html.P("所选字段不存在于数据中", className="text-muted text-center py-5")
                # 转置数据，确保返回DataFrame
                transposed = df[selected_rows].T
                if isinstance(transposed, pd.Series):
                    table_df = transposed.to_frame()
                else:
                    table_df = transposed
                # 确保是DataFrame类型
                assert isinstance(table_df, pd.DataFrame), "table_df must be a DataFrame"
                table_df.columns = [f'行{i+1}' for i in range(len(table_df.columns))]
            
            chart_config = {
                "type": "table",
                "title": title or "数据表格",
                "limit": 100,
            }
            fig = chart_engine.create_chart(table_df, chart_config)
            return dcc.Graph(figure=fig, id="preview-chart")
        else:
            # 普通图表类型：使用X轴/Y轴配置
            x_field = assignments.get('x')
            y_fields = assignments.get('y') or []
            group_field = assignments.get('group')
            
            if chart_type != 'pie' and not x_field:
                return html.P("请将字段拖拽到 X 轴", className="text-muted text-center py-5")
            if not y_fields:
                return html.P("请至少选择一个 Y 轴字段", className="text-muted text-center py-5")
            if chart_type == 'pie':
                if not group_field and not x_field:
                    return html.P("饼图需要分组字段", className="text-muted text-center py-5")
                if not y_fields:
                    return html.P("饼图需要一个数值字段", className="text-muted text-center py-5")
                if not group_field:
                    group_field = x_field
            
            chart_config = {
                "type": chart_type or "line",
                "x": x_field,
                "y": y_fields if len(y_fields) > 1 else (y_fields[0] if y_fields else None),
                "group": group_field,
                "title": title or "图表预览",
                "color_theme": color_theme or "default",
                "custom_colors": custom_colors or {},
                "show_labels": "show-labels" in options,
                "show_legend": "show-legend" in options,
                "agg_function": agg_function or "sum",
            }
            fig = chart_engine.create_chart(df, chart_config)
            return dcc.Graph(figure=fig, id="preview-chart")
    except Exception as e:
        return dbc.Alert(f"生成图表失败：{str(e)}", color="danger")

@app.callback(
    [Output("current-chart-config", "data", allow_duplicate=True),
     Output("chart-save-status", "children", allow_duplicate=True)],
    [Input("btn-save-chart", "n_clicks")],
    [State("chart-datasource-select", "value"),
     State("chart-type", "value"),
     State("chart-field-assignments", "data"),
     State("agg-function", "value"),
     State("chart-title", "value"),
     State("color-theme", "value"),
     State("chart-options", "value"),
     State("custom-colors-config", "data")],
    prevent_initial_call=True
)
def save_chart(save_clicks, datasource_id, chart_type, assignments, agg_function, title, color_theme, options, custom_colors):
    """保存图表配置"""
    if not datasource_id:
        return dash.no_update, dbc.Alert("请先选择数据源", color="warning", className="m-2")
    try:
        ds_config = config_manager.get_datasource(datasource_id)
        if not ds_config:
            return dash.no_update, dbc.Alert("数据源不存在", color="warning", className="m-2")
        adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
        df = adapter.fetch_data(limit=1000)
        if df is None or df.empty:
            return dash.no_update, dbc.Alert("数据为空", color="warning", className="m-2")
        assignments = assignments or default_chart_assignments()
        x_field = assignments.get('x')
        y_fields = assignments.get('y') or []
        if chart_type != 'table' and not x_field and chart_type != 'pie':
            return dash.no_update, dbc.Alert("请将字段拖拽到 X 轴", color="warning", className="m-2")
        if not y_fields:
            return dash.no_update, dbc.Alert("请至少选择一个 Y 轴字段", color="warning", className="m-2")
        options = options or []
        chart_config = {
            "datasource_id": datasource_id,
            "type": chart_type or "line",
            "x": x_field,
            "y": y_fields if len(y_fields) > 1 else (y_fields[0] if y_fields else None),
            "group": assignments.get('group'),
            "title": title or "图表预览",
            "color_theme": color_theme or "default",
            "custom_colors": custom_colors or {},
            "show_labels": "show-labels" in options,
            "show_legend": "show-legend" in options,
            "agg_function": agg_function or "sum",
        }
        chart_config['name'] = title or "未命名图表"
        config_manager.save_chart(chart_config)
        return chart_config, dbc.Alert("图表保存成功！", color="success", className="m-2")
    except Exception as e:
        return dash.no_update, dbc.Alert(f"保存图表失败：{str(e)}", color="danger", className="m-2")

@app.callback(
    Output("chart-save-status", "children", allow_duplicate=True),
    [Input("btn-export-chart-image", "n_clicks"),
     Input("export-png", "n_clicks"),
     Input("export-pdf", "n_clicks"),
     Input("export-html", "n_clicks")],
    [State("chart-datasource-select", "value"),
     State("chart-type", "value"),
     State("chart-field-assignments", "data"),
     State("agg-function", "value"),
     State("chart-title", "value"),
     State("color-theme", "value"),
     State("chart-options", "value"),
     State("custom-colors-config", "data")],
    prevent_initial_call=True
)
def export_chart(png_clicks, png_dropdown, pdf_clicks, html_clicks, 
                 datasource_id, chart_type, assignments, agg_function, title, color_theme, options, custom_colors):
    """导出图表"""
    ctx = callback_context
    if not ctx.triggered or not datasource_id:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    try:
        ds_config = config_manager.get_datasource(datasource_id)
        if not ds_config:
            return dbc.Alert("数据源不存在", color="warning", className="m-2")
        adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
        df = adapter.fetch_data(limit=1000)
        if df is None or df.empty:
            return dbc.Alert("数据为空", color="warning", className="m-2")
        assignments = assignments or default_chart_assignments()
        x_field = assignments.get('x')
        y_fields = assignments.get('y') or []
        group_field = assignments.get('group')
        options = options or []
        chart_config = {
            "type": chart_type or "line",
            "x": x_field,
            "y": y_fields if len(y_fields) > 1 else (y_fields[0] if y_fields else None),
            "group": group_field,
            "title": title or "图表",
            "color_theme": color_theme or "default",
            "custom_colors": custom_colors or {},
            "show_labels": "show-labels" in options,
            "show_legend": "show-legend" in options,
            "agg_function": agg_function or "sum",
        }
        if chart_type == 'table':
            chart_config['limit'] = 100
        fig = chart_engine.create_chart(df, chart_config)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_title = (title or "chart").replace(" ", "_").replace("/", "_")
        
        if trigger_id in ["btn-export-chart-image", "export-png"]:
            # 导出为PNG
            export_path = EXPORT_DIR / f"{chart_title}_{timestamp}.png"
            fig.write_image(str(export_path), width=1200, height=600)
            return dbc.Alert(f"图表已导出为PNG：{export_path}", color="success", className="m-2")
        
        elif trigger_id == "export-pdf":
            # 导出为PDF
            export_path = EXPORT_DIR / f"{chart_title}_{timestamp}.pdf"
            fig.write_image(str(export_path), format="pdf", width=1200, height=600)
            return dbc.Alert(f"图表已导出为PDF：{export_path}", color="success", className="m-2")
        
        elif trigger_id == "export-html":
            # 导出为HTML
            export_path = EXPORT_DIR / f"{chart_title}_{timestamp}.html"
            fig.write_html(str(export_path))
            return dbc.Alert(f"图表已导出为HTML：{export_path}", color="success", className="m-2")
        
        return dash.no_update
    except Exception as e:
        error_msg = str(e)
        if "kaleido" in error_msg.lower() or "orca" in error_msg.lower():
            return dbc.Alert("导出图片需要安装kaleido包。请运行: pip install kaleido", color="warning", className="m-2")
        return dbc.Alert(f"导出图表失败：{error_msg}", color="danger", className="m-2")

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
# 仪表盘回调函数
# ==========================================

@app.callback(
    [Output("dashboard-selector", "options"),
     Output("dashboard-selector", "value")],
    [Input("url", "pathname"),
     Input("dashboard-refresh-trigger", "data")],
    prevent_initial_call=False
)
def load_dashboard_list(pathname, refresh_trigger):
    """加载仪表盘列表"""
    if pathname == "/dashboard":
        dashboards = config_manager.load_dashboards()
        options = [
            {"label": db.get('name', '未命名仪表盘'), "value": db.get('id')}
            for db in dashboards if db.get('id')
        ]
        selected = options[0]["value"] if options else None
        if not options:
            options = [{"label": "暂无仪表盘，请创建", "value": None, "disabled": True}]
        return options, selected
    return [], None

@app.callback(
    [Output("current-dashboard-id", "data"),
     Output("current-dashboard-config", "data"),
     Output("dashboard-title", "children")],
    Input("dashboard-selector", "value"),
    prevent_initial_call=False
)
def select_dashboard(dashboard_id):
    """选择仪表盘"""
    if not dashboard_id:
        return None, None, "我的仪表盘"
    
    dashboard = config_manager.get_dashboard(dashboard_id)
    if dashboard:
        return dashboard_id, dashboard, dashboard.get('name', '我的仪表盘')
    return None, None, "我的仪表盘"

@app.callback(
    Output("dashboard-charts-container", "children"),
    [Input("current-dashboard-config", "data"),
     Input("time-filter", "value"),
     Input("start-date", "date"),
     Input("end-date", "date")],
    prevent_initial_call=False
)
def render_dashboard_charts(dashboard_config, time_filter, start_date, end_date):
    """渲染仪表盘中的图表"""
    if not dashboard_config:
        return html.P("请选择或创建一个仪表盘", className="text-muted text-center py-5")
    
    chart_ids = dashboard_config.get('chart_ids', [])
    if not chart_ids:
        return html.P("该仪表盘还没有添加图表，请点击\"添加图表\"按钮添加", className="text-muted text-center py-5")
    
    charts = config_manager.load_charts()
    chart_map = {chart.get('id'): chart for chart in charts if chart.get('id')}
    
    rows = []
    current_row = []
    
    for i, chart_id in enumerate(chart_ids):
        chart_config = chart_map.get(chart_id)
        if not chart_config:
            continue
        
        # 获取图表配置
        datasource_id = chart_config.get('datasource_id')
        chart_type = chart_config.get('type', 'line')
        
        if not datasource_id:
            continue
        
        try:
            # 加载数据
            ds_config = config_manager.get_datasource(datasource_id)
            if not ds_config:
                continue
            
            adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
            df = adapter.fetch_data(limit=1000)
            
            if df is None or df.empty:
                continue
            
            # 应用时间筛选（如果有时间字段）
            if time_filter and time_filter != "custom":
                # 这里可以根据实际需求实现时间筛选逻辑
                pass
            
            # 生成图表
            chart_config_for_engine = {
                "type": chart_type,
                "x": chart_config.get('x'),
                "y": chart_config.get('y'),
                "group": chart_config.get('group'),
                "title": chart_config.get('title', chart_config.get('name', '图表')),
                "color_theme": chart_config.get('color_theme', 'default'),
                "custom_colors": chart_config.get('custom_colors', {}),
                "show_labels": chart_config.get('show_labels', False),
                "show_legend": chart_config.get('show_legend', True),
                "agg_function": chart_config.get('agg_function', 'sum'),
            }
            
            fig = chart_engine.create_chart(df, chart_config_for_engine)
            
            # 确定图表宽度（可以根据配置或默认值）
            chart_width = chart_config.get('width', 6)  # 默认6列（Bootstrap 12列系统）
            
            chart_card = dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.Span(chart_config.get('title', chart_config.get('name', '图表')), className="me-auto"),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                html.I(className="fas fa-times"),
                                                id={"type": "remove-chart-from-dashboard", "chart_id": chart_id},
                                                color="link",
                                                size="sm",
                                                className="text-danger"
                                            ),
                                        ],
                                        className="float-end",
                                    ),
                                ],
                                className="d-flex justify-content-between align-items-center",
                            ),
                            dbc.CardBody(
                                [
                                    dcc.Graph(figure=fig, id={"type": "dashboard-chart", "chart_id": chart_id}),
                                ]
                            ),
                        ],
                        className="mb-3",
                    ),
                ],
                width=chart_width,
            )
            
            current_row.append(chart_card)
            
            # 每行最多12列，如果当前行已满或这是最后一个图表，创建新行
            if sum(c.width for c in current_row) >= 12 or i == len(chart_ids) - 1:
                rows.append(dbc.Row(current_row, className="mb-3"))
                current_row = []
        
        except Exception as e:
            # 如果图表生成失败，显示错误信息
            error_card = dbc.Col(
                [
                    dbc.Alert(f"图表加载失败：{str(e)}", color="danger"),
                ],
                width=12,
            )
            current_row.append(error_card)
            if sum(c.width for c in current_row) >= 12:
                rows.append(dbc.Row(current_row, className="mb-3"))
                current_row = []
    
    if not rows:
        return html.P("无法加载图表，请检查数据源配置", className="text-muted text-center py-5")
    
    return rows

@app.callback(
    [Output("modal-dashboard", "is_open"),
     Output("dashboard-modal-header", "children"),
     Output("dashboard-name-input", "value"),
     Output("dashboard-description-input", "value")],
    [Input("btn-new-dashboard", "n_clicks"),
     Input("btn-edit-dashboard", "n_clicks"),
     Input("btn-cancel-dashboard-modal", "n_clicks"),
     Input("btn-save-dashboard-modal", "n_clicks")],
    [State("modal-dashboard", "is_open"),
     State("current-dashboard-config", "data"),
     State("dashboard-name-input", "value"),
     State("dashboard-description-input", "value")],
    prevent_initial_call=True
)
def toggle_dashboard_modal(new_clicks, edit_clicks, cancel_clicks, save_clicks, is_open, current_dashboard, name, description):
    """打开/关闭仪表盘编辑模态框"""
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id in ["btn-new-dashboard", "btn-edit-dashboard"]:
        if trigger_id == "btn-new-dashboard":
            return True, "新建仪表盘", "", ""
        else:
            if current_dashboard:
                return True, "编辑仪表盘", current_dashboard.get('name', ''), current_dashboard.get('description', '')
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    elif trigger_id == "btn-cancel-dashboard-modal":
        return False, dash.no_update, dash.no_update, dash.no_update
    
    elif trigger_id == "btn-save-dashboard-modal":
        return False, dash.no_update, dash.no_update, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output("dashboard-refresh-trigger", "data", allow_duplicate=True),
     Output("current-dashboard-id", "data", allow_duplicate=True),
     Output("current-dashboard-config", "data", allow_duplicate=True)],
    Input("btn-save-dashboard-modal", "n_clicks"),
    [State("current-dashboard-id", "data"),
     State("dashboard-name-input", "value"),
     State("dashboard-description-input", "value")],
    prevent_initial_call=True
)
def save_dashboard(save_clicks, current_id, name, description):
    """保存仪表盘"""
    if not name:
        return dash.no_update, dash.no_update, dash.no_update
    
    dashboard_config = {
        "name": name,
        "description": description or "",
        "chart_ids": [],
    }
    
    if current_id:
        dashboard_config["id"] = current_id
        existing = config_manager.get_dashboard(current_id)
        if existing:
            dashboard_config["chart_ids"] = existing.get('chart_ids', [])
    
    config_manager.save_dashboard(dashboard_config)
    saved_id = dashboard_config.get('id')
    
    # 刷新仪表盘列表
    return dash.callback_context.triggered[0]["value"] + 1 if dash.callback_context.triggered else 1, saved_id, dashboard_config

@app.callback(
    [Output("dashboard-refresh-trigger", "data", allow_duplicate=True),
     Output("current-dashboard-id", "data", allow_duplicate=True),
     Output("current-dashboard-config", "data", allow_duplicate=True)],
    Input("btn-delete-dashboard", "n_clicks"),
    State("current-dashboard-id", "data"),
    prevent_initial_call=True
)
def delete_dashboard(delete_clicks, dashboard_id):
    """删除仪表盘"""
    if not dashboard_id:
        return dash.no_update, dash.no_update, dash.no_update
    
    dashboards = config_manager.load_dashboards()
    dashboards = [db for db in dashboards if db.get('id') != dashboard_id]
    
    with open(config_manager.dashboards_file, 'w', encoding='utf-8') as f:
        json.dump({'dashboards': dashboards}, f, indent=2, ensure_ascii=False)
    
    return dash.callback_context.triggered[0]["value"] + 1 if dash.callback_context.triggered else 1, None, None

@app.callback(
    [Output("modal-add-chart-to-dashboard", "is_open"),
     Output("chart-selector-for-dashboard", "options")],
    [Input("btn-add-chart-to-dashboard", "n_clicks"),
     Input("btn-cancel-add-chart", "n_clicks"),
     Input("btn-confirm-add-chart", "n_clicks")],
    [State("modal-add-chart-to-dashboard", "is_open"),
     State("chart-selector-for-dashboard", "value"),
     State("current-dashboard-config", "data")],
    prevent_initial_call=True
)
def toggle_add_chart_modal(add_clicks, cancel_clicks, confirm_clicks, is_open, selected_chart_id, dashboard_config):
    """打开/关闭添加图表模态框"""
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "btn-add-chart-to-dashboard":
        # 加载图表列表
        charts = config_manager.load_charts()
        options = [
            {"label": chart.get('name', chart.get('title', '未命名图表')), "value": chart.get('id')}
            for chart in charts if chart.get('id')
        ]
        if not options:
            options = [{"label": "暂无可用图表，请先创建图表", "value": None, "disabled": True}]
        return True, options
    
    elif trigger_id == "btn-cancel-add-chart":
        return False, dash.no_update
    
    elif trigger_id == "btn-confirm-add-chart":
        if selected_chart_id and dashboard_config:
            chart_ids = dashboard_config.get('chart_ids', [])
            if selected_chart_id not in chart_ids:
                chart_ids.append(selected_chart_id)
                dashboard_config['chart_ids'] = chart_ids
                config_manager.save_dashboard(dashboard_config)
        return False, dash.no_update
    
    return dash.no_update, dash.no_update

@app.callback(
    [Output("dashboard-refresh-trigger", "data", allow_duplicate=True),
     Output("current-dashboard-config", "data", allow_duplicate=True)],
    Input({"type": "remove-chart-from-dashboard", "chart_id": ALL}, "n_clicks"),
    State("current-dashboard-config", "data"),
    prevent_initial_call=True
)
def remove_chart_from_dashboard(remove_clicks, dashboard_config):
    """从仪表盘中移除图表"""
    if not dashboard_config or not any(remove_clicks):
        return dash.no_update, dash.no_update
    
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    # 获取被点击的图表ID
    trigger_id = ctx.triggered[0]["prop_id"]
    if "chart_id" in trigger_id:
        # 从JSON字符串中提取chart_id
        import json
        try:
            chart_id_dict = json.loads(trigger_id.split(".")[0])
            chart_id = chart_id_dict.get("chart_id")
            
            chart_ids = dashboard_config.get('chart_ids', [])
            if chart_id in chart_ids:
                chart_ids.remove(chart_id)
                dashboard_config['chart_ids'] = chart_ids
                config_manager.save_dashboard(dashboard_config)
                return dash.callback_context.triggered[0]["value"] + 1 if dash.callback_context.triggered else 1, dashboard_config
        except:
            pass
    
    return dash.no_update, dash.no_update

@app.callback(
    Output("dashboard-charts-container", "children", allow_duplicate=True),
    [Input("btn-export-dashboard-png", "n_clicks"),
     Input("btn-export-dashboard-pdf", "n_clicks"),
     Input("btn-export-dashboard-html", "n_clicks")],
    [State("current-dashboard-config", "data"),
     State("dashboard-charts-container", "children")],
    prevent_initial_call=True
)
def export_dashboard(png_clicks, pdf_clicks, html_clicks, dashboard_config, current_charts):
    """导出仪表盘"""
    ctx = callback_context
    if not ctx.triggered or not dashboard_config:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    try:
        chart_ids = dashboard_config.get('chart_ids', [])
        if not chart_ids:
            return html.Div([
                dbc.Alert("该仪表盘没有图表，无法导出", color="warning", className="m-2"),
            ])
        
        charts = config_manager.load_charts()
        chart_map = {chart.get('id'): chart for chart in charts if chart.get('id')}
        
        # 收集所有图表
        figures = []
        for chart_id in chart_ids:
            chart_config = chart_map.get(chart_id)
            if not chart_config:
                continue
            
            datasource_id = chart_config.get('datasource_id')
            if not datasource_id:
                continue
            
            try:
                ds_config = config_manager.get_datasource(datasource_id)
                if not ds_config:
                    continue
                
                adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
                df = adapter.fetch_data(limit=1000)
                
                if df is None or df.empty:
                    continue
                
                chart_config_for_engine = {
                    "type": chart_config.get('type', 'line'),
                    "x": chart_config.get('x'),
                    "y": chart_config.get('y'),
                    "group": chart_config.get('group'),
                    "title": chart_config.get('title', chart_config.get('name', '图表')),
                    "color_theme": chart_config.get('color_theme', 'default'),
                    "custom_colors": chart_config.get('custom_colors', {}),
                    "show_labels": chart_config.get('show_labels', False),
                    "show_legend": chart_config.get('show_legend', True),
                    "agg_function": chart_config.get('agg_function', 'sum'),
                }
                
                fig = chart_engine.create_chart(df, chart_config_for_engine)
                figures.append(fig)
            except Exception as e:
                continue
        
        if not figures:
            return html.Div([
                dbc.Alert("无法生成图表，请检查数据源配置", color="danger", className="m-2"),
            ])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dashboard_name = (dashboard_config.get('name', 'dashboard')).replace(" ", "_").replace("/", "_")
        
        if trigger_id == "btn-export-dashboard-png":
            if figures:
                export_path = EXPORT_DIR / f"{dashboard_name}_{timestamp}.png"
                figures[0].write_image(str(export_path), width=1200, height=600)
                return html.Div([
                    dbc.Alert(f"仪表盘已导出为PNG：{export_path}", color="success", className="m-2"),
                    current_charts if current_charts else html.P("请选择或创建一个仪表盘", className="text-muted text-center py-5"),
                ])
        
        elif trigger_id == "btn-export-dashboard-pdf":
            if figures:
                export_path = EXPORT_DIR / f"{dashboard_name}_{timestamp}.pdf"
                figures[0].write_image(str(export_path), format="pdf", width=1200, height=600)
                return html.Div([
                    dbc.Alert(f"仪表盘已导出为PDF：{export_path}", color="success", className="m-2"),
                    current_charts if current_charts else html.P("请选择或创建一个仪表盘", className="text-muted text-center py-5"),
                ])
        
        elif trigger_id == "btn-export-dashboard-html":
            export_path = EXPORT_DIR / f"{dashboard_name}_{timestamp}.html"
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{dashboard_config.get('name', '仪表盘')}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>{dashboard_config.get('name', '仪表盘')}</h1>
    <p>{dashboard_config.get('description', '')}</p>
"""
            for i, fig in enumerate(figures):
                chart_html = fig.to_html(include_plotlyjs=False, div_id=f"chart-{i}")
                html_content += f'<div id="chart-{i}"></div>\n'
                html_content += f'<script>{chart_html}</script>\n'
            
            html_content += """</body>
</html>"""
            
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return html.Div([
                dbc.Alert(f"仪表盘已导出为HTML：{export_path}", color="success", className="m-2"),
                current_charts if current_charts else html.P("请选择或创建一个仪表盘", className="text-muted text-center py-5"),
            ])
        
        return dash.no_update
    
    except Exception as e:
        return html.Div([
            dbc.Alert(f"导出失败：{str(e)}", color="danger", className="m-2"),
            current_charts if current_charts else html.P("请选择或创建一个仪表盘", className="text-muted text-center py-5"),
        ])

# ==========================================
# 启动应用
# ==========================================
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)

