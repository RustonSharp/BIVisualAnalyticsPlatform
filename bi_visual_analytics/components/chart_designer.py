"""
图表设计器 UI 组件
提供拖拽式图表配置界面
"""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc


def create_chart_designer():
    """创建图表设计器界面"""

    return dbc.Container(
        [
            dbc.Row(
                [
                    # 左侧：字段列表
                    dbc.Col(
                        [
                            html.H5("数据字段", className="mb-3"),
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.Div(id="field-list"),
                                        html.Small(
                                            "拖拽字段到右侧配置区",
                                            className="text-muted",
                                        ),
                                    ]
                                ),
                                style={"height": "600px", "overflow-y": "auto"},
                            ),
                        ],
                        width=3,
                    ),
                    # 中间：配置区
                    dbc.Col(
                        [
                            html.H5("图表配置", className="mb-3"),
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        # 图表类型
                                        dbc.Label("图表类型"),
                                        dcc.Dropdown(
                                            id="chart-type",
                                            options=[
                                                {"label": "📈 折线图", "value": "line"},
                                                {"label": "📊 柱状图", "value": "bar"},
                                                {"label": "🥧 饼图", "value": "pie"},
                                                {"label": "📋 表格", "value": "table"},
                                                {"label": "⚪ 散点图", "value": "scatter"},
                                                {"label": "📉 面积图", "value": "area"},
                                            ],
                                            value="bar",
                                            clearable=False,
                                            className="mb-3",
                                        ),
                                        # X 轴
                                        dbc.Label("X 轴"),
                                        dcc.Dropdown(
                                            id="chart-x-axis",
                                            placeholder="选择 X 轴字段",
                                            className="mb-3",
                                        ),
                                        # Y 轴
                                        dbc.Label("Y 轴"),
                                        dcc.Dropdown(
                                            id="chart-y-axis",
                                            placeholder="选择 Y 轴字段",
                                            className="mb-3",
                                        ),
                                        # 分组字段
                                        dbc.Label("分组字段（可选）"),
                                        dcc.Dropdown(
                                            id="chart-group-by",
                                            placeholder="选择分组字段",
                                            className="mb-3",
                                        ),
                                        # 聚合函数
                                        dbc.Label("聚合函数"),
                                        dcc.Dropdown(
                                            id="chart-agg-func",
                                            options=[
                                                {"label": "求和", "value": "sum"},
                                                {"label": "平均值", "value": "mean"},
                                                {"label": "计数", "value": "count"},
                                                {"label": "最大值", "value": "max"},
                                                {"label": "最小值", "value": "min"},
                                                {"label": "无", "value": "none"},
                                            ],
                                            value="none",
                                            clearable=False,
                                            className="mb-3",
                                        ),
                                        # 图表标题
                                        dbc.Label("图表标题"),
                                        dbc.Input(
                                            id="chart-title",
                                            placeholder="输入标题",
                                            className="mb-3",
                                        ),
                                        # 配色方案
                                        dbc.Label("配色方案"),
                                        dcc.Dropdown(
                                            id="chart-color-theme",
                                            options=[
                                                {"label": "默认", "value": "default"},
                                                {"label": "商务", "value": "business"},
                                                {"label": "海洋", "value": "ocean"},
                                                {"label": "大地", "value": "earth"},
                                                {"label": "日落", "value": "sunset"},
                                            ],
                                            value="default",
                                            clearable=False,
                                            className="mb-3",
                                        ),
                                        # 生成按钮
                                        dbc.Button(
                                            "生成图表",
                                            id="generate-chart-btn",
                                            color="primary",
                                            className="w-100 mt-3",
                                        ),
                                    ]
                                )
                            ),
                        ],
                        width=4,
                    ),
                    # 右侧：图表预览
                    dbc.Col(
                        [
                            html.H5("图表预览", className="mb-3"),
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        dcc.Loading(
                                            id="loading-chart",
                                            children=html.Div(id="chart-preview"),
                                            type="default",
                                        )
                                    ]
                                ),
                                style={"height": "600px", "overflow-y": "auto"},
                            ),
                        ],
                        width=5,
                    ),
                ]
            )
        ],
        fluid=True,
        className="mt-4",
    )


def create_field_item(field_name: str, field_type: str):
    """
    创建字段列表项

    Args:
        field_name: 字段名
        field_type: 字段类型 (numeric/datetime/text)
    """
    # 根据类型选择图标
    icon_map = {
        "numeric": "🔢",
        "datetime": "📅",
        "text": "📝",
    }
    icon = icon_map.get(field_type, "❓")

    return dbc.ListGroupItem(
        [
            html.Span(icon, className="me-2"),
            html.Strong(field_name),
            html.Small(f" ({field_type})", className="text-muted ms-2"),
        ],
        className="mb-1",
        style={"cursor": "move"},
    )


def create_chart_card(chart_id: str, chart_config: dict):
    """
    创建图表卡片（用于仪表盘）

    Args:
        chart_id: 图表 ID
        chart_config: 图表配置
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H6(
                        chart_config.get("title", "未命名图表"),
                        className="mb-0 d-inline",
                    ),
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                "⚙️", size="sm", color="light", className="float-end"
                            ),
                            dbc.Button(
                                "❌", size="sm", color="light", className="float-end"
                            ),
                        ],
                        className="float-end",
                    ),
                ]
            ),
            dbc.CardBody([html.Div(id=f"chart-{chart_id}")]),
        ],
        className="mb-3",
    )
