"""
筛选器面板 UI 组件
提供交互式数据筛选功能
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta


def create_filter_panel():
    """创建筛选器面板"""

    return dbc.Card(
        [
            dbc.CardHeader(html.H5("数据筛选器", className="mb-0")),
            dbc.CardBody(
                [
                    # 时间范围筛选
                    html.H6("时间范围", className="mb-3"),
                    create_date_range_filter(),
                    html.Hr(),
                    # 类别筛选
                    html.H6("类别筛选", className="mb-3 mt-3"),
                    html.Div(id="category-filters"),
                    html.Hr(),
                    # 应用按钮
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                "应用筛选",
                                id="apply-filters-btn",
                                color="primary",
                                className="me-2",
                            ),
                            dbc.Button(
                                "重置",
                                id="reset-filters-btn",
                                color="secondary",
                            ),
                        ],
                        className="w-100 mt-3",
                    ),
                ]
            ),
        ],
        className="mb-3",
    )


def create_date_range_filter():
    """创建时间范围筛选器"""

    # 计算默认日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    return html.Div(
        [
            # 快捷选项
            dbc.Label("快捷选项"),
            dcc.Dropdown(
                id="quick-date-filter",
                options=[
                    {"label": "今天", "value": "today"},
                    {"label": "昨天", "value": "yesterday"},
                    {"label": "近 7 天", "value": "last_7_days"},
                    {"label": "近 30 天", "value": "last_30_days"},
                    {"label": "本月", "value": "this_month"},
                    {"label": "上月", "value": "last_month"},
                    {"label": "自定义", "value": "custom"},
                ],
                value="last_30_days",
                clearable=False,
                className="mb-3",
            ),
            # 自定义日期范围
            html.Div(
                [
                    dbc.Label("自定义日期范围"),
                    dcc.DatePickerRange(
                        id="custom-date-range",
                        start_date=start_date,
                        end_date=end_date,
                        display_format="YYYY-MM-DD",
                        style={"width": "100%"},
                    ),
                ],
                id="custom-date-range-container",
                style={"display": "none"},
                className="mb-3",
            ),
        ]
    )


def create_category_filter(field_name: str, options: list):
    """
    创建类别筛选器

    Args:
        field_name: 字段名
        options: 选项列表
    """
    return html.Div(
        [
            dbc.Label(field_name),
            dcc.Dropdown(
                id=f"filter-{field_name}",
                options=[{"label": opt, "value": opt} for opt in options],
                multi=True,
                placeholder=f"选择 {field_name}",
                className="mb-3",
            ),
        ]
    )


def create_numeric_range_filter(field_name: str, min_val: float, max_val: float):
    """
    创建数值范围筛选器

    Args:
        field_name: 字段名
        min_val: 最小值
        max_val: 最大值
    """
    return html.Div(
        [
            dbc.Label(f"{field_name} 范围"),
            dcc.RangeSlider(
                id=f"range-{field_name}",
                min=min_val,
                max=max_val,
                value=[min_val, max_val],
                marks={
                    min_val: f"{min_val:.0f}",
                    max_val: f"{max_val:.0f}",
                },
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-4",
            ),
        ]
    )


def create_global_filter_bar():
    """创建全局筛选栏（显示在页面顶部）"""

    return dbc.Navbar(
        dbc.Container(
            [
                html.Div(
                    [
                        html.Span("🔍 ", className="me-2"),
                        html.Strong("当前筛选条件：", className="me-3"),
                        html.Span(id="active-filters-display", className="text-muted"),
                    ],
                    className="d-flex align-items-center",
                ),
                dbc.Button(
                    "编辑筛选",
                    id="edit-filters-btn",
                    size="sm",
                    color="light",
                    className="ms-auto",
                ),
            ],
            fluid=True,
        ),
        color="light",
        light=True,
        className="mb-3",
    )
