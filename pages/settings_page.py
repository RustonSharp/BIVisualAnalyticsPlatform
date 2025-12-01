"""设置页面模块"""
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context
import dash
from language_manager import language_manager
from logger import get_logger

logger = get_logger('settings_page')


def create_settings_page():
    """创建设置页面"""
    current_lang = language_manager.get_language()
    texts = language_manager.get_all_texts()
    
    # 根据语言设置选项文本
    refresh_options = [
        {"label": texts["off"], "value": "off"},
        {"label": f"5 {texts['minutes']}", "value": "5"},
        {"label": f"10 {texts['minutes']}", "value": "10"},
        {"label": f"30 {texts['minutes']}", "value": "30"},
        {"label": f"1 {texts['hour']}", "value": "60"},
    ]
    
    theme_options = [
        {"label": texts["default"], "value": "default"},
        {"label": texts["business_blue"], "value": "blue"},
        {"label": texts["vibrant_orange"], "value": "orange"},
        {"label": texts["natural_green"], "value": "green"},
    ]
    
    return dbc.Container(
        [
            html.H2(texts["settings"], id="settings-page-title", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(id="general-settings-header", children=texts["general_settings"]),
                                    dbc.CardBody(
                                        [
                                            html.Label(id="refresh-interval-label", children=texts["auto_refresh_interval"], className="form-label"),
                                            dbc.Select(
                                                id="refresh-interval",
                                                options=refresh_options,
                                                value="off",
                                                className="mb-3",
                                            ),
                                            html.Label(id="default-theme-label", children=texts["default_chart_theme"], className="form-label"),
                                            dbc.Select(
                                                id="default-theme",
                                                options=theme_options,
                                                value="default",
                                                className="mb-3",
                                            ),
                                            html.Hr(className="my-3"),
                                            html.Label(id="select-language-label", children=texts["select_language"], className="form-label"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        texts["chinese"],
                                                        id="btn-lang-zh",
                                                        color="primary" if current_lang == "zh" else "secondary",
                                                        outline=True if current_lang != "zh" else False,
                                                        className="me-2",
                                                    ),
                                                    dbc.Button(
                                                        texts["english"],
                                                        id="btn-lang-en",
                                                        color="primary" if current_lang == "en" else "secondary",
                                                        outline=True if current_lang != "en" else False,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            html.Div(id="language-change-status", children=[]),
                                            dcc.Store(id="language-change-message", data=None),
                                            dcc.Interval(id="language-change-interval", interval=100, disabled=True),
                                            html.Hr(className="my-3"),
                                            dbc.Button(texts["save_settings"], id="btn-save-settings", color="primary", className="mb-3"),
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
                                    dbc.CardHeader(id="datasource-config-header", children=texts["datasource_config"]),
                                    dbc.CardBody(
                                        [
                                            html.Label(id="export-config-label", children=texts["export_config"], className="form-label"),
                                            dbc.Button(id="btn-export-config", children=texts["export_all_datasource_config"], color="info", className="mb-3"),
                                            html.Label(id="import-config-label", children=texts["import_config"], className="form-label"),
                                            dbc.Button(id="btn-import-config", children=texts["import_datasource_config"], color="warning"),
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
        
        # 获取当前语言的文本
        texts = language_manager.get_all_texts()
        
        # 保存刷新间隔到全局Store
        refresh_value = refresh_interval_value if refresh_interval_value else "off"
        
        # 显示保存成功消息
        success_message = dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                texts["settings_saved"],
            ],
            color="success",
            className="mt-2"
        )
        
        # 保存状态消息数据（包含时间戳）
        status_data = {
            "message": texts["settings_saved"],
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
    
    # 语言切换回调
    @app.callback(
        [Output("global-language-setting", "data", allow_duplicate=True),
         Output("language-change-status", "children"),
         Output("language-change-message", "data"),
         Output("language-change-interval", "disabled"),
         Output("btn-lang-zh", "color"),
         Output("btn-lang-zh", "outline"),
         Output("btn-lang-en", "color"),
         Output("btn-lang-en", "outline")],
        [Input("btn-lang-zh", "n_clicks"),
         Input("btn-lang-en", "n_clicks")],
        State("global-language-setting", "data"),
        prevent_initial_call=True
    )
    def change_language(zh_clicks, en_clicks, current_lang):
        """切换语言"""
        import time
        from dash import callback_context
        
        ctx = callback_context
        
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        trigger_info = ctx.triggered[0]
        button_id = trigger_info['prop_id'].split('.')[0]
        prop_id = trigger_info['prop_id']
        
        # 只处理 n_clicks 属性的变化，忽略其他属性（如 color, outline）的变化
        if '.n_clicks' not in prop_id:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # 检查点击次数是否有效（必须大于0）
        if (button_id == "btn-lang-zh" and (zh_clicks is None or zh_clicks == 0)) or \
           (button_id == "btn-lang-en" and (en_clicks is None or en_clicks == 0)):
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # 确定要切换到的语言
        if button_id == "btn-lang-zh":
            new_lang = "zh"
        elif button_id == "btn-lang-en":
            new_lang = "en"
        else:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # 如果语言没有变化，不执行任何操作
        if new_lang == current_lang:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # 保存语言设置
        logger.info(f"用户切换语言: {current_lang} -> {new_lang}")
        if language_manager.save_language(new_lang):
            logger.info(f"语言设置保存成功: {new_lang}")
        else:
            logger.error(f"语言设置保存失败: {new_lang}")
        
        # 获取新语言的文本
        texts = language_manager.get_all_texts(new_lang)
        
        # 显示切换成功消息
        success_message = dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                texts["language_changed"],
            ],
            color="success",
            className="mt-2"
        )
        
        # 保存状态消息数据
        status_data = {
            "message": texts["language_changed"],
            "timestamp": time.time()
        }
        
        # 更新按钮样式
        zh_color = "primary" if new_lang == "zh" else "secondary"
        zh_outline = False if new_lang == "zh" else True
        en_color = "primary" if new_lang == "en" else "secondary"
        en_outline = False if new_lang == "en" else True
        
        # 返回新语言设置、成功消息、状态数据、启用Interval和按钮样式
        return new_lang, success_message, status_data, False, zh_color, zh_outline, en_color, en_outline
    
    @app.callback(
        [Output("language-change-status", "children", allow_duplicate=True),
         Output("language-change-interval", "disabled", allow_duplicate=True)],
        Input("language-change-interval", "n_intervals"),
        State("language-change-message", "data"),
        prevent_initial_call=True
    )
    def clear_language_change_status(n_intervals, status_data):
        """3秒后自动清除语言切换状态消息"""
        import time
        
        if not status_data or not status_data.get('timestamp'):
            return [], True
        
        current_time = time.time()
        elapsed = current_time - status_data.get('timestamp', 0)
        
        if elapsed >= 3.0:
            return [], True
        
        return dash.no_update, False
    
    # 监听语言变化，刷新设置页面内容
    @app.callback(
        [Output("settings-page-title", "children", allow_duplicate=True),
         Output("general-settings-header", "children", allow_duplicate=True),
         Output("refresh-interval-label", "children", allow_duplicate=True),
         Output("default-theme-label", "children", allow_duplicate=True),
         Output("refresh-interval", "options", allow_duplicate=True),
         Output("default-theme", "options", allow_duplicate=True),
         Output("btn-save-settings", "children", allow_duplicate=True),
         Output("select-language-label", "children", allow_duplicate=True),
         Output("datasource-config-header", "children", allow_duplicate=True),
         Output("export-config-label", "children", allow_duplicate=True),
         Output("btn-export-config", "children", allow_duplicate=True),
         Output("import-config-label", "children", allow_duplicate=True),
         Output("btn-import-config", "children", allow_duplicate=True)],
        Input("global-language-setting", "data"),
        prevent_initial_call=True
    )
    def update_settings_page_texts(language):
        """语言变化时更新设置页面的文本"""
        # 确保语言有效
        if not language or language not in ["zh", "en"]:
            language = language_manager.get_language()
        # 确保语言管理器使用正确的语言
        language_manager.set_language(language)
        texts = language_manager.get_all_texts(language)
        
        # 更新刷新间隔选项
        refresh_options = [
            {"label": texts["off"], "value": "off"},
            {"label": f"5 {texts['minutes']}", "value": "5"},
            {"label": f"10 {texts['minutes']}", "value": "10"},
            {"label": f"30 {texts['minutes']}", "value": "30"},
            {"label": f"1 {texts['hour']}", "value": "60"},
        ]
        
        # 更新主题选项
        theme_options = [
            {"label": texts["default"], "value": "default"},
            {"label": texts["business_blue"], "value": "blue"},
            {"label": texts["vibrant_orange"], "value": "orange"},
            {"label": texts["natural_green"], "value": "green"},
        ]
        
        return (
            texts["settings"],  # 页面标题
            texts["general_settings"],  # 通用设置标题
            texts["auto_refresh_interval"],  # 自动刷新间隔标签
            texts["default_chart_theme"],  # 默认图表主题标签
            refresh_options,  # 刷新间隔选项
            theme_options,  # 主题选项
            texts["save_settings"],  # 保存设置按钮
            texts["select_language"],  # 选择语言标签
            texts["datasource_config"],  # 数据源配置标题
            texts["export_config"],  # 导出配置标签
            texts["export_all_datasource_config"],  # 导出按钮
            texts["import_config"],  # 导入配置标签
            texts["import_datasource_config"],  # 导入按钮
        )

