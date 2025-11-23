"""数据源管理页面模块"""
import dash
from dash import dcc, html, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import json
from pathlib import Path

from components.common import create_table_from_dataframe
from data_adapter import DataSourceAdapter
from load_data import load_from_file, DBConfig, load_from_database, load_from_api


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
                    dcc.Store(id="current-datasource-id", data=None),
                    dcc.Store(id="current-uploaded-file", data=None),
                    html.Div(id="test-connection-status", className="m-3"),
                    dbc.ModalBody(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        [
                                            html.Div([
                                                html.Label("上传文件", className="form-label mt-3"),
                                                html.Div([
                                                    # 上传组件，使用按钮样式
                                                    dcc.Upload(
                                                        id="upload-file",
                                                        children=dbc.Button(
                                                            [
                                                                html.I(className="fas fa-upload me-2"),
                                                                "上传文件"
                                                            ],
                                                            color="primary",
                                                            className="mb-2",
                                                        ),
                                                        multiple=False,
                                                    ),
                                                    html.Div(
                                                        html.Small("支持 CSV、Excel (.xls, .xlsx)", className="text-muted d-block"),
                                                        className="mb-2"
                                                    ),
                                                ]),
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


def register_datasource_callbacks(app, config_manager, data_source_manager, upload_dir):
    """注册数据源页面的所有回调函数"""
    
    @app.callback(
        Output("datasource-list", "children", allow_duplicate=True),
        Input("url", "pathname"),
        prevent_initial_call='initial_duplicate'
    )
    def load_datasource_list(pathname):
        """页面加载时自动加载数据源列表"""
        if pathname == "/datasource":
            datasources = config_manager.load_datasources()
            return create_datasource_table(datasources)
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
        """打开/关闭数据源配置模态框"""
        ctx = callback_context
        if not ctx.triggered:
            return [dash.no_update] * 6
        
        trigger_id = ctx.triggered[0]["prop_id"]
        trigger_str = str(trigger_id)
        
        if "btn-test-connection" in trigger_str or "btn-save-datasource" in trigger_str:
            return [dash.no_update] * 6
        
        if trigger_str == "btn-add-datasource.n_clicks":
            return True, "tab-file", "新增数据源", None, None, ""
        elif trigger_str == "btn-cancel-datasource.n_clicks":
            return False, current_tab or "tab-file", "新增数据源", None, None, ""
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
        
        return [dash.no_update] * 6

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
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            file_path = upload_dir / filename
            with open(file_path, 'wb') as f:
                f.write(decoded)
            
            try:
                df = load_from_file(str(file_path))
                
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
        
        if button_id not in ["btn-test-connection", "btn-save-datasource"]:
            datasources = config_manager.load_datasources()
            return create_datasource_table(datasources), "", False
        
        try:
            used_filename = current_file or filename
            
            if active_tab == "tab-file":
                if not used_filename:
                    datasources = config_manager.load_datasources()
                    return create_datasource_table(datasources), dbc.Alert("请先上传文件", color="warning", className="m-3"), False
                
                file_path = str(upload_dir / used_filename)
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
                        return create_datasource_table(datasources), status_msg, False
                    except Exception as e:
                        datasources = config_manager.load_datasources()
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
                        load_from_database(db_config, "SELECT 1")
                        
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
                        return create_datasource_table(datasources), status_msg, False
                    except Exception as e:
                        datasources = config_manager.load_datasources()
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
                        return create_datasource_table(datasources), status_msg, False
                    except Exception as e:
                        datasources = config_manager.load_datasources()
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
                return create_datasource_table(datasources), dbc.Alert("数据源保存成功！", color="success", className="m-3"), True
            
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
            return False, False
        return dash.no_update, dash.no_update

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
                filename,
                ds_config.get('name', ''),
                "postgresql",
                None, None, None, None, None,
                "SELECT * FROM table_name LIMIT 100",
                None,
                None, None, None, None, None,
                filename,
                ""
            )
        elif ds_type == 'database':
            return (
                None, None,
                ds_config.get('engine', 'postgresql'),
                ds_config.get('host', ''),
                ds_config.get('port', 5432),
                ds_config.get('database', ''),
                ds_config.get('user', ''),
                ds_config.get('password', ''),
                ds_config.get('sql', 'SELECT * FROM table_name LIMIT 100'),
                ds_config.get('name', ''),
                None, None, None, None, None,
                None,
                ""
            )
        else:  # api
            headers = ds_config.get('headers', {})
            params = ds_config.get('params', {})
            return (
                None, None,
                "postgresql", None, None, None, None, None,
                "SELECT * FROM table_name LIMIT 100", None,
                ds_config.get('url', ''),
                ds_config.get('method', 'GET'),
                json.dumps(headers, indent=2) if headers else '',
                json.dumps(params, indent=2) if params else '',
                ds_config.get('name', ''),
                None,
                ""
            )

