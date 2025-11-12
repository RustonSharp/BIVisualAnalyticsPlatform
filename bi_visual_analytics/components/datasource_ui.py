"""
数据源配置 UI 组件
提供可视化的数据源配置界面
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_datasource_config_ui():
    """创建数据源配置界面"""

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H3("数据源配置", className="mb-4"),
                            # 数据源类型选择
                            dbc.Label("数据源类型"),
                            dcc.Dropdown(
                                id="datasource-type",
                                options=[
                                    {"label": "CSV / Excel 文件", "value": "csv"},
                                    {"label": "数据库 (PostgreSQL/MySQL)", "value": "database"},
                                    {"label": "REST API", "value": "api"},
                                ],
                                value="csv",
                                clearable=False,
                                className="mb-3",
                            ),
                            # 数据源名称
                            dbc.Label("数据源名称"),
                            dbc.Input(
                                id="datasource-name",
                                placeholder="输入数据源名称",
                                className="mb-3",
                            ),
                            # 动态配置区域
                            html.Div(id="datasource-config-area"),
                            # 操作按钮
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "测试连接",
                                        id="test-connection-btn",
                                        color="info",
                                        className="me-2",
                                    ),
                                    dbc.Button(
                                        "保存配置",
                                        id="save-datasource-btn",
                                        color="primary",
                                        className="me-2",
                                    ),
                                ],
                                className="mt-3",
                            ),
                            # 反馈信息
                            html.Div(id="datasource-feedback", className="mt-3"),
                            # 数据预览
                            html.Hr(),
                            html.H5("数据预览", className="mt-4"),
                            html.Div(id="data-preview"),
                        ],
                        width=12,
                    )
                ]
            )
        ],
        fluid=True,
    )


def create_csv_config():
    """CSV 配置表单"""
    return dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("选择文件"),
                dcc.Upload(
                    id="csv-file-upload",
                    children=dbc.Button(
                        [
                            html.I(className="fas fa-upload me-2"),
                            "点击选择 CSV/Excel 文件",
                        ],
                        color="primary",
                        outline=True,
                        className="w-100",
                    ),
                    multiple=False,
                    className="mb-3",
                ),
                html.Div(id="csv-upload-status", className="mb-3"),
                dbc.Label("或输入文件路径"),
                dbc.Input(
                    id="csv-file-path",
                    placeholder="例如: data/sales.csv",
                    className="mb-3",
                ),
                dbc.Label("编码方式"),
                dcc.Dropdown(
                    id="csv-encoding",
                    options=[
                        {"label": "UTF-8", "value": "utf-8"},
                        {"label": "GBK", "value": "gbk"},
                        {"label": "GB2312", "value": "gb2312"},
                    ],
                    value="utf-8",
                    clearable=False,
                    className="mb-3",
                ),
                dbc.Label("分隔符"),
                dcc.Dropdown(
                    id="csv-separator",
                    options=[
                        {"label": "逗号 (,)", "value": ","},
                        {"label": "制表符 (\\t)", "value": "\t"},
                        {"label": "分号 (;)", "value": ";"},
                    ],
                    value=",",
                    clearable=False,
                    className="mb-3",
                ),
            ]
        ),
        className="mt-3",
    )


def create_database_config():
    """数据库配置表单"""
    return dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("数据库类型"),
                dcc.Dropdown(
                    id="db-type",
                    options=[
                        {"label": "PostgreSQL", "value": "postgresql"},
                        {"label": "MySQL", "value": "mysql"},
                    ],
                    value="postgresql",
                    clearable=False,
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("主机地址"),
                                dbc.Input(
                                    id="db-host",
                                    placeholder="localhost",
                                    value="localhost",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("端口"),
                                dbc.Input(
                                    id="db-port", placeholder="5432", type="number"
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Label("数据库名"),
                dbc.Input(id="db-database", placeholder="mydb", className="mb-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("用户名"),
                                dbc.Input(id="db-username", placeholder="user"),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("密码"),
                                dbc.Input(
                                    id="db-password", type="password", placeholder="****"
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Label("表名"),
                dbc.Input(id="db-table", placeholder="表名（可选）", className="mb-3"),
            ]
        ),
        className="mt-3",
    )


def create_api_config():
    """API 配置表单"""
    return dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("API URL"),
                dbc.Input(
                    id="api-url",
                    placeholder="https://api.example.com/data",
                    className="mb-3",
                ),
                dbc.Label("请求方法"),
                dcc.Dropdown(
                    id="api-method",
                    options=[
                        {"label": "GET", "value": "GET"},
                        {"label": "POST", "value": "POST"},
                    ],
                    value="GET",
                    clearable=False,
                    className="mb-3",
                ),
                dbc.Label("JSON 数据路径（可选）"),
                dbc.Input(
                    id="api-json-path",
                    placeholder="例如: data.results",
                    className="mb-3",
                ),
                dbc.Label("API Key（可选）"),
                dbc.Input(
                    id="api-key", type="password", placeholder="API Key", className="mb-3"
                ),
            ]
        ),
        className="mt-3",
    )
