"""设置页面模块"""
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context
import dash


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
                                            dbc.Button("保存设置", id="btn-save-settings", color="primary", className="mb-3"),
                                            html.Div(id="settings-save-status", children=[]),
                                            dcc.Store(id="settings-save-status-message", data=None),  # 存储保存状态消息和时间戳
                                            dcc.Interval(id="settings-save-status-interval", interval=100, disabled=True),  # 用于定时清除消息
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


def register_settings_callbacks(app):
    """注册设置页面的回调函数"""
    
    @app.callback(
        Output("global-refresh-interval-setting", "data", allow_duplicate=True),
        Input("refresh-interval", "value"),
        prevent_initial_call='initial_duplicate'
    )
    def update_refresh_interval_setting(refresh_interval_value):
        """更新全局刷新间隔设置（自动保存）"""
        if refresh_interval_value:
            return refresh_interval_value
        return dash.no_update
    
    @app.callback(
        [Output("global-refresh-interval-setting", "data", allow_duplicate=True),
         Output("settings-save-status", "children"),
         Output("settings-save-status-message", "data"),
         Output("settings-save-status-interval", "disabled")],
        Input("btn-save-settings", "n_clicks"),
        [State("refresh-interval", "value"),
         State("default-theme", "value")],
        prevent_initial_call=True
    )
    def save_settings(save_clicks, refresh_interval_value, default_theme_value):
        """保存设置"""
        import time
        
        if not save_clicks:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # 保存刷新间隔到全局Store
        refresh_value = refresh_interval_value if refresh_interval_value else "off"
        
        # 显示保存成功消息
        success_message = dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                "设置已保存成功！",
            ],
            color="success",
            className="mt-2"
        )
        
        # 保存状态消息数据（包含时间戳）
        status_data = {
            "message": "设置已保存成功！",
            "timestamp": time.time()
        }
        
        # 返回更新的刷新间隔设置、成功消息、状态数据和启用Interval
        return refresh_value, success_message, status_data, False
    
    @app.callback(
        [Output("settings-save-status", "children", allow_duplicate=True),
         Output("settings-save-status-interval", "disabled", allow_duplicate=True)],
        Input("settings-save-status-interval", "n_intervals"),
        State("settings-save-status-message", "data"),
        prevent_initial_call=True
    )
    def clear_save_status(n_intervals, status_data):
        """3秒后自动清除保存状态消息"""
        import time
        
        if not status_data or not status_data.get('timestamp'):
            return [], True  # 没有消息，禁用 Interval
        
        current_time = time.time()
        elapsed = current_time - status_data.get('timestamp', 0)
        
        # 如果超过3秒，清除消息并禁用 Interval
        if elapsed >= 3.0:
            return [], True
        
        # 否则保持消息不变，继续运行 Interval
        return dash.no_update, False

