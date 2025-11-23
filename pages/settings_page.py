"""设置页面模块"""
import dash_bootstrap_components as dbc
from dash import html


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

