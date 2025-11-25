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


def create_chart_designer_page():
    """创建图表设计器页面"""
    return dbc.Container(
        [
            html.H2("图表设计器", className="mb-4"),
            dcc.Store(id="chart-field-assignments", data=default_chart_assignments()),
            dcc.Store(id="custom-colors-config", data={}),
            dcc.Store(id="field-agg-functions-config", data={}),  # 存储每个字段的聚合函数配置
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
                                                            # X 轴配置
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
                                                            # Y 轴配置
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
                                                            # 分组配置
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
                            
                            # 聚合函数
                            html.Div(id="agg-function-card", children=[
                                dbc.Card(
                                    [
                                        dbc.CardHeader("聚合函数配置"),
                                        dbc.CardBody(
                                            [
                                                html.Div([
                                                    html.Label("默认聚合函数（所有Y轴字段）", className="form-label mb-2"),
                                                    dbc.Select(
                                                        id="agg-function",
                                                        options=[
                                                            {"label": "求和 (SUM)", "value": "sum"},
                                                            {"label": "平均值 (AVG)", "value": "avg"},
                                                            {"label": "计数 (COUNT)", "value": "count"},
                                                            {"label": "最大值 (MAX)", "value": "max"},
                                                            {"label": "最小值 (MIN)", "value": "min"},
                                                            {"label": "占比 (Percentage)", "value": "percentage"},
                                                        ],
                                                        value="sum",
                                                        className="mb-3",
                                                    ),
                                                ]),
                                                html.Div(id="field-agg-functions", children=[
                                                    html.Label("各字段聚合函数（可选）", className="form-label mb-2"),
                                                    html.P("可以为每个Y轴字段单独设置聚合函数。如果不设置，将使用默认聚合函数。", 
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
                                            # 自定义颜色配置
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
                    
                    # 中间：已保存图表管理
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.Span("已保存图表", className="me-auto"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        [html.I(className="fas fa-plus me-1"), "新增"],
                                                        id="btn-new-chart",
                                                        color="success",
                                                        size="sm",
                                                        outline=True
                                                    ),
                                                    dbc.Button(
                                                        [html.I(className="fas fa-sync me-1"), "刷新"],
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
                                                html.P("加载中...", className="text-muted text-center py-3"),
                                            ]),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                                style={"max-height": "600px", "overflow-y": "auto"},
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
                                            dcc.Store(id="current-chart-config", data=None),
                                            dcc.Store(id="current-chart-figure", data=None),
                                            dcc.Store(id="editing-chart-id", data=None),
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
                        width=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


def _generate_chart_cards(charts):
    """生成图表卡片列表的辅助函数"""
    if not charts:
        return html.P("暂无已保存的图表", className="text-muted text-center py-3")
    
    chart_cards = []
    chart_type_names = {
        'line': '折线图',
        'bar': '柱状图',
        'pie': '饼图',
        'table': '表格',
        'combo': '组合图'
    }
    
    for chart in charts:
        chart_id_item = chart.get('id')
        chart_name_item = chart.get('name', chart.get('title', '未命名图表'))
        chart_type_item = chart.get('type', 'line')
        chart_type_name = chart_type_names.get(chart_type_item, chart_type_item)
        created_at = chart.get('created_at', '')
        
        try:
            if created_at:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = created_dt.strftime('%Y-%m-%d %H:%M')
            else:
                created_str = '未知'
        except:
            created_str = created_at[:16] if created_at else '未知'
        
        chart_card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.H6(chart_name_item, className="mb-1 fw-bold"),
                                html.P(f"类型: {chart_type_name}", className="mb-1 small text-muted"),
                                html.P(f"创建: {created_str}", className="mb-2 small text-muted"),
                            ],
                            className="mb-2"
                        ),
                        dbc.ButtonGroup(
                            [
                                dbc.Button(
                                    [html.I(className="fas fa-edit me-1"), "编辑"],
                                    id={"type": "edit-saved-chart", "chart_id": chart_id_item},
                                    color="primary",
                                    size="sm",
                                    className="flex-fill"
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-trash me-1"), "删除"],
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
                options = [{"label": "请先添加数据源", "value": None, "disabled": True}]
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
                no_updates = [dash.no_update] * 11
                no_updates.append(dbc.Alert("图表不存在", color="danger", className="m-2"))
                return tuple(no_updates)
            
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
                dbc.Alert("图表配置已加载，可以开始编辑", color="success", className="m-2")
            )
        except Exception as e:
            no_updates = [dash.no_update] * 11
            no_updates.append(dbc.Alert(f"加载图表失败：{str(e)}", color="danger", className="m-2"))
            return tuple(no_updates)
        
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
                
                chart_config = config_manager.get_chart(chart_id)
                if chart_config:
                    chart_name = chart_config.get('name', '未命名图表')
                    config_manager.delete_chart(chart_id)
                    
                    charts = config_manager.load_charts()
                    charts_list = _generate_chart_cards(charts)
                    
                    return charts_list, dbc.Alert(f"图表 '{chart_name}' 已删除", color="success", className="m-2")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return dash.no_update, dbc.Alert(f"删除失败：{str(e)}", color="danger", className="m-2")
        
        return dash.no_update, dash.no_update

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
        """根据图表类型显示/隐藏不同的配置界面"""
        if chart_type == "table":
            return {"display": "none"}, {"display": "block"}, {"display": "none"}, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif chart_type == "pie":
            return (
                {"display": "block"},
                {"display": "none"},
                {"display": "block"},
                {"display": "none"},
                "数值字段（必需）",
                "提示：拖拽数值字段到下方区域",
                "分类字段（必需）",
                "提示：拖拽分类字段到下方区域"
            )
        else:
            return (
                {"display": "block"},
                {"display": "none"},
                {"display": "block"},
                {"display": "block"},
                "Y 轴",
                "提示：拖拽字段到下方区域",
                "分组/颜色",
                "提示：拖拽字段到下方区域"
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
        
        if not group_field or chart_type == "table":
            return {"display": "none"}, html.P("请先设置分组字段", className="text-muted text-center py-3")
        
        if not datasource_id:
            return {"display": "none"}, html.P("请先选择数据源", className="text-muted text-center py-3")
        
        try:
            ds_config = config_manager.get_datasource(datasource_id)
            if not ds_config:
                return {"display": "none"}, html.P("数据源不存在", className="text-muted text-center py-3")
            
            adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
            df = adapter.fetch_data(limit=1000)
            
            if df is None or df.empty or group_field not in df.columns:
                return {"display": "none"}, html.P("无法加载分组数据", className="text-muted text-center py-3")
            
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
        
        current_colors = current_colors or {}
        new_colors = current_colors.copy()
        
        for i, color_id in enumerate(color_ids):
            if i < len(color_values):
                group_val = color_id.get('group', '')
                if group_val and color_values[i]:
                    new_colors[group_val] = color_values[i]
        
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
        
        if trigger_id == "btn-add-table-column":
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
        
        if not y_fields or len(y_fields) == 0:
            return html.P("请先添加Y轴字段", className="text-muted small mb-2")
        
        # 为每个Y轴字段创建一个聚合函数选择器
        field_selectors = []
        for field in y_fields:
            current_func = field_agg_config.get(field, default_agg_function)
            field_selectors.append(
                dbc.Row([
                    dbc.Col([
                        html.Label(f"{field}:", className="form-label small mb-1"),
                        dbc.Select(
                            id={"type": "field-agg-function", "field": field},
                            options=[
                                {"label": "求和 (SUM)", "value": "sum"},
                                {"label": "平均值 (AVG)", "value": "avg"},
                                {"label": "计数 (COUNT)", "value": "count"},
                                {"label": "最大值 (MAX)", "value": "max"},
                                {"label": "最小值 (MIN)", "value": "min"},
                                {"label": "占比 (Percentage)", "value": "percentage"},
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
                table_columns = assignments.get('table_columns', []) if assignments else []
                table_rows = assignments.get('table_rows', []) if assignments else []
                if table_orientation:
                    if assignments:
                        assignments['table_orientation'] = table_orientation
                else:
                    table_orientation = assignments.get('table_orientation', 'horizontal') if assignments else 'horizontal'
                
                if table_orientation == 'horizontal':
                    if not table_columns:
                        return html.P("请拖拽字段到表格列区域", className="text-muted text-center py-5")
                    selected_columns = [col for col in table_columns if col in df.columns]
                    if not selected_columns:
                        return html.P("所选字段不存在于数据中", className="text-muted text-center py-5")
                    result = df[selected_columns]
                    if isinstance(result, pd.Series):
                        table_df: pd.DataFrame = result.to_frame()
                    else:
                        table_df = result
                    assert isinstance(table_df, pd.DataFrame), "table_df must be a DataFrame"
                else:
                    if not table_rows:
                        return html.P("请拖拽字段到表格行区域", className="text-muted text-center py-5")
                    selected_rows = [row for row in table_rows if row in df.columns]
                    if not selected_rows:
                        return html.P("所选字段不存在于数据中", className="text-muted text-center py-5")
                    transposed = df[selected_rows].T
                    if isinstance(transposed, pd.Series):
                        table_df = transposed.to_frame()
                    else:
                        table_df = transposed
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
                    "agg_functions": field_agg_functions or {},  # 各字段的聚合函数配置
                }
                fig = chart_engine.create_chart(df, chart_config)
                return dcc.Graph(figure=fig, id="preview-chart")
        except Exception as e:
            return dbc.Alert(f"生成图表失败：{str(e)}", color="danger")

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
        if not datasource_id:
            return dash.no_update, dbc.Alert("请先选择数据源", color="warning", className="m-2"), dash.no_update, dash.no_update
        try:
            ds_config = config_manager.get_datasource(datasource_id)
            if not ds_config:
                return dash.no_update, dbc.Alert("数据源不存在", color="warning", className="m-2"), dash.no_update, dash.no_update
            adapter = data_source_manager.get_adapter(datasource_id, ds_config) or DataSourceAdapter(ds_config)
            df = adapter.fetch_data(limit=1000)
            if df is None or df.empty:
                return dash.no_update, dbc.Alert("数据为空", color="warning", className="m-2"), dash.no_update, dash.no_update
            assignments = assignments or default_chart_assignments()
            x_field = assignments.get('x')
            y_fields = assignments.get('y') or []
            if chart_type != 'table' and not x_field and chart_type != 'pie':
                return dash.no_update, dbc.Alert("请将字段拖拽到 X 轴", color="warning", className="m-2"), dash.no_update, dash.no_update
            if not y_fields and chart_type != 'table':
                return dash.no_update, dbc.Alert("请至少选择一个 Y 轴字段", color="warning", className="m-2"), dash.no_update, dash.no_update
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
                "agg_functions": field_agg_functions or {},  # 各字段的聚合函数配置
            }
            
            if chart_type == 'table':
                chart_config['table_columns'] = assignments.get('table_columns', [])
                chart_config['table_rows'] = assignments.get('table_rows', [])
                chart_config['table_orientation'] = assignments.get('table_orientation', 'horizontal')
            
            chart_config['name'] = title or "未命名图表"
            
            # 如果正在编辑已有图表，保留图表ID以便更新
            if editing_id:
                chart_config['id'] = editing_id
            
            config_manager.save_chart(chart_config)
            
            # 重新加载图表列表
            charts = config_manager.load_charts()
            charts_list = _generate_chart_cards(charts)
            
            # 如果正在编辑，重新加载更新后的图表配置
            if editing_id:
                updated_config = config_manager.get_chart(editing_id)
                if updated_config:
                    chart_config = updated_config
            
            # 保存成功后，保持当前编辑状态（用户可以继续编辑或点击"新增"创建新图表）
            return chart_config, dbc.Alert("图表保存成功！", color="success", className="m-2"), charts_list, editing_id
        except Exception as e:
            return dash.no_update, dbc.Alert(f"保存图表失败：{str(e)}", color="danger", className="m-2"), dash.no_update, dash.no_update

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
            html.P("已创建新图表，请开始配置", className="text-muted text-center py-2")  # 提示信息
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

