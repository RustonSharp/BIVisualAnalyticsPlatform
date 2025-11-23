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
         Input("end-date", "date"),
         Input("export-status-message", "data")],
        prevent_initial_call=False
    )
    def render_dashboard_charts(dashboard_config, time_filter, start_date, end_date, export_status):
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
                df = adapter.fetch_data(limit=1000)
                
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
                            df = df[(df[date_field] >= start) & (df[date_field] <= end)]
                
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
                                df = df[(df[date_field] >= custom_start) & (df[date_field] <= custom_end)]
                        except (ValueError, TypeError):
                            # 如果日期转换失败，跳过筛选
                            pass
                
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
                
                # 创建图表卡片
                chart_card = dbc.Card(
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
                            [
                                dcc.Graph(figure=fig, id={"type": "dashboard-chart", "chart_id": chart_id}),
                            ]
                        ),
                    ],
                    className="mb-3",
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

