"""图表设计器页面模块"""
import dash
from dash import dcc, html, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from components.common import default_chart_assignments, render_assigned_fields, create_table_from_dataframe
from data_adapter import DataSourceAdapter
import pandas as pd
from language_manager import language_manager
from logger import get_logger

logger = get_logger('chart_designer_page')


def create_chart_designer_page():
    """创建图表设计器页面"""
    texts = language_manager.get_all_texts()
    return dbc.Container(
        [
            html.H2(texts["chart_designer_title"], id="chart-designer-title", className="mb-4"),
            dcc.Store(id="chart-field-assignments", data=default_chart_assignments()),
            dcc.Store(id="custom-colors-config", data={}),
            dcc.Store(id="field-agg-functions-config", data={}),  # 存储每个字段的聚合函数配置
            dcc.Store(id="dnd-last-event", data=""),
            html.Button(id="dnd-event-trigger", n_clicks=0, style={"display": "none"}),
            dcc.Store(id="dnd-event-data", data=""),
            
            dbc.Row(
                [
                    # 左侧：字段列表和配置区
                    dbc.Col(
                        [
                            # 数据源选择
                            dbc.Card(
                                [
                                    dbc.CardHeader(texts["select_datasource"], id="select-datasource-header"),
                                    dbc.CardBody(
                                        [
                                            html.Label(texts["select_datasource"], htmlFor="chart-datasource-select", className="form-label", style={"display": "none"}),
                                            dbc.Select(
                                                id="chart-datasource-select",
                                                name="chart-datasource-select",
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
                                    dbc.CardHeader(texts["field_list"], id="field-list-header"),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                html.P(texts["select_datasource_first"], id="field-list-hint", className="text-muted mb-0"),
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
                                    dbc.CardHeader(texts["chart_type"], id="chart-type-header"),
                                    dbc.CardBody(
                                        [
                                            html.Label(texts["chart_type"], htmlFor="chart-type", className="form-label", style={"display": "none"}),
                                            dbc.RadioItems(
                                                id="chart-type",
                                                name="chart-type",
                                                options=[
                                                    {"label": texts["line_chart"], "value": "line"},
                                                    {"label": texts["bar_chart"], "value": "bar"},
                                                    {"label": texts["pie_chart"], "value": "pie"},
                                                    {"label": texts["table"], "value": "table"},
                                                    {"label": texts["combo_chart"], "value": "combo"},
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
                                        dbc.CardHeader(texts["chart_config"], id="chart-config-header"),
                                        dbc.CardBody(
                                            [
                                                # 普通图表配置（折线图、柱状图等）
                                                html.Div(id="chart-config-normal", children=[
                                                    html.Div(
                                                        [
                                                            # X 轴配置
                                                            html.Div(id="x-axis-config", children=[
                                                                html.Div(
                                                                    [
                                                                        html.Label(texts["x_axis"], className="form-label fw-bold mb-0"),
                                                                        dbc.Button(texts["clear"], id="btn-clear-x-axis", color="link", size="sm", className="p-0 ms-2"),
                                                                    ],
                                                                    className="d-flex align-items-center mb-2"
                                                                ),
                                                                html.Div(
                                                                    id="drop-x-axis",
                                                                    children=[
                                                                        html.P(texts["drag_field_here"], className="text-muted text-center mb-0"),
                                                                    ],
                                                                    style={
                                                                        "minHeight": "60px",
                                                                        "marginBottom": "15px",
                                                                        "border": "2px dashed #ced4da",
                                                                        "borderRadius": "6px",
                                                                        "padding": "0.5rem"
                                                                    },
                                                                    className="drop-zone",
                                                                ),
                                                            ]),
                                                            # Y 轴配置
                                                            html.Div(
                                                                [
                                                                    html.Label(id="y-axis-label", children=texts["y_axis"], className="form-label fw-bold mb-0"),
                                                                    dbc.Button(texts["clear"], id="btn-clear-y-axis", color="link", size="sm", className="p-0 ms-2"),
                                                                ],
                                                                className="d-flex align-items-center mb-2"
                                                            ),
                                                            html.P(id="y-axis-hint", children=texts["drag_field_here"], className="text-muted text-center mb-2 small"),
                                                            html.Div(
                                                                id="drop-y-axis",
                                                                children=[
                                                                    html.P(texts["drag_field_here"], className="text-muted text-center mb-0"),
                                                                ],
                                                                style={
                                                                    "minHeight": "60px",
                                                                    "marginBottom": "15px",
                                                                    "border": "2px dashed #ced4da",
                                                                    "borderRadius": "6px",
                                                                    "padding": "0.5rem"
                                                                },
                                                                className="drop-zone",
                                                            ),
                                                            # 分组配置
                                                            html.Div(
                                                                [
                                                                    html.Label(id="group-label", children=texts["group_color"], className="form-label fw-bold mb-0"),
                                                                    dbc.Button(texts["clear"], id="btn-clear-group", color="link", size="sm", className="p-0 ms-2"),
                                                                ],
                                                                className="d-flex align-items-center mb-2"
                                                            ),
                                                            html.P(id="group-hint", children=texts["drag_field_here"], className="text-muted text-center mb-2 small"),
                                                            html.Div(
                                                                id="drop-group",
                                                                children=[
                                                                    html.P(texts["drag_field_here"], className="text-muted text-center mb-0"),
                                                                ],
                                                                style={
                                                                    "minHeight": "60px",
                                                                    "marginBottom": "15px",
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
                                                            html.Label(texts["display_orientation"], htmlFor="table-orientation", className="form-label fw-bold mb-2"),
                                                            dbc.RadioItems(
                                                                id="table-orientation",
                                                                name="table-orientation",
                                                                options=[
                                                                    {"label": texts["horizontal_display"], "value": "horizontal"},
                                                                    {"label": texts["vertical_display"], "value": "vertical"},
                                                                ],
                                                                value="horizontal",
                                                                inline=False,
                                                            ),
                                                        ],
                                                        className="mb-3"
                                                    ),
                                                    html.Div(id="table-columns-config", children=[
                                                        html.Label(texts["table_columns_config"], className="form-label fw-bold mb-2"),
                                                        html.P(texts["drag_field_to_columns"], className="text-muted small mb-2"),
                                                        html.Div(id="table-columns-list", children=[
                                                            html.P(texts["drag_field_as_column"].format(1), className="text-muted text-center mb-2 small"),
                                                            html.Div(
                                                                id="drop-table-col-1",
                                                                children=[
                                                                    html.P(texts["drag_field_here"], className="text-muted text-center mb-0"),
                                                                ],
                                                                style={
                                                                    "minHeight": "50px",
                                                                    "marginBottom": "10px",
                                                                    "border": "2px dashed #ced4da",
                                                                    "borderRadius": "6px",
                                                                    "padding": "0.5rem"
                                                                },
                                                                className="drop-zone",
                                                            ),
                                                        ]),
                                                        dbc.Button(texts["add_column"], id="btn-add-table-column", color="link", size="sm", className="p-0 mt-2"),
                                                    ]),
                                                    html.Div(id="table-rows-config", style={"display": "none"}, children=[
                                                        html.Label(texts["table_rows_config"], className="form-label fw-bold mb-2"),
                                                        html.P(texts["drag_field_to_rows"], className="text-muted small mb-2"),
                                                        html.Div(id="table-rows-list", children=[
                                                            html.P(texts["drag_field_as_row"].format(1), className="text-muted text-center mb-2 small"),
                                                            html.Div(
                                                                id="drop-table-row-1",
                                                                children=[
                                                                    html.P(texts["drag_field_here"], className="text-muted text-center mb-0"),
                                                                ],
                                                                style={
                                                                    "minHeight": "50px",
                                                                    "marginBottom": "10px",
                                                                    "border": "2px dashed #ced4da",
                                                                    "borderRadius": "6px",
                                                                    "padding": "0.5rem"
                                                                },
                                                                className="drop-zone",
                                                            ),
                                                        ]),
                                                        dbc.Button(texts["add_row"], id="btn-add-table-row", color="link", size="sm", className="p-0 mt-2"),
                                                    ]),
                                                ]),
                                            ]
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                            ]),
                            
                            # 聚合函数
                            html.Div(id="agg-function-card", children=[
                                dbc.Card(
                                    [
                                        dbc.CardHeader(texts["aggregation_function_config"], id="agg-function-header"),
                                        dbc.CardBody(
                                            [
                                                html.Div([
                                                    html.Label(texts["default_aggregation_function"], htmlFor="agg-function", className="form-label mb-2"),
                                                    dbc.Select(
                                                        id="agg-function",
                                                        name="agg-function",
                                                        options=[
                                                            {"label": texts["sum"], "value": "sum"},
                                                            {"label": texts["avg"], "value": "avg"},
                                                            {"label": texts["count"], "value": "count"},
                                                            {"label": texts["max"], "value": "max"},
                                                            {"label": texts["min"], "value": "min"},
                                                            {"label": texts["percentage"], "value": "percentage"},
                                                        ],
                                                        value="sum",
                                                        className="mb-3",
                                                    ),
                                                ]),
                                                html.Div(id="field-agg-functions", children=[
                                                    html.Label(texts["field_aggregation_function"], className="form-label mb-2"),
                                                    html.P(texts["field_aggregation_hint"], 
                                                          className="text-muted small mb-2"),
                                                ]),
                                            ]
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                            ]),
                            
                            # 样式配置
                            dbc.Card(
                                [
                                    dbc.CardHeader(texts["style_config"], id="style-config-header"),
                                    dbc.CardBody(
                                        [
                                            html.Label(texts["chart_title"], htmlFor="chart-title", className="form-label"),
                                            dbc.Input(
                                                id="chart-title", 
                                                name="chart-title",
                                                placeholder=texts["enter_chart_title"], 
                                                type="text", 
                                                className="mb-3", 
                                                autoComplete="off"
                                            ),
                                            html.Label(texts["color_theme"], htmlFor="color-theme", className="form-label"),
                                            dbc.Select(
                                                id="color-theme",
                                                name="color-theme",
                                                options=[
                                                    {"label": texts["default"], "value": "default"},
                                                    {"label": texts["business_blue"], "value": "blue"},
                                                    {"label": texts["vibrant_orange"], "value": "orange"},
                                                    {"label": texts["natural_green"], "value": "green"},
                                                    {"label": texts["purple"], "value": "purple"},
                                                ],
                                                value="default",
                                                className="mb-3",
                                            ),
                                            # 自定义颜色配置
                                            html.Div(id="custom-colors-section", children=[
                                                html.Hr(className="my-3"),
                                                html.Label(texts["custom_color_config"], className="form-label fw-bold"),
                                                html.P(texts["custom_color_hint"], className="text-muted small mb-3"),
                                                html.Div(id="custom-colors-list", children=[
                                                    html.P(texts["set_group_field_first"], className="text-muted text-center py-3"),
                                                ]),
                                            ], style={"display": "none"}),
                                            html.Label(texts.get("chart_options", "图表选项"), htmlFor="chart-options", className="form-label", style={"display": "none"}),
                                            dbc.Checklist(
                                                options=[
                                                    {"label": texts["show_labels"], "value": "show-labels"},
                                                    {"label": texts["show_legend"], "value": "show-legend"},
                                                ],
                                                value=["show-legend"],
                                                id="chart-options",
                                                name="chart-options",
                                            ),
                                        ]
                                    ),
                                ],
                            ),
                        ],
                        width=3,
                    ),
                    
                    # 中间：已保存图表管理
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.Span(texts["saved_charts"], id="saved-charts-header", className="me-auto"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        [html.I(className="fas fa-plus me-1"), texts["add"]],
                                                        id="btn-new-chart",
                                                        color="success",
                                                        size="sm",
                                                        outline=True
                                                    ),
                                                    dbc.Button(
                                                        [html.I(className="fas fa-sync me-1"), texts["refresh"]],
                                                        id="btn-refresh-saved-charts",
                                                        color="link",
                                                        size="sm",
                                                        className="p-0"
                                                    ),
                                                ],
                                                className="d-flex gap-1",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="saved-charts-list", children=[
                                                html.P(texts["loading"], className="text-muted text-center py-3"),
                                            ]),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                                style={"maxHeight": "600px", "overflowY": "auto"},
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
                                            html.Span(texts["chart_preview"], id="chart-preview-header", className="me-auto"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(texts["save_chart"], id="btn-save-chart", color="success", size="sm"),
                                                    dbc.Button(texts["export_image"], id="btn-export-chart-image", color="info", size="sm"),
                                                ],
                                                className="float-end",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Store(id="current-chart-config", data=None),
                                            dcc.Store(id="current-chart-figure", data=None),
                                            dcc.Store(id="editing-chart-id", data=None),
                                            html.Div(id="chart-save-status", children=[], className="mb-2"),
                                            html.Div(id="chart-preview", children=[
                                                html.P(texts["select_datasource_and_config"], id="preview-hint", className="text-muted text-center py-5"),
                                            ]),
                                        ]
                                    ),
                                ],
                                style={"height": "100%"},
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


def _generate_chart_cards(charts):
    """生成图表卡片列表的辅助函数"""
    texts = language_manager.get_all_texts()
    if not charts:
        return html.P(texts["no_saved_charts"], className="text-muted text-center py-3")
    
    # 按创建时间倒序排序（最新的在前）
    def get_sort_key(chart):
        created_at = chart.get('created_at', '')
        if created_at:
            try:
                # 尝试解析ISO格式的时间
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                return created_dt.timestamp()
            except:
                # 如果解析失败，使用字符串比较
                return created_at
        return ''
    
    sorted_charts = sorted(charts, key=get_sort_key, reverse=True)
    
    chart_cards = []
    chart_type_names = {
        'line': texts['line_chart'],
        'bar': texts['bar_chart'],
        'pie': texts['pie_chart'],
        'table': texts['table'],
        'combo': texts['combo_chart']
    }
    
    for chart in sorted_charts:
        chart_id_item = chart.get('id')
        chart_name_item = chart.get('name', chart.get('title', texts['unnamed_chart']))
        chart_type_item = chart.get('type', 'line')
        chart_type_name = chart_type_names.get(chart_type_item, chart_type_item)
        created_at = chart.get('created_at', '')
        
        try:
            if created_at:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = created_dt.strftime('%Y-%m-%d %H:%M')
            else:
                created_str = texts['unknown']
        except:
            created_str = created_at[:16] if created_at else texts['unknown']
        
        chart_card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.H6(chart_name_item, className="mb-1 fw-bold"),
                                html.P(texts["chart_type_colon"].format(chart_type_name), className="mb-1 small text-muted"),
                                html.P(texts["created_colon"].format(created_str), className="mb-2 small text-muted"),
                            ],
                            className="mb-2"
                        ),
                        dbc.ButtonGroup(
                            [
                                dbc.Button(
                                    [html.I(className="fas fa-edit me-1"), texts["edit"]],
                                    id={"type": "edit-saved-chart", "chart_id": chart_id_item},
                                    color="primary",
                                    size="sm",
                                    className="flex-fill"
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-trash me-1"), texts["delete"]],
                                    id={"type": "delete-saved-chart", "chart_id": chart_id_item},
                                    color="danger",
                                    size="sm",
                                    className="flex-fill"
                                ),
                            ],
                            className="w-100",
                            vertical=False,
                        ),
                    ],
                    className="p-2"
                ),
            ],
            className="mb-2",
            style={"border": "1px solid #dee2e6", "borderRadius": "6px"}
        )
        chart_cards.append(chart_card)
    
    return html.Div(chart_cards)


def register_chart_designer_callbacks(app, config_manager, data_source_manager, chart_engine, export_dir):
    """注册图表设计器页面的所有回调函数"""
    from typing import List, Any
    import pandas as pd
    from datetime import datetime
    
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
            # 初始加载时不自动选择数据源，显示空图表
            selected = None
            if not options:
                texts = language_manager.get_all_texts()
                options = [{"label": texts["please_add_datasource_first"], "value": None, "disabled": True}]
            return options, selected
        return [], None

    @app.callback(
        Output("saved-charts-list", "children"),
        [Input("url", "pathname"),
         Input("btn-refresh-saved-charts", "n_clicks")],
        prevent_initial_call=False
    )
    def load_saved_charts_list(pathname, refresh_clicks):
        """加载已保存的图表列表"""
        if pathname != "/chart-designer":
            return dash.no_update
        
        charts = config_manager.load_charts()
        return _generate_chart_cards(charts)

    @app.callback(
        [Output("editing-chart-id", "data", allow_duplicate=True),
         Output("chart-datasource-select", "value", allow_duplicate=True),
         Output("chart-type", "value", allow_duplicate=True),
         Output("chart-field-assignments", "data", allow_duplicate=True),
         Output("agg-function", "value", allow_duplicate=True),
         Output("field-agg-functions-config", "data", allow_duplicate=True),
         Output("chart-title", "value", allow_duplicate=True),
         Output("color-theme", "value", allow_duplicate=True),
         Output("chart-options", "value", allow_duplicate=True),
         Output("custom-colors-config", "data", allow_duplicate=True),
         Output("table-orientation", "value", allow_duplicate=True),
         Output("chart-save-status", "children", allow_duplicate=True)],
        Input("url", "pathname"),
        State("editing-chart-id", "data"),
        prevent_initial_call='initial_duplicate'
    )
    def initialize_chart_designer(pathname, current_editing_id):
        """初始化图表设计器 - 进入页面时自动显示空图表"""
        # 只有进入图表设计器页面时才执行
        if pathname != "/chart-designer":
            return [dash.no_update] * 12
        
        # 如果正在编辑某个图表，不清空（保持编辑状态）
        # 如果没有任何编辑状态，自动清空并显示空图表
        if current_editing_id is not None:
            # 正在编辑图表，不清空
            return [dash.no_update] * 12
        
        # 重置为默认值（空图表状态）
        assignments = default_chart_assignments()
        
        return (
            None,  # editing-chart-id: 清空编辑状态
            None,  # chart-datasource-select: 清空数据源选择
            "line",  # chart-type: 默认折线图
            assignments,  # chart-field-assignments: 重置字段配置
            "sum",  # agg-function: 默认求和
            {},  # field-agg-functions-config: 清空字段聚合函数配置
            "",  # chart-title: 清空标题
            "default",  # color-theme: 默认主题
            ["show-legend"],  # chart-options: 默认只显示图例
            {},  # custom-colors-config: 清空自定义颜色
            "horizontal",  # table-orientation: 默认横向
            html.P("", className="mb-0")  # chart-save-status: 清空状态信息
        )

    @app.callback(
        [Output("editing-chart-id", "data", allow_duplicate=True),
         Output("chart-datasource-select", "value", allow_duplicate=True),
         Output("chart-type", "value", allow_duplicate=True),
         Output("chart-field-assignments", "data", allow_duplicate=True),
         Output("agg-function", "value", allow_duplicate=True),
         Output("field-agg-functions-config", "data", allow_duplicate=True),
         Output("chart-title", "value", allow_duplicate=True),
         Output("color-theme", "value", allow_duplicate=True),
         Output("chart-options", "value", allow_duplicate=True),
         Output("custom-colors-config", "data", allow_duplicate=True),
         Output("table-orientation", "value", allow_duplicate=True),
         Output("chart-save-status", "children", allow_duplicate=True)],
        [Input({"type": "edit-saved-chart", "chart_id": ALL}, "n_clicks")],
        prevent_initial_call=True
    )
    def load_chart_for_edit(edit_clicks):
        """加载图表配置到设计器（编辑）"""
        ctx = callback_context
        if not ctx.triggered:
            return [dash.no_update] * 12
        
        trigger_id = ctx.triggered[0]["prop_id"]
        
        try:
            if "edit-saved-chart" not in trigger_id:
                return [dash.no_update] * 12
            
            chart_id_dict = json.loads(trigger_id.split(".")[0])
            chart_id = chart_id_dict.get("chart_id")
            
            chart_config = config_manager.get_chart(chart_id)
            if not chart_config:
                texts = language_manager.get_all_texts()
                return (
                    dash.no_update,  # editing-chart-id
                    dash.no_update,  # chart-datasource-select
                    dash.no_update,  # chart-type
                    dash.no_update,  # chart-field-assignments
                    dash.no_update,  # agg-function
                    dash.no_update,  # field-agg-functions-config
                    dash.no_update,  # chart-title
                    dash.no_update,  # color-theme
                    dash.no_update,  # chart-options
                    dash.no_update,  # custom-colors-config
                    dash.no_update,  # table-orientation
                    dbc.Alert(texts["chart_not_found"], color="danger", className="m-2")  # chart-save-status
                )
            
            assignments = default_chart_assignments()
            assignments['x'] = chart_config.get('x')
            y_value = chart_config.get('y')
            if isinstance(y_value, list):
                assignments['y'] = y_value
            elif y_value:
                assignments['y'] = [y_value]
            assignments['group'] = chart_config.get('group')
            assignments['table_columns'] = chart_config.get('table_columns', [])
            assignments['table_rows'] = chart_config.get('table_rows', [])
            table_orientation = chart_config.get('table_orientation', 'horizontal')
            assignments['table_orientation'] = table_orientation
            
            options = []
            if chart_config.get('show_labels', False):
                options.append('show-labels')
            if chart_config.get('show_legend', True):
                options.append('show-legend')
            
            texts = language_manager.get_all_texts()
            return (
                chart_id,
                chart_config.get('datasource_id'),
                chart_config.get('type', 'line'),
                assignments,
                chart_config.get('agg_function', 'sum'),
                chart_config.get('agg_functions', {}),  # 加载字段聚合函数配置
                chart_config.get('title', chart_config.get('name', '')),
                chart_config.get('color_theme', 'default'),
                options,
                chart_config.get('custom_colors', {}),
                table_orientation,
                dbc.Alert(texts["chart_config_loaded"], color="success", className="m-2")
            )
        except Exception as e:
            texts = language_manager.get_all_texts()
            return (
                dash.no_update,  # editing-chart-id
                dash.no_update,  # chart-datasource-select
                dash.no_update,  # chart-type
                dash.no_update,  # chart-field-assignments
                dash.no_update,  # agg-function
                dash.no_update,  # field-agg-functions-config
                dash.no_update,  # chart-title
                dash.no_update,  # color-theme
                dash.no_update,  # chart-options
                dash.no_update,  # custom-colors-config
                dash.no_update,  # table-orientation
                dbc.Alert(texts["load_chart_failed"].format(str(e)), color="danger", className="m-2")  # chart-save-status
            )
        
        return [dash.no_update] * 12

    @app.callback(
        [Output("saved-charts-list", "children", allow_duplicate=True),
         Output("chart-save-status", "children", allow_duplicate=True)],
        Input({"type": "delete-saved-chart", "chart_id": ALL}, "n_clicks"),
        prevent_initial_call=True
    )
    def delete_saved_chart(delete_clicks):
        """删除已保存的图表"""
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"]
        trigger_value = ctx.triggered[0]["value"]
        
        if trigger_value is None:
            return dash.no_update, dash.no_update
        
        try:
            if "delete-saved-chart" in trigger_id:
                chart_id_dict = json.loads(trigger_id.split(".")[0])
                chart_id = chart_id_dict.get("chart_id")
                
                if isinstance(trigger_value, list):
                    clicked_indices = []
                    for i, v in enumerate(trigger_value):
                        if v is not None and isinstance(v, (int, float)) and v > 0:
                            clicked_indices.append(i)
                    
                    if not clicked_indices:
                        return dash.no_update, dash.no_update
                    
                    charts = config_manager.load_charts()
                    clicked_index = clicked_indices[0]
                    if clicked_index >= len(charts):
                        return dash.no_update, dash.no_update
                    clicked_chart = charts[clicked_index]
                    if clicked_chart.get('id') != chart_id:
                        return dash.no_update, dash.no_update
                
                texts = language_manager.get_all_texts()
                chart_config = config_manager.get_chart(chart_id)
                if chart_config:
                    chart_name = chart_config.get('name', texts['unnamed_chart'])
                    config_manager.delete_chart(chart_id)
                    
                    charts = config_manager.load_charts()
                    charts_list = _generate_chart_cards(charts)
                    
                    texts = language_manager.get_all_texts()
                    return charts_list, dbc.Alert(texts["chart_deleted"].format(chart_name), color="success", className="m-2")
        except Exception as e:
            import traceback
            traceback.print_exc()
            texts = language_manager.get_all_texts()
            return dash.no_update, dbc.Alert(texts["delete_failed"].format(str(e)), color="danger", className="m-2")
        
        return dash.no_update, dash.no_update

    @app.callback(
        [Output("field-list", "children"),
         Output("chart-field-assignments", "data", allow_duplicate=True)],
        Input("chart-datasource-select", "value"),
        prevent_initial_call="initial_duplicate"
    )
    def load_datasource_fields(datasource_id):
        """根据数据源加载可拖拽字段列表"""
        texts = language_manager.get_all_texts()
        assignments = default_chart_assignments()
        if not datasource_id:
            return html.P(texts["select_datasource_to_view_fields"], className="text-muted mb-0"), assignments
        try:
            ds_config = config_manager.get_datasource(datasource_id)
            if not ds_config:
                texts = language_manager.get_all_texts()
                return html.P(texts["datasource_not_found"], className="text-danger mb-0"), assignments
            adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
            schema = adapter.get_schema()
            columns = schema.get('columns', []) if isinstance(schema, dict) else []
            if not columns:
                texts = language_manager.get_all_texts()
                return html.P(texts["no_fields_detected"], className="text-muted mb-0"), assignments
            type_labels = {
                'date': texts['field_type_date'],
                'datetime64[ns]': texts['field_type_date'],
                'numeric': texts['field_type_numeric'],
                'integer': texts['field_type_numeric'],
                'text': texts['field_type_text']
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
                texts = language_manager.get_all_texts()
                return html.P(texts["no_fields_detected_simple"], className="text-muted mb-0"), assignments
            return html.Div(badges, className="d-flex flex-wrap"), assignments
        except Exception as exc:
            texts = language_manager.get_all_texts()
            return dbc.Alert(texts["load_fields_failed"].format(str(exc)), color="danger"), assignments

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
        """根据图表类型显示/隐藏不同的配置界面"""
        texts = language_manager.get_all_texts()
        if chart_type == "table":
            return {"display": "none"}, {"display": "block"}, {"display": "none"}, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif chart_type == "pie":
            return (
                {"display": "block"},
                {"display": "none"},
                {"display": "block"},
                {"display": "none"},
                texts["numeric_field_required"],
                texts["hint_drag_numeric_field"],
                texts["category_field_required"],
                texts["hint_drag_category_field"]
            )
        else:
            return (
                {"display": "block"},
                {"display": "none"},
                {"display": "block"},
                {"display": "block"},
                texts["y_axis_label"],
                texts["hint_drag_field_below"],
                texts["group_color_label"],
                texts["hint_drag_field_below"]
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
        """根据表格方向显示列或行配置"""
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
        """根据字段配置更新拖拽区域显示"""
        if chart_type == "table":
            return dash.no_update, dash.no_update, dash.no_update
        assignments = assignments or default_chart_assignments()
        texts = language_manager.get_all_texts()
        return (
            render_assigned_fields(assignments.get('x'), texts["drag_field_here"]),
            render_assigned_fields(assignments.get('y'), texts["drag_field_here"], multiple=True),
            render_assigned_fields(assignments.get('group'), texts["drag_field_here"]),
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
        
        if not group_field or chart_type == "table":
            texts = language_manager.get_all_texts()
            return {"display": "none"}, html.P(texts["set_group_field_first"], className="text-muted text-center py-3")
        
        if not datasource_id:
            texts = language_manager.get_all_texts()
            return {"display": "none"}, html.P(texts["select_datasource_first"], className="text-muted text-center py-3")
        
        try:
            ds_config = config_manager.get_datasource(datasource_id)
            if not ds_config:
                texts = language_manager.get_all_texts()
                return {"display": "none"}, html.P(texts["datasource_not_found"], className="text-muted text-center py-3")
            
            adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
            df = adapter.fetch_data(limit=1000)
            
            if df is None or df.empty or group_field not in df.columns:
                texts = language_manager.get_all_texts()
                return {"display": "none"}, html.P(texts["cannot_load_group_data"], className="text-muted text-center py-3")
            
            unique_groups = sorted(df[group_field].dropna().unique().tolist())
            custom_colors = custom_colors or {}
            
            color_inputs = []
            default_colors = [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
            ]
            
            for i, group_val in enumerate(unique_groups):
                group_val_str = str(group_val)
                current_color = custom_colors.get(group_val_str, default_colors[i % len(default_colors)])
                
                # 为动态创建的输入字段生成唯一ID字符串用于htmlFor
                color_input_id_str = f"custom-color-input-{group_val_str}"
                color_inputs.append(
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Label(f"{group_val}", htmlFor=color_input_id_str, className="form-label mb-1 small"),
                            ], width=4),
                            dbc.Col([
                                dbc.Input(
                                    id={"type": "custom-color-input", "group": group_val_str},
                                    name=f"color-{group_val_str}",
                                    type="color",
                                    value=current_color,
                                    className="form-control form-control-color",
                                    style={"width": "100%", "height": "38px"},
                                    autoComplete="off"
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
                texts = language_manager.get_all_texts()
                return {"display": "none"}, html.P(texts["load_group_data_failed"].format(str(e)), className="text-danger text-center py-3")

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
        
        current_colors = current_colors or {}
        new_colors = current_colors.copy()
        
        for i, color_id in enumerate(color_ids):
            if i < len(color_values):
                group_val = color_id.get('group', '')
                if group_val and color_values[i]:
                    new_colors[group_val] = color_values[i]
        
        display_values = [new_colors.get(id.get('group', ''), '#000000') for id in color_ids]
        
        return new_colors, display_values

    # 使用ClientsideCallback将事件数据传递到Store
    app.clientside_callback(
        """
        function(n_clicks) {
            try {
                if (!n_clicks || n_clicks === 0) {
                    return window.dash_clientside ? window.dash_clientside.no_update : null;
                }
                // 从全局变量读取事件数据
                const eventData = (window._dndEventData || "").toString();
                if (!eventData || eventData === "") {
                    console.warn("ClientsideCallback: 没有事件数据");
                    return window.dash_clientside ? window.dash_clientside.no_update : null;
                }
                console.log("ClientsideCallback触发: n_clicks=", n_clicks, "eventData=", eventData);
                // 清空全局变量
                window._dndEventData = "";
                return eventData;
            } catch (e) {
                console.error("ClientsideCallback错误:", e);
                return window.dash_clientside ? window.dash_clientside.no_update : null;
            }
        }
        """,
        Output("dnd-last-event", "data"),
        Input("dnd-event-trigger", "n_clicks"),
        prevent_initial_call=True
    )

    @app.callback(
        Output("chart-field-assignments", "data", allow_duplicate=True),
        Input("dnd-last-event", "data"),
        State("chart-field-assignments", "data"),
        prevent_initial_call=True
    )
    def handle_drag_drop_event(event_payload, assignments):
        """处理前端拖拽事件，更新字段配置"""
        logger.debug(f"收到拖拽事件: event_payload={event_payload}")
        if not event_payload:
            logger.debug("拖拽事件为空，跳过")
            raise dash.exceptions.PreventUpdate
        
        event_str = event_payload
        if '|' in event_str:
            event_str = event_str.split('|')[0]
        
        try:
            event = json.loads(event_str)
            logger.debug(f"解析拖拽事件成功: {event}")
        except json.JSONDecodeError as e:
            logger.warning(f"解析拖拽事件失败: {event_str}, 错误: {e}")
            raise dash.exceptions.PreventUpdate
        
        field = event.get('field')
        target = event.get('target')
        logger.debug(f"拖拽字段: {field}, 目标: {target}")
        
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
            col_index_str = target.replace('drop-table-col-', '')
            try:
                col_index = int(col_index_str)
                if field in new_assignments['table_columns']:
                    new_assignments['table_columns'].remove(field)
                col_pos = col_index - 1
                if col_pos < len(new_assignments['table_columns']):
                    new_assignments['table_columns'].insert(col_pos, field)
                else:
                    new_assignments['table_columns'].append(field)
            except (ValueError, IndexError):
                pass
            return new_assignments
        elif target and target.startswith('drop-table-row-'):
            row_index_str = target.replace('drop-table-row-', '')
            try:
                row_index = int(row_index_str)
                if field in new_assignments['table_rows']:
                    new_assignments['table_rows'].remove(field)
                row_pos = row_index - 1
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
            logger.info(f"字段 {field} 已分配到X轴")
        elif target == 'drop-y-axis':
            if field not in new_assignments['y']:
                new_assignments['y'].append(field)
                logger.info(f"字段 {field} 已添加到Y轴")
        elif target == 'drop-group':
            new_assignments['group'] = field
            logger.info(f"字段 {field} 已分配到分组")
        else:
            logger.warning(f"未知的拖拽目标: {target}")
        logger.debug(f"更新后的字段配置: {new_assignments}")
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
        texts = language_manager.get_all_texts()
        
        if trigger_id == "btn-add-table-column":
            new_col_index = len(table_columns) + 1
            col_div = html.Div([
                html.P(texts["drag_field_as_column_n"].format(new_col_index), className="text-muted text-center mb-2 small"),
                html.Div(
                    id={"type": "drop-table-col", "index": new_col_index},
                    children=[html.P("拖拽字段到此处", className="text-muted text-center mb-0")],
                    style={
                        "minHeight": "50px",
                        "marginBottom": "10px",
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
            new_row_index = len(table_rows) + 1
            row_div = html.Div([
                html.P(texts["drag_field_as_row_n"].format(new_row_index), className="text-muted text-center mb-2 small"),
                html.Div(
                    id={"type": "drop-table-row", "index": new_row_index},
                    children=[html.P("拖拽字段到此处", className="text-muted text-center mb-0")],
                    style={
                        "minHeight": "50px",
                        "marginBottom": "10px",
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
                html.P(texts["column_n"].format(i+1, col), className="text-muted text-center mb-2 small"),
                html.Div(
                    id=f"drop-table-col-{i+1}",
                    children=[dbc.Badge(col, color="secondary", pill=True)],
                    style={
                        "minHeight": "50px",
                        "marginBottom": "10px",
                        "border": "2px dashed #ced4da",
                        "borderRadius": "6px",
                        "padding": "0.5rem"
                    },
                    className="drop-zone",
                ),
            ]))
        cols_list.append(html.Div([
            html.P(texts["drag_field_as_column_n"].format(len(table_columns)+1), className="text-muted text-center mb-2 small"),
            html.Div(
                id=f"drop-table-col-{len(table_columns)+1}",
                children=[html.P("拖拽字段到此处", className="text-muted text-center mb-0")],
                style={
                    "minHeight": "50px",
                    "marginBottom": "10px",
                    "border": "2px dashed #ced4da",
                    "borderRadius": "6px",
                    "padding": "0.5rem"
                },
                className="drop-zone",
            ),
        ]))
        
        texts = language_manager.get_all_texts()
        rows_list = []
        for i, row in enumerate(table_rows):
            rows_list.append(html.Div([
                html.P(texts["row_n"].format(i+1, row), className="text-muted text-center mb-2 small"),
                html.Div(
                    id=f"drop-table-row-{i+1}",
                    children=[dbc.Badge(row, color="secondary", pill=True)],
                    style={
                        "minHeight": "50px",
                        "marginBottom": "10px",
                        "border": "2px dashed #ced4da",
                        "borderRadius": "6px",
                        "padding": "0.5rem"
                    },
                    className="drop-zone",
                ),
            ]))
        rows_list.append(html.Div([
            html.P(texts["drag_field_as_row_n"].format(len(table_rows)+1), className="text-muted text-center mb-2 small"),
            html.Div(
                id=f"drop-table-row-{len(table_rows)+1}",
                children=[html.P("拖拽字段到此处", className="text-muted text-center mb-0")],
                style={
                    "minHeight": "50px",
                    "marginBottom": "10px",
                    "border": "2px dashed #ced4da",
                    "borderRadius": "6px",
                    "padding": "0.5rem"
                },
                className="drop-zone",
            ),
        ]))
        
        return cols_list, rows_list

    @app.callback(
        Output("field-agg-functions", "children"),
        [Input("chart-field-assignments", "data"),
         Input("agg-function", "value")],
        State("field-agg-functions-config", "data"),
        prevent_initial_call=False
    )
    def update_field_agg_functions_ui(assignments, default_agg_function, field_agg_config):
        """根据Y轴字段动态生成每个字段的聚合函数选择器"""
        assignments = assignments or default_chart_assignments()
        y_fields = assignments.get('y', [])
        field_agg_config = field_agg_config or {}
        default_agg_function = default_agg_function or 'sum'
        
        texts = language_manager.get_all_texts()
        if not y_fields or len(y_fields) == 0:
            return html.P(texts["add_y_axis_field_first"], className="text-muted small mb-2")
        
        # 为每个Y轴字段创建一个聚合函数选择器
        field_selectors = []
        for field in y_fields:
            current_func = field_agg_config.get(field, default_agg_function)
            # 为动态创建的Select生成唯一ID字符串用于htmlFor
            select_id_str = f"field-agg-function-{field}"
            field_selectors.append(
                dbc.Row([
                    dbc.Col([
                        html.Label(f"{field}:", htmlFor=select_id_str, className="form-label small mb-1"),
                        dbc.Select(
                            id={"type": "field-agg-function", "field": field},
                            name=f"agg-function-{field}",
                            options=[
                                {"label": texts["sum"], "value": "sum"},
                                {"label": texts["avg"], "value": "avg"},
                                {"label": texts["count"], "value": "count"},
                                {"label": texts["max"], "value": "max"},
                                {"label": texts["min"], "value": "min"},
                                {"label": texts["percentage"], "value": "percentage"},
                            ],
                            value=current_func,
                            size="sm",
                        ),
                    ], width=12, className="mb-2"),
                ], className="mb-2")
            )
        
        return html.Div(field_selectors)

    @app.callback(
        Output("field-agg-functions-config", "data", allow_duplicate=True),
        [Input({"type": "field-agg-function", "field": ALL}, "value")],
        [State({"type": "field-agg-function", "field": ALL}, "id"),
         State("field-agg-functions-config", "data")],
        prevent_initial_call=True
    )
    def update_field_agg_functions_config(field_funcs, field_ids, current_config):
        """更新字段聚合函数配置"""
        current_config = current_config or {}
        new_config = current_config.copy()
        
        for field_id, func_value in zip(field_ids, field_funcs):
            if isinstance(field_id, dict) and 'field' in field_id:
                field_name = field_id['field']
                new_config[field_name] = func_value
        
        return new_config

    @app.callback(
        Output("chart-preview", "children"),
        [Input("chart-datasource-select", "value"),
         Input("chart-type", "value"),
         Input("chart-field-assignments", "data"),
         Input("agg-function", "value"),
         Input("field-agg-functions-config", "data"),
         Input("chart-title", "value"),
         Input("color-theme", "value"),
         Input("chart-options", "value"),
         Input("table-orientation", "value"),
         Input("custom-colors-config", "data")],
        prevent_initial_call=False
    )
    def update_chart_preview(datasource_id, chart_type, assignments, agg_function, field_agg_functions, title, color_theme, options, table_orientation, custom_colors):
        """根据当前配置生成预览图表"""
        texts = language_manager.get_all_texts()
        try:
            if not datasource_id:
                return html.P(texts["select_datasource"], className="text-muted text-center py-5")
            ds_config = config_manager.get_datasource(datasource_id)
            if not ds_config:
                return html.P(texts["datasource_not_found"], className="text-muted text-center py-5")
            adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
            df = adapter.fetch_data(limit=1000)
            if df is None or df.empty:
                return html.P(texts["data_empty_cannot_generate"], className="text-muted text-center py-5")
            assignments = assignments or default_chart_assignments()
            options = options or []
            
            if chart_type == 'table':
                table_columns = assignments.get('table_columns', []) if assignments else []
                table_rows = assignments.get('table_rows', []) if assignments else []
                if table_orientation:
                    if assignments:
                        assignments['table_orientation'] = table_orientation
                else:
                    table_orientation = assignments.get('table_orientation', 'horizontal') if assignments else 'horizontal'
                
                if table_orientation == 'horizontal':
                    if not table_columns:
                        return html.P(texts["drag_field_to_table_columns"], className="text-muted text-center py-5")
                    selected_columns = [col for col in table_columns if col in df.columns]
                    if not selected_columns:
                        return html.P(texts["field_not_in_data"], className="text-muted text-center py-5")
                    result = df[selected_columns]
                    if isinstance(result, pd.Series):
                        table_df: pd.DataFrame = result.to_frame()
                    else:
                        table_df = result
                    assert isinstance(table_df, pd.DataFrame), "table_df must be a DataFrame"
                else:
                    if not table_rows:
                        return html.P(texts["drag_field_to_table_rows"], className="text-muted text-center py-5")
                    selected_rows = [row for row in table_rows if row in df.columns]
                    if not selected_rows:
                        return html.P(texts["field_not_in_data"], className="text-muted text-center py-5")
                    transposed = df[selected_rows].T
                    if isinstance(transposed, pd.Series):
                        table_df = transposed.to_frame()
                    else:
                        table_df = transposed
                    assert isinstance(table_df, pd.DataFrame), "table_df must be a DataFrame"
                    # 使用通用的列名，避免硬编码中文
                    table_df.columns = [f'Col{i+1}' for i in range(len(table_df.columns))]
                
                chart_config = {
                    "type": "table",
                    "title": title or texts["data_table"],
                    "limit": 100,
                }
                fig = chart_engine.create_chart(table_df, chart_config)
                return dcc.Graph(figure=fig, id="preview-chart")
            else:
                x_field = assignments.get('x')
                y_fields = assignments.get('y') or []
                group_field = assignments.get('group')
                
                if chart_type != 'pie' and not x_field:
                    return html.P(texts["drag_field_to_x_axis"], className="text-muted text-center py-5")
                if not y_fields:
                    return html.P(texts["at_least_one_y_axis"], className="text-muted text-center py-5")
                if chart_type == 'pie':
                    if not group_field and not x_field:
                        return html.P(texts["pie_needs_group_field"], className="text-muted text-center py-5")
                    if not y_fields:
                        return html.P(texts["pie_needs_numeric_field"], className="text-muted text-center py-5")
                    if not group_field:
                        group_field = x_field
                
                # 验证字段是否存在于数据中
                if x_field and x_field not in df.columns:
                    return html.P(texts["field_not_in_data"].format(x_field), className="text-muted text-center py-5")
                for y_field in y_fields:
                    if y_field and y_field not in df.columns:
                        return html.P(texts["field_not_in_data"].format(y_field), className="text-muted text-center py-5")
                if group_field and group_field not in df.columns:
                    return html.P(texts["field_not_in_data"].format(group_field), className="text-muted text-center py-5")
                
                chart_config = {
                    "type": chart_type or "line",
                    "x": x_field,
                    "y": y_fields if len(y_fields) > 1 else (y_fields[0] if y_fields else None),
                    "group": group_field,
                    "title": title or texts["chart_preview"],
                    "color_theme": color_theme or "default",
                    "custom_colors": custom_colors or {},
                    "show_labels": "show-labels" in options,
                    "show_legend": "show-legend" in options,
                    "agg_function": agg_function or "sum",
                    "agg_functions": field_agg_functions or {},  # 各字段的聚合函数配置
                }
                fig = chart_engine.create_chart(df, chart_config)
                logger.debug(f"图表预览生成成功 [类型: {chart_type}, 数据行数: {len(df)}]")
                return dcc.Graph(figure=fig, id="preview-chart")
        except KeyError as e:
            # 字段不存在错误
            missing_field = str(e).strip("'\"")
            logger.warning(f"图表预览生成失败：字段不存在 [字段: {missing_field}, 类型: {chart_type}]")
            texts = language_manager.get_all_texts()
            return dbc.Alert(f"{texts.get('field_not_in_data', '字段不存在')}: {missing_field}", color="warning")
        except Exception as e:
            logger.error(f"图表预览生成失败 [类型: {chart_type}]: {str(e)}", exc_info=True)
            texts = language_manager.get_all_texts()
            return dbc.Alert(f"{texts.get('generate_chart_failed', '生成图表失败')}：{str(e)}", color="danger")

    @app.callback(
        [Output("current-chart-config", "data", allow_duplicate=True),
         Output("chart-save-status", "children", allow_duplicate=True),
         Output("saved-charts-list", "children", allow_duplicate=True),
         Output("editing-chart-id", "data", allow_duplicate=True)],
        [Input("btn-save-chart", "n_clicks")],
        [State("chart-datasource-select", "value"),
         State("chart-type", "value"),
         State("chart-field-assignments", "data"),
         State("agg-function", "value"),
         State("field-agg-functions-config", "data"),
         State("chart-title", "value"),
         State("color-theme", "value"),
         State("chart-options", "value"),
         State("custom-colors-config", "data"),
         State("editing-chart-id", "data")],
        prevent_initial_call=True
    )
    def save_chart(save_clicks, datasource_id, chart_type, assignments, agg_function, field_agg_functions, title, color_theme, options, custom_colors, editing_id):
        """保存图表配置"""
        texts = language_manager.get_all_texts()
        if not datasource_id:
            return dash.no_update, dbc.Alert(texts["select_datasource_first"], color="warning", className="m-2"), dash.no_update, dash.no_update
        try:
            ds_config = config_manager.get_datasource(datasource_id)
            if not ds_config:
                return dash.no_update, dbc.Alert(texts["datasource_not_found"], color="warning", className="m-2"), dash.no_update, dash.no_update
            adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
            df = adapter.fetch_data(limit=1000)
            if df is None or df.empty:
                return dash.no_update, dbc.Alert(texts["data_empty"], color="warning", className="m-2"), dash.no_update, dash.no_update
            assignments = assignments or default_chart_assignments()
            x_field = assignments.get('x')
            y_fields = assignments.get('y') or []
            if chart_type != 'table' and not x_field and chart_type != 'pie':
                return dash.no_update, dbc.Alert(texts["drag_field_to_x_axis"], color="warning", className="m-2"), dash.no_update, dash.no_update
            if not y_fields and chart_type != 'table':
                return dash.no_update, dbc.Alert(texts["at_least_one_y_axis"], color="warning", className="m-2"), dash.no_update, dash.no_update
            options = options or []
            chart_config = {
                "datasource_id": datasource_id,
                "type": chart_type or "line",
                "x": x_field,
                "y": y_fields if len(y_fields) > 1 else (y_fields[0] if y_fields else None),
                "group": assignments.get('group'),
                "title": title or texts["chart_preview"],
                "color_theme": color_theme or "default",
                "custom_colors": custom_colors or {},
                "show_labels": "show-labels" in options,
                "show_legend": "show-legend" in options,
                "agg_function": agg_function or "sum",
                "agg_functions": field_agg_functions or {},  # 各字段的聚合函数配置
            }
            
            if chart_type == 'table':
                chart_config['table_columns'] = assignments.get('table_columns', [])
                chart_config['table_rows'] = assignments.get('table_rows', [])
                chart_config['table_orientation'] = assignments.get('table_orientation', 'horizontal')
            
            chart_config['name'] = title or texts["unnamed_chart"]
            
            # 如果正在编辑已有图表，保留图表ID以便更新
            if editing_id:
                chart_config['id'] = editing_id
            
            if config_manager.save_chart(chart_config):
                chart_name = chart_config.get('name', title or texts["unnamed_chart"])
                logger.info(f"用户保存图表 [ID: {chart_config.get('id')}, 名称: {chart_name}, 类型: {chart_type}]")
            else:
                logger.error(f"保存图表失败 [ID: {chart_config.get('id')}]")
            
            # 重新加载图表列表
            charts = config_manager.load_charts()
            logger.debug(f"重新加载图表列表: 共 {len(charts)} 个图表")
            charts_list = _generate_chart_cards(charts)
            logger.debug(f"图表列表已生成，包含 {len(charts)} 个图表卡片")
            
            # 如果正在编辑，重新加载更新后的图表配置
            if editing_id:
                updated_config = config_manager.get_chart(editing_id)
                if updated_config:
                    chart_config = updated_config
            
            # 保存成功后，保持当前编辑状态（用户可以继续编辑或点击"新增"创建新图表）
            return chart_config, dbc.Alert(texts["chart_saved_success"], color="success", className="m-2"), charts_list, editing_id
        except Exception as e:
            return dash.no_update, dbc.Alert(f"{texts['save_chart_failed']}：{str(e)}", color="danger", className="m-2"), dash.no_update, dash.no_update

    @app.callback(
        [Output("editing-chart-id", "data", allow_duplicate=True),
         Output("chart-datasource-select", "value", allow_duplicate=True),
         Output("chart-type", "value", allow_duplicate=True),
         Output("chart-field-assignments", "data", allow_duplicate=True),
         Output("agg-function", "value", allow_duplicate=True),
         Output("field-agg-functions-config", "data", allow_duplicate=True),
         Output("chart-title", "value", allow_duplicate=True),
         Output("color-theme", "value", allow_duplicate=True),
         Output("chart-options", "value", allow_duplicate=True),
         Output("custom-colors-config", "data", allow_duplicate=True),
         Output("table-orientation", "value", allow_duplicate=True),
         Output("chart-save-status", "children", allow_duplicate=True)],
        Input("btn-new-chart", "n_clicks"),
        prevent_initial_call=True
    )
    def create_new_chart(new_clicks):
        """创建新图表 - 清空所有配置"""
        if not new_clicks:
            return [dash.no_update] * 12
        
        texts = language_manager.get_all_texts()
        # 重置为默认值
        assignments = default_chart_assignments()
        
        return (
            None,  # editing-chart-id: 清空编辑状态
            None,  # chart-datasource-select: 清空数据源选择
            "line",  # chart-type: 默认折线图
            assignments,  # chart-field-assignments: 重置字段配置
            "sum",  # agg-function: 默认求和
            {},  # field-agg-functions-config: 清空字段聚合函数配置
            "",  # chart-title: 清空标题
            "default",  # color-theme: 默认主题
            ["show-legend"],  # chart-options: 默认只显示图例
            {},  # custom-colors-config: 清空自定义颜色
            "horizontal",  # table-orientation: 默认横向
            html.P(texts["new_chart_created"], className="text-muted text-center py-2")  # 提示信息
        )

    @app.callback(
        Output("chart-save-status", "children", allow_duplicate=True),
        [Input("btn-export-chart-image", "n_clicks"),
         Input("export-png", "n_clicks"),
         Input("export-pdf", "n_clicks"),
         Input("export-html", "n_clicks")],
        [         State("chart-datasource-select", "value"),
         State("chart-type", "value"),
         State("chart-field-assignments", "data"),
         State("agg-function", "value"),
         State("field-agg-functions-config", "data"),
         State("chart-title", "value"),
         State("color-theme", "value"),
         State("chart-options", "value"),
         State("custom-colors-config", "data")],
        prevent_initial_call=True
    )
    def export_chart(png_clicks, png_dropdown, pdf_clicks, html_clicks, 
                     datasource_id, chart_type, assignments, agg_function, field_agg_functions, title, color_theme, options, custom_colors):
        """导出图表"""
        ctx = callback_context
        if not ctx.triggered or not datasource_id:
            return dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        try:
            ds_config = config_manager.get_datasource(datasource_id)
            texts = language_manager.get_all_texts()
            if not ds_config:
                return dbc.Alert(texts["datasource_not_found"], color="warning", className="m-2")
            adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
            df = adapter.fetch_data(limit=1000)
            if df is None or df.empty:
                texts = language_manager.get_all_texts()
                return dbc.Alert(texts["data_empty"], color="warning", className="m-2")
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
                "agg_functions": field_agg_functions or {},  # 各字段的聚合函数配置
            }
            if chart_type == 'table':
                chart_config['limit'] = 100
            fig = chart_engine.create_chart(df, chart_config)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            chart_title = (title or "chart").replace(" ", "_").replace("/", "_")
            
            if trigger_id in ["btn-export-chart-image", "export-png"]:
                export_path = export_dir / f"{chart_title}_{timestamp}.png"
                fig.write_image(str(export_path), width=1200, height=600)
                return dbc.Alert(f"图表已导出为PNG：{export_path}", color="success", className="m-2")
            
            elif trigger_id == "export-pdf":
                export_path = export_dir / f"{chart_title}_{timestamp}.pdf"
                fig.write_image(str(export_path), format="pdf", width=1200, height=600)
                return dbc.Alert(f"图表已导出为PDF：{export_path}", color="success", className="m-2")
            
            elif trigger_id == "export-html":
                export_path = export_dir / f"{chart_title}_{timestamp}.html"
                fig.write_html(str(export_path))
                return dbc.Alert(f"图表已导出为HTML：{export_path}", color="success", className="m-2")
            
            return dash.no_update
        except Exception as e:
            error_msg = str(e)
            if "kaleido" in error_msg.lower() or "orca" in error_msg.lower():
                return dbc.Alert("导出图片需要安装kaleido包。请运行: pip install kaleido", color="warning", className="m-2")
            return dbc.Alert(f"导出图表失败：{error_msg}", color="danger", className="m-2")

