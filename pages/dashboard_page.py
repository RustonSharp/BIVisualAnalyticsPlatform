"""仪表盘页面模块"""
import dash
from dash import dcc, html, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, cast
import pandas as pd
from plotly.subplots import make_subplots

from data_adapter import DataSourceAdapter
from tools.export_utils import (
    export_dashboard_to_html,
    export_dashboard_to_png,
    export_dashboard_to_pdf,
)


def create_dashboard_page():
    """创建仪表盘页面"""
    return dbc.Container(
        [
            # Store组件：存储当前选中的仪表盘ID和仪表盘配置
            dcc.Store(id="current-dashboard-id", data=None),
            dcc.Store(id="current-dashboard-config", data=None),
            dcc.Store(id="dashboard-refresh-trigger", data=0),
            dcc.Store(id="export-status-message", data=None),  # 存储导出状态消息和时间戳
            dcc.Interval(id="export-status-interval", interval=100, disabled=True),  # 用于定时清除消息
            dcc.Store(id="chart-filter-state", data=None),  # 存储图表联动筛选条件 {source_chart_id, field, value}
            dcc.Store(id="chart-data-cache", data={}),  # 缓存每个图表的原始数据，用于筛选
            
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
                                    dbc.Button([html.I(className="fas fa-filter me-1"), "清除筛选"], 
                                              id="btn-clear-chart-filter", color="warning", size="sm", outline=True, 
                                              style={"display": "none"}),
                                    dbc.Button([html.I(className="fas fa-share-alt me-1"), "分享链接"], 
                                              id="btn-share-dashboard", color="primary", size="sm", outline=True),
                                    dbc.ButtonGroup([
                                        dbc.Button([html.I(className="fas fa-image me-1"), "PNG"], 
                                                  id="btn-export-dashboard-png", color="info", size="sm", outline=True),
                                        dbc.Button([html.I(className="fas fa-file-pdf me-1"), "PDF"], 
                                                  id="btn-export-dashboard-pdf", color="info", size="sm", outline=True),
                                        dbc.Button([html.I(className="fas fa-file-code me-1"), "HTML"], 
                                                  id="btn-export-dashboard-html", color="info", size="sm", outline=True),
                                    ]),
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
                                            html.Div([
                                                html.Label("时间范围", className="form-label d-inline-block me-3"),
                                                html.Div(id="chart-filter-status", className="d-inline-block me-3"),
                                            ], className="mb-2"),
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
            
            # 分享链接模态框
            dbc.Modal(
                [
                    dbc.ModalHeader("分享仪表盘链接"),
                    dbc.ModalBody(
                        [
                            html.P("复制下面的链接分享给其他人，他们可以直接访问此仪表盘：", className="mb-3"),
                            dbc.InputGroup(
                                [
                                    dbc.Input(id="share-link-input", readonly=True, value=""),
                                    dbc.Button(
                                        [html.I(className="fas fa-copy me-1"), "复制"],
                                        id="btn-copy-share-link",
                                        color="primary",
                                        outline=True
                                    ),
                                ],
                                className="mb-3"
                            ),
                            html.Div(id="share-link-copy-status", children=[]),
                            html.Hr(),
                            html.P([
                                html.Strong("提示："), " 分享的链接包含当前仪表盘的ID，访问者将看到相同的仪表盘内容。",
                            ], className="text-muted small mb-0"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("关闭", id="btn-close-share-modal", color="secondary"),
                        ]
                    ),
                ],
                id="modal-share-dashboard",
                is_open=False,
            ),
        ],
        fluid=True,
    )


def register_dashboard_callbacks(app, config_manager, data_source_manager, chart_engine, export_dir):
    """注册仪表盘页面的所有回调函数"""
    from components.common import default_chart_assignments
    
    @app.callback(
        Output("custom-date-range", "style"),
        Input("time-filter", "value")
    )
    def toggle_custom_date_range(filter_value):
        """显示/隐藏自定义日期范围选择器"""
        if filter_value == "custom":
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(
        [Output("dashboard-selector", "options"),
         Output("dashboard-selector", "value")],
        [Input("url", "pathname"),
         Input("url", "search"),
         Input("dashboard-refresh-trigger", "data")],
        prevent_initial_call=False
    )
    def load_dashboard_list(pathname, search, refresh_trigger):
        """加载仪表盘列表"""
        if pathname == "/dashboard":
            dashboards = config_manager.load_dashboards()
            options = [
                {"label": db.get('name', '未命名仪表盘'), "value": db.get('id')}
                for db in dashboards if db.get('id')
            ]
            
            # 从URL参数中获取dashboard_id
            selected = None
            if search:
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(f"?{search}" if not search.startswith('?') else search)
                params = parse_qs(parsed.query)
                if 'dashboard_id' in params and params['dashboard_id']:
                    dashboard_id_from_url = params['dashboard_id'][0]
                    # 验证该ID是否存在于仪表盘列表中
                    if any(opt['value'] == dashboard_id_from_url for opt in options):
                        selected = dashboard_id_from_url
            
            # 如果没有从URL获取到，使用第一个
            if not selected:
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
         Input("end-date", "date"),
         Input("export-status-message", "data"),
         Input("chart-filter-state", "data")],
        [State("chart-data-cache", "data")],
        prevent_initial_call=False
    )
    def render_dashboard_charts(dashboard_config, time_filter, start_date, end_date, export_status, filter_state, data_cache):
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
        error_count = 0
        total_charts = len(chart_ids)
        
        for i, chart_id in enumerate(chart_ids):
            chart_config = chart_map.get(chart_id)
            if not chart_config:
                error_card = dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.H5(f"图表 {chart_id}", className="mb-0 d-inline-block"),
                                dbc.Button(
                                    [html.I(className="fas fa-times")],
                                    id={"type": "remove-chart-from-dashboard", "chart_id": chart_id},
                                    color="link",
                                    size="sm",
                                    className="float-end",
                                ),
                            ],
                            className="d-flex justify-content-between align-items-center",
                        ),
                        dbc.CardBody(
                            dbc.Alert(f"图表配置不存在（ID: {chart_id}），请检查图表配置", color="warning")
                        ),
                    ],
                    className="mb-3",
                )
                current_row.append(dbc.Col(error_card, width=6))
                error_count += 1
                if len(current_row) == 2 or i == len(chart_ids) - 1:
                    rows.append(dbc.Row(current_row, className="mb-3"))
                    current_row = []
                continue
            
            # 获取图表配置
            datasource_id = chart_config.get('datasource_id')
            chart_type = chart_config.get('type', 'line')
            chart_title = chart_config.get('title', chart_config.get('name', '图表'))
            
            if not datasource_id:
                error_card = dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.H5(chart_title, className="mb-0 d-inline-block"),
                                dbc.Button(
                                    [html.I(className="fas fa-times")],
                                    id={"type": "remove-chart-from-dashboard", "chart_id": chart_id},
                                    color="link",
                                    size="sm",
                                    className="float-end",
                                ),
                            ],
                            className="d-flex justify-content-between align-items-center",
                        ),
                        dbc.CardBody(
                            dbc.Alert("图表未关联数据源，请在图表设计器中配置数据源", color="warning")
                        ),
                    ],
                    className="mb-3",
                )
                current_row.append(dbc.Col(error_card, width=6))
                error_count += 1
                if len(current_row) == 2 or i == len(chart_ids) - 1:
                    rows.append(dbc.Row(current_row, className="mb-3"))
                    current_row = []
                continue
            
            try:
                # 加载数据
                ds_config = config_manager.get_datasource(datasource_id)
                if not ds_config:
                    error_card = dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.H5(chart_title, className="mb-0 d-inline-block"),
                                    dbc.Button(
                                        [html.I(className="fas fa-times")],
                                        id={"type": "remove-chart-from-dashboard", "chart_id": chart_id},
                                        color="link",
                                        size="sm",
                                        className="float-end",
                                    ),
                                ],
                                className="d-flex justify-content-between align-items-center",
                            ),
                            dbc.CardBody(
                                dbc.Alert(f"数据源不存在（ID: {datasource_id}），请检查数据源配置", color="warning")
                            ),
                        ],
                        className="mb-3",
                    )
                    current_row.append(dbc.Col(error_card, width=6))
                    error_count += 1
                    if len(current_row) == 2 or i == len(chart_ids) - 1:
                        rows.append(dbc.Row(current_row, className="mb-3"))
                        current_row = []
                    continue
                
                adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
                df_raw = adapter.fetch_data(limit=1000)
                
                # 确保 df 是 DataFrame 类型
                if not isinstance(df_raw, pd.DataFrame):
                    error_card = dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.H5(chart_title, className="mb-0 d-inline-block"),
                                    dbc.Button(
                                        [html.I(className="fas fa-times")],
                                        id={"type": "remove-chart-from-dashboard", "chart_id": chart_id},
                                        color="link",
                                        size="sm",
                                        className="float-end",
                                    ),
                                ],
                                className="d-flex justify-content-between align-items-center",
                            ),
                            dbc.CardBody(
                                dbc.Alert("数据源返回的数据格式不正确", color="warning")
                            ),
                        ],
                        className="mb-3",
                    )
                    current_row.append(dbc.Col(error_card, width=6))
                    error_count += 1
                    if len(current_row) == 2 or i == len(chart_ids) - 1:
                        rows.append(dbc.Row(current_row, className="mb-3"))
                        current_row = []
                    continue
                
                # 明确类型为 DataFrame
                df: pd.DataFrame = cast(pd.DataFrame, df_raw)
                
                if df is None or df.empty:
                    error_card = dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.H5(chart_title, className="mb-0 d-inline-block"),
                                    dbc.Button(
                                        [html.I(className="fas fa-times")],
                                        id={"type": "remove-chart-from-dashboard", "chart_id": chart_id},
                                        color="link",
                                        size="sm",
                                        className="float-end",
                                    ),
                                ],
                                className="d-flex justify-content-between align-items-center",
                            ),
                            dbc.CardBody(
                                dbc.Alert("数据源没有数据或数据为空，请检查数据源", color="warning")
                            ),
                        ],
                        className="mb-3",
                    )
                    current_row.append(dbc.Col(error_card, width=6))
                    error_count += 1
                    if len(current_row) == 2 or i == len(chart_ids) - 1:
                        rows.append(dbc.Row(current_row, className="mb-3"))
                        current_row = []
                    continue
                
                # 应用时间筛选（如果有时间字段）
                if time_filter and time_filter != "custom":
                    date_field = None
                    for col in df.columns:
                        if pd.api.types.is_datetime64_any_dtype(df[col]) or 'date' in str(df[col].dtype).lower():
                            date_field = col
                            break
                    
                    if date_field:
                        now = pd.Timestamp.now()
                        start: Optional[pd.Timestamp] = None
                        end: Optional[pd.Timestamp] = None
                        
                        if time_filter == "today":
                            start = now.normalize()
                            end = now
                        elif time_filter == "7days":
                            delta_days = 7
                            delta = pd.Timedelta(days=delta_days)
                            start = (now - delta).normalize()  # type: ignore
                            end = now
                        elif time_filter == "30days":
                            delta_days = 30
                            delta = pd.Timedelta(days=delta_days)
                            start = (now - delta).normalize()  # type: ignore
                            end = now
                        elif time_filter == "month":
                            start = now.replace(day=1).normalize()
                            end = now
                        
                        if start is not None and end is not None:
                            # DataFrame 的布尔索引总是返回 DataFrame
                            df_filtered = df[(df[date_field] >= start) & (df[date_field] <= end)]
                            df = cast(pd.DataFrame, df_filtered)  # type: ignore
                
                if time_filter == "custom" and start_date and end_date:
                    date_field = None
                    for col in df.columns:
                        if pd.api.types.is_datetime64_any_dtype(df[col]) or 'date' in str(df[col].dtype).lower():
                            date_field = col
                            break
                    
                    if date_field:
                        try:
                            custom_start = pd.Timestamp(start_date)  # type: ignore
                            custom_end = pd.Timestamp(end_date)  # type: ignore
                            # 检查是否为有效的Timestamp（不是NaT）
                            if custom_start is not pd.NaT and custom_end is not pd.NaT:  # type: ignore
                                # DataFrame 的布尔索引总是返回 DataFrame
                                df_filtered = df[(df[date_field] >= custom_start) & (df[date_field] <= custom_end)]
                                df = cast(pd.DataFrame, df_filtered)  # type: ignore
                        except (ValueError, TypeError):
                            # 如果日期转换失败，跳过筛选
                            pass
                
                # 应用图表联动筛选（如果存在筛选条件且当前图表不是源图表）
                if filter_state and filter_state.get('source_chart_id') != chart_id:
                    filter_field = filter_state.get('field')
                    filter_value = filter_state.get('value')
                    
                    # 应用筛选条件
                    if filter_field and filter_value is not None and filter_field in df.columns:
                        # 应用筛选条件
                        try:
                            # 尝试数值比较
                            if pd.api.types.is_numeric_dtype(df[filter_field]):
                                # DataFrame 的布尔索引总是返回 DataFrame
                                df_filtered = df[df[filter_field] == filter_value]
                                df = cast(pd.DataFrame, df_filtered)  # type: ignore
                            else:
                                # 字符串匹配
                                # DataFrame 的布尔索引总是返回 DataFrame
                                df_filtered = df[df[filter_field].astype(str) == str(filter_value)]
                                df = cast(pd.DataFrame, df_filtered)  # type: ignore
                        except:
                            # 如果筛选失败，尝试模糊匹配
                            try:
                                # DataFrame 的布尔索引总是返回 DataFrame
                                df_filtered = df[df[filter_field].astype(str).str.contains(str(filter_value), na=False)]
                                df = cast(pd.DataFrame, df_filtered)  # type: ignore
                            except:
                                pass  # 如果筛选失败，使用原始数据
                
                chart_config_for_engine = {
                    "type": chart_type,
                    "x": chart_config.get('x'),
                    "y": chart_config.get('y'),
                    "group": chart_config.get('group'),
                    "title": chart_title,
                    "color_theme": chart_config.get('color_theme', 'default'),
                    "custom_colors": chart_config.get('custom_colors', {}),
                    "show_labels": chart_config.get('show_labels', False),
                    "show_legend": chart_config.get('show_legend', True),
                    "agg_function": chart_config.get('agg_function', 'sum'),
                }
                
                if chart_type == 'table':
                    chart_config_for_engine['table_columns'] = chart_config.get('table_columns', [])
                    chart_config_for_engine['table_rows'] = chart_config.get('table_rows', [])
                    chart_config_for_engine['table_orientation'] = chart_config.get('table_orientation', 'horizontal')
                
                fig = chart_engine.create_chart(df, chart_config_for_engine)
                
                # 检查是否是筛选源图表
                is_filter_source = filter_state and filter_state.get('source_chart_id') == chart_id
                is_filtered = filter_state and filter_state.get('source_chart_id') != chart_id and filter_state.get('field')
                
                # 创建图表卡片，如果是筛选源则添加边框高亮
                card_class = "mb-3"
                if is_filter_source:
                    card_class += " border-primary border-2"
                elif is_filtered:
                    card_class += " border-info border-1"
                
                # 添加筛选提示
                filter_badge = None
                if is_filter_source:
                    filter_badge = dbc.Badge("筛选源", color="primary", className="ms-2")
                elif is_filtered:
                    filter_field = filter_state.get('field')
                    filter_value = filter_state.get('value')
                    filter_badge = dbc.Badge(
                        f"已筛选: {filter_field}={filter_value}", 
                        color="info", 
                        className="ms-2"
                    )
                
                chart_card = dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.Div([
                                    html.H5(chart_title, className="mb-0 d-inline-block"),
                                    filter_badge,
                                ], className="d-inline-block"),
                                dbc.Button(
                                    [html.I(className="fas fa-times")],
                                    id={"type": "remove-chart-from-dashboard", "chart_id": chart_id},
                                    color="link",
                                    size="sm",
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
                    className=card_class,
                )
                
                current_row.append(dbc.Col(chart_card, width=6))
                
                # 每2个图表一行
                if len(current_row) == 2 or i == len(chart_ids) - 1:
                    rows.append(dbc.Row(current_row, className="mb-3"))
                    current_row = []
                    
            except Exception as e:
                import traceback
                error_msg = str(e)
                error_detail = traceback.format_exc()
                chart_title_for_error = chart_config.get('title', chart_config.get('name', f'图表 {chart_id}'))
                print(f"[仪表盘] 加载图表失败 (ID: {chart_id}, 名称: {chart_title_for_error}): {error_msg}")
                print(f"[仪表盘] 错误详情:\n{error_detail}")
                
                error_card = dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.H5(chart_title_for_error, className="mb-0 d-inline-block"),
                                dbc.Button(
                                    [html.I(className="fas fa-times")],
                                    id={"type": "remove-chart-from-dashboard", "chart_id": chart_id},
                                    color="link",
                                    size="sm",
                                    className="float-end",
                                ),
                            ],
                            className="d-flex justify-content-between align-items-center",
                        ),
                        dbc.CardBody(
                            dbc.Alert(f"加载图表失败：{error_msg}", color="danger")
                        ),
                    ],
                    className="mb-3",
                )
                current_row.append(dbc.Col(error_card, width=6))
                error_count += 1
                if len(current_row) == 2 or i == len(chart_ids) - 1:
                    rows.append(dbc.Row(current_row, className="mb-3"))
                    current_row = []
        
        # 如果所有图表都失败了，显示汇总信息
        if not rows:
            if total_charts > 0:
                return dbc.Alert(
                    [
                        html.H5("无法加载图表", className="alert-heading"),
                        html.P(f"共有 {total_charts} 个图表，但全部加载失败。请检查：", className="mb-2"),
                        html.Ul([
                            html.Li("数据源配置是否正确"),
                            html.Li("数据源是否已启用"),
                            html.Li("数据源是否有数据"),
                            html.Li("图表配置是否完整"),
                        ]),
                    ],
                    color="warning",
                    className="m-4"
                )
            else:
                result = html.P("该仪表盘还没有添加图表，请点击\"添加图表\"按钮添加", className="text-muted text-center py-5")
                # 如果有导出状态消息，显示在顶部
                if export_status and export_status.get('message'):
                    return [export_status['message'], result]
                return result
        
        # 如果有导出状态消息，显示在图表前面
        if export_status and export_status.get('message'):
            return [export_status['message']] + rows
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
        
        return callback_context.triggered[0]["value"] + 1 if callback_context.triggered else 1, saved_id, dashboard_config

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
        
        return callback_context.triggered[0]["value"] + 1 if callback_context.triggered else 1, None, None

    @app.callback(
        [Output("modal-add-chart-to-dashboard", "is_open"),
         Output("chart-selector-for-dashboard", "options"),
         Output("current-dashboard-config", "data", allow_duplicate=True),
         Output("dashboard-add-chart-status", "children", allow_duplicate=True)],
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
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-add-chart-to-dashboard":
            charts = config_manager.load_charts()
            options = [
                {"label": chart.get('name', chart.get('title', '未命名图表')), "value": chart.get('id')}
                for chart in charts if chart.get('id')
            ]
            if not options:
                options = [{"label": "暂无可用图表，请先创建图表", "value": None, "disabled": True}]
            return True, options, dash.no_update, dash.no_update
        
        elif trigger_id == "btn-cancel-add-chart":
            return False, dash.no_update, dash.no_update, dash.no_update
        
        elif trigger_id == "btn-confirm-add-chart":
            if selected_chart_id and dashboard_config:
                chart_ids = dashboard_config.get('chart_ids', [])
                if selected_chart_id not in chart_ids:
                    chart_ids.append(selected_chart_id)
                    dashboard_config['chart_ids'] = chart_ids
                    config_manager.save_dashboard(dashboard_config)
                    updated_dashboard = config_manager.get_dashboard(dashboard_config.get('id'))
                    if updated_dashboard:
                        return False, dash.no_update, updated_dashboard, dbc.Alert("图表已添加到仪表盘", color="success", className="m-2")
                    else:
                        return False, dash.no_update, dashboard_config, dbc.Alert("图表已添加到仪表盘", color="success", className="m-2")
                else:
                    return False, dash.no_update, dash.no_update, dbc.Alert("该图表已存在于仪表盘中", color="warning", className="m-2")
            else:
                return False, dash.no_update, dash.no_update, dbc.Alert("请选择图表和仪表盘", color="warning", className="m-2")
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

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
        
        trigger_id = ctx.triggered[0]["prop_id"]
        if "chart_id" in trigger_id:
            try:
                chart_id_dict = json.loads(trigger_id.split(".")[0])
                chart_id = chart_id_dict.get("chart_id")
                
                chart_ids = dashboard_config.get('chart_ids', [])
                if chart_id in chart_ids:
                    chart_ids.remove(chart_id)
                    dashboard_config['chart_ids'] = chart_ids
                    config_manager.save_dashboard(dashboard_config)
                    return callback_context.triggered[0]["value"] + 1 if callback_context.triggered else 1, dashboard_config
            except:
                pass
        
        return dash.no_update, dash.no_update

    @app.callback(
        [Output("export-status-message", "data", allow_duplicate=True),
         Output("export-status-interval", "disabled", allow_duplicate=True)],
        [Input("btn-export-dashboard-png", "n_clicks"),
         Input("btn-export-dashboard-pdf", "n_clicks"),
         Input("btn-export-dashboard-html", "n_clicks")],
        [State("current-dashboard-config", "data")],
        prevent_initial_call=True
    )
    def export_dashboard(png_clicks, pdf_clicks, html_clicks, dashboard_config):
        """导出仪表盘"""
        import traceback
        import time
        
        ctx = callback_context
        if not ctx.triggered or not dashboard_config:
            return dash.no_update, dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        try:
            chart_ids = dashboard_config.get('chart_ids', [])
            if not chart_ids:
                alert = dbc.Alert("该仪表盘没有图表，无法导出", color="warning", className="m-2")
                return {
                    "message": alert,
                    "timestamp": time.time()
                }, False  # 启用 Interval
            
            charts = config_manager.load_charts()
            chart_map = {chart.get('id'): chart for chart in charts if chart.get('id')}
            
            figures_with_titles = []
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
                    
                    chart_title = chart_config.get('title', chart_config.get('name', '图表'))
                    chart_type = chart_config.get('type', 'line')
                    chart_config_for_engine = {
                        "type": chart_type,
                        "x": chart_config.get('x'),
                        "y": chart_config.get('y'),
                        "group": chart_config.get('group'),
                        "title": chart_title,
                        "color_theme": chart_config.get('color_theme', 'default'),
                        "custom_colors": chart_config.get('custom_colors', {}),
                        "show_labels": chart_config.get('show_labels', False),
                        "show_legend": chart_config.get('show_legend', True),
                        "agg_function": chart_config.get('agg_function', 'sum'),
                    }
                    
                    if chart_type == 'table':
                        chart_config_for_engine['table_columns'] = chart_config.get('table_columns', [])
                        chart_config_for_engine['table_rows'] = chart_config.get('table_rows', [])
                        chart_config_for_engine['table_orientation'] = chart_config.get('table_orientation', 'horizontal')
                    
                    fig = chart_engine.create_chart(df, chart_config_for_engine)
                    figures_with_titles.append((fig, chart_title, chart_type))
                except Exception as e:
                    print(f"生成图表 {chart_id} 时出错: {str(e)}")
                    traceback.print_exc()
                    continue
            
            if not figures_with_titles:
                alert = dbc.Alert("无法生成图表，请检查数据源配置", color="danger", className="m-2")
                return {
                    "message": alert,
                    "timestamp": time.time()
                }, False  # 启用 Interval
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dashboard_name = (dashboard_config.get('name', 'dashboard')).replace(" ", "_").replace("/", "_")
            
            if trigger_id == "btn-export-dashboard-png":
                try:
                    export_path = export_dashboard_to_png(
                        dashboard_config,
                        figures_with_titles,
                        export_dir,
                        timestamp
                    )
                    alert = dbc.Alert(f"仪表盘已导出为PNG：{export_path.name}", color="success", className="m-2")
                    return {
                        "message": alert,
                        "timestamp": time.time()
                    }, False  # 启用 Interval，3秒后自动清除
                except Exception as e:
                    import traceback
                    error_msg = str(e)
                    error_trace = traceback.format_exc()
                    print(f"PNG导出失败: {error_msg}")
                    print(error_trace)
                    alert = dbc.Alert(
                        f"PNG导出失败：{error_msg}。请安装以下库之一：imgkit（需要wkhtmltopdf）、playwright 或 kaleido。",
                        color="danger",
                        className="m-2"
                    )
                    return {
                        "message": alert,
                        "timestamp": time.time()
                    }, False  # 启用 Interval
            
            elif trigger_id == "btn-export-dashboard-pdf":
                try:
                    export_path = export_dashboard_to_pdf(
                        dashboard_config,
                        figures_with_titles,
                        export_dir,
                        timestamp
                    )
                    alert = dbc.Alert(f"仪表盘已导出为PDF：{export_path.name}", color="success", className="m-2")
                    return {
                        "message": alert,
                        "timestamp": time.time()
                    }, False  # 启用 Interval，3秒后自动清除
                except Exception as e:
                    import traceback
                    error_msg = str(e)
                    traceback.print_exc()
                    alert = dbc.Alert(f"PDF导出失败：{error_msg}。请确保已安装kaleido库（pip install kaleido）以及reportlab和PIL库（pip install reportlab pillow）。", color="danger", className="m-2")
                    return {
                        "message": alert,
                        "timestamp": time.time()
                    }, False  # 启用 Interval
            
            elif trigger_id == "btn-export-dashboard-html":
                try:
                    export_path = export_dashboard_to_html(
                        dashboard_config,
                        figures_with_titles,
                        export_dir,
                        timestamp
                    )
                    alert = dbc.Alert(f"仪表盘已导出为HTML：{export_path.name}", color="success", className="m-2")
                    return {
                        "message": alert,
                        "timestamp": time.time()
                    }, False  # 启用 Interval，3秒后自动清除
                except Exception as e:
                    import traceback
                    error_msg = str(e)
                    error_trace = traceback.format_exc()
                    print(f"HTML导出失败: {error_msg}")
                    print(error_trace)
                    alert = dbc.Alert(f"HTML导出失败：{error_msg}", color="danger", className="m-2")
                    return {
                        "message": alert,
                        "timestamp": time.time()
                    }, False  # 启用 Interval
            
            return dash.no_update, dash.no_update
        
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"导出仪表盘时发生错误: {error_msg}")
            print(error_trace)
            alert = dbc.Alert(f"导出失败：{error_msg}。请检查控制台日志获取详细信息。", color="danger", className="m-2")
            return {
                "message": alert,
                "timestamp": time.time()
            }, False  # 启用 Interval

    @app.callback(
        [Output("export-status-message", "data", allow_duplicate=True),
         Output("export-status-interval", "disabled", allow_duplicate=True)],
        Input("export-status-interval", "n_intervals"),
        State("export-status-message", "data"),
        prevent_initial_call=True
    )
    def clear_export_status(n_intervals, status_data):
        """3秒后自动清除导出状态消息"""
        import time
        
        if not status_data or not status_data.get('timestamp'):
            return None, True  # 没有消息，禁用 Interval
        
        current_time = time.time()
        elapsed = current_time - status_data.get('timestamp', 0)
        
        # 如果超过3秒，清除消息并禁用 Interval
        if elapsed >= 3.0:
            return None, True
        
        # 否则保持消息不变，继续运行 Interval
        return dash.no_update, False

    @app.callback(
        [Output("chart-filter-state", "data", allow_duplicate=True),
         Output("chart-data-cache", "data", allow_duplicate=True)],
        [Input({"type": "dashboard-chart", "chart_id": ALL}, "clickData"),
         Input({"type": "dashboard-chart", "chart_id": ALL}, "selectedData")],
        [State("current-dashboard-config", "data"),
         State("chart-filter-state", "data"),
         State("chart-data-cache", "data")],
        prevent_initial_call=True
    )
    def handle_chart_click(click_data_list, selected_data_list, dashboard_config, current_filter, data_cache):
        """处理图表点击事件，设置筛选条件"""
        ctx = callback_context
        if not ctx.triggered or not dashboard_config:
            return dash.no_update, dash.no_update
        
        # 找到被点击的图表
        triggered_id = ctx.triggered[0]["prop_id"]
        if not triggered_id or triggered_id == ".":
            return dash.no_update, dash.no_update
        
        try:
            # 解析图表ID
            chart_id_str = triggered_id.split(".")[0]
            chart_id_dict = json.loads(chart_id_str)
            source_chart_id = chart_id_dict.get("chart_id")
            
            if not source_chart_id:
                return dash.no_update, dash.no_update
            
            # 获取被点击图表的索引
            chart_ids = dashboard_config.get('chart_ids', [])
            if source_chart_id not in chart_ids:
                return dash.no_update, dash.no_update
            
            chart_index = chart_ids.index(source_chart_id)
            click_data = click_data_list[chart_index] if chart_index < len(click_data_list) else None
            
            # 如果点击的是已筛选的源图表，清除筛选（再次点击源图表清除筛选）
            if current_filter and current_filter.get('source_chart_id') == source_chart_id and click_data:
                return None, dash.no_update
            
            if not click_data:
                return dash.no_update, dash.no_update
            
            # 从点击数据中提取筛选字段和值
            filter_field = None
            filter_value = None
            
            # Plotly 点击数据结构：{'points': [{'x': value, 'y': value, 'customdata': ..., ...}]}
            points = click_data.get('points', [])
            if points:
                point = points[0]
                
                # 获取图表配置以确定字段
                charts = config_manager.load_charts()
                chart_map = {chart.get('id'): chart for chart in charts if chart.get('id')}
                chart_config = chart_map.get(source_chart_id)
                
                if chart_config:
                    chart_type = chart_config.get('type', 'line')
                    x_field = chart_config.get('x')
                    y_field = chart_config.get('y')
                    group_field = chart_config.get('group')
                    
                    # 根据图表类型和点击位置确定筛选字段
                    if chart_type in ['bar', 'line', 'combo']:
                        # 对于柱状图和折线图，通常点击 X 轴值进行筛选
                        if 'x' in point and point['x'] is not None:
                            filter_field = x_field
                            filter_value = point['x']
                        elif 'label' in point and point['label'] is not None:
                            filter_field = x_field
                            filter_value = point['label']
                        elif 'customdata' in point and point['customdata'] is not None:
                            # 尝试从 customdata 中获取值
                            filter_field = x_field
                            filter_value = point['customdata']
                    elif chart_type == 'pie':
                        # 对于饼图，点击的是分类值
                        if 'label' in point and point['label'] is not None:
                            filter_field = group_field or x_field
                            filter_value = point['label']
                        elif 'x' in point and point['x'] is not None:
                            filter_field = group_field or x_field
                            filter_value = point['x']
                        elif 'customdata' in point and point['customdata'] is not None:
                            filter_field = group_field or x_field
                            filter_value = point['customdata']
                    
                    # 如果找到了筛选字段和值，设置筛选条件
                    if filter_field and filter_value is not None:
                        filter_state = {
                            "source_chart_id": source_chart_id,
                            "field": filter_field,
                            "value": filter_value
                        }
                        return filter_state, dash.no_update
            
            return dash.no_update, dash.no_update
            
        except Exception as e:
            import traceback
            print(f"处理图表点击事件时出错: {str(e)}")
            traceback.print_exc()
            return dash.no_update, dash.no_update

    @app.callback(
        [Output("chart-filter-state", "data", allow_duplicate=True),
         Output("btn-clear-chart-filter", "style", allow_duplicate=True),
         Output("chart-filter-status", "children", allow_duplicate=True)],
        [Input("btn-clear-chart-filter", "n_clicks"),
         Input("chart-filter-state", "data")],
        prevent_initial_call=True
    )
    def update_filter_ui(clear_clicks, filter_state):
        """更新筛选UI：清除筛选或更新筛选状态显示"""
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # 如果点击了清除按钮
        if trigger_id == "btn-clear-chart-filter" and clear_clicks:
            return None, {"display": "none"}, html.Div()
        
        # 如果有筛选条件，显示状态和按钮
        if filter_state:
            source_chart_id = filter_state.get('source_chart_id')
            filter_field = filter_state.get('field')
            filter_value = filter_state.get('value')
            
            # 获取源图表名称
            charts = config_manager.load_charts()
            chart_map = {chart.get('id'): chart for chart in charts if chart.get('id')}
            source_chart = chart_map.get(source_chart_id)
            source_chart_name = source_chart.get('name', source_chart.get('title', '图表')) if source_chart else f"图表 {source_chart_id}"
            
            status_badge = dbc.Badge(
                [
                    html.I(className="fas fa-filter me-1"),
                    f"筛选中: {source_chart_name} - {filter_field}={filter_value}",
                ],
                color="info",
                className="ms-2"
            )
            return dash.no_update, {"display": "inline-block"}, status_badge
        
        # 没有筛选条件
        return dash.no_update, {"display": "none"}, html.Div()
    
    @app.callback(
        [Output("btn-clear-chart-filter", "style", allow_duplicate=True),
         Output("chart-filter-status", "children", allow_duplicate=True)],
        Input("chart-filter-state", "data"),
        prevent_initial_call='initial_duplicate'
    )
    def init_filter_ui(filter_state):
        """初始化筛选UI显示"""
        if filter_state:
            source_chart_id = filter_state.get('source_chart_id')
            filter_field = filter_state.get('field')
            filter_value = filter_state.get('value')
            
            # 获取源图表名称
            charts = config_manager.load_charts()
            chart_map = {chart.get('id'): chart for chart in charts if chart.get('id')}
            source_chart = chart_map.get(source_chart_id)
            source_chart_name = source_chart.get('name', source_chart.get('title', '图表')) if source_chart else f"图表 {source_chart_id}"
            
            status_badge = dbc.Badge(
                [
                    html.I(className="fas fa-filter me-1"),
                    f"筛选中: {source_chart_name} - {filter_field}={filter_value}",
                ],
                color="info",
                className="ms-2"
            )
            return {"display": "inline-block"}, status_badge
        
        return {"display": "none"}, html.Div()

    @app.callback(
        [Output("modal-share-dashboard", "is_open"),
         Output("share-link-input", "value")],
        [Input("btn-share-dashboard", "n_clicks"),
         Input("btn-close-share-modal", "n_clicks")],
        [State("modal-share-dashboard", "is_open"),
         State("current-dashboard-id", "data")],
        prevent_initial_call=True
    )
    def toggle_share_modal(share_clicks, close_clicks, is_open, dashboard_id):
        """打开/关闭分享链接模态框"""
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "btn-share-dashboard" and share_clicks:
            if not dashboard_id:
                return dash.no_update, dash.no_update
            
            # 生成分享链接
            # 获取当前的主机地址（可以从环境变量或配置中获取，这里使用默认值）
            import os
            base_url = os.getenv("DASH_APP_URL", "http://localhost:8050")
            share_link = f"{base_url}/dashboard?dashboard_id={dashboard_id}"
            
            return True, share_link
        
        elif trigger_id == "btn-close-share-modal":
            return False, dash.no_update
        
        return dash.no_update, dash.no_update

    @app.callback(
        Output("share-link-copy-status", "children", allow_duplicate=True),
        Input("btn-copy-share-link", "n_clicks"),
        State("share-link-input", "value"),
        prevent_initial_call=True
    )
    def copy_share_link(copy_clicks, link_value):
        """复制分享链接到剪贴板"""
        if copy_clicks and link_value:
            # 返回成功消息（实际复制由客户端JavaScript完成）
            return dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    "链接已复制到剪贴板！",
                ],
                color="success",
                className="mt-2"
            )
        return dash.no_update

    # 客户端回调：使用JavaScript复制到剪贴板
    app.clientside_callback(
        """
        function(n_clicks, link_value) {
            if (n_clicks && link_value) {
                // 尝试使用现代 Clipboard API
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(link_value).then(function() {
                        console.log('链接已复制到剪贴板');
                    }).catch(function(err) {
                        console.error('Clipboard API 复制失败:', err);
                        // 降级到 execCommand 方法
                        fallbackCopy(link_value);
                    });
                } else {
                    // 降级到 execCommand 方法
                    fallbackCopy(link_value);
                }
            }
            return window.dash_clientside.no_update;
        }
        function fallbackCopy(text) {
            const tempInput = document.createElement('input');
            tempInput.value = text;
            tempInput.style.position = 'fixed';
            tempInput.style.opacity = '0';
            tempInput.style.left = '-9999px';
            document.body.appendChild(tempInput);
            tempInput.select();
            tempInput.setSelectionRange(0, 99999); // 对于移动设备
            
            try {
                document.execCommand('copy');
                console.log('链接已复制到剪贴板（使用 fallback 方法）');
            } catch (err) {
                console.error('复制失败:', err);
            } finally {
                document.body.removeChild(tempInput);
            }
        }
        """,
        Output("share-link-input", "value", allow_duplicate=True),
        [Input("btn-copy-share-link", "n_clicks")],
        [State("share-link-input", "value")],
        prevent_initial_call=True
    )

