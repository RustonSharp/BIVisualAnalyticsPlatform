"""通用辅助函数和组件"""
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from typing import Dict, Any, Optional


def create_table_from_dataframe(df: pd.DataFrame, **kwargs) -> dbc.Table:
    """从 DataFrame 创建 Bootstrap 表格"""
    thead = html.Thead([
        html.Tr([html.Th(col) for col in df.columns])
    ])
    tbody = html.Tbody([
        html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
        for i in range(len(df))
    ])
    
    table = dbc.Table(
        [thead, tbody],
        **kwargs
    )
    return table


def default_chart_assignments() -> Dict[str, Any]:
    """获取图表字段配置的默认结构"""
    return {
        "x": None,
        "y": [],
        "group": None,
        "table_columns": [],
        "table_rows": [],
        "table_orientation": "horizontal"
    }


def render_assigned_fields(value: Optional[Any], placeholder: str, multiple: bool = False):
    """根据当前字段配置渲染拖拽区域内容"""
    if multiple:
        items = value if isinstance(value, list) else ([] if value is None else [value])
    else:
        items = [value] if value else []
    if not items:
        return html.P(placeholder, className="text-muted text-center mb-0")
    badges = [
        dbc.Badge(
            str(item),
            color="secondary",
            pill=True,
            className="me-2 mb-2"
        )
        for item in items
    ]
    wrapper_class = "d-flex flex-wrap" if multiple and len(badges) > 1 else None
    return html.Div(badges, className=wrapper_class)

