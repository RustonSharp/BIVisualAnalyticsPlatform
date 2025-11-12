"""
图表生成引擎
负责根据配置生成各类 Plotly 图表
"""

from typing import Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


class ChartEngine:
    """图表生成核心引擎"""

    # 预设配色方案
    COLOR_THEMES = {
        "default": px.colors.qualitative.Plotly,
        "business": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
        "ocean": ["#006BA4", "#FF800E", "#ABABAB", "#595959", "#5F9ED1"],
        "earth": ["#A6761D", "#E6AB02", "#66A61E", "#E7298A", "#7570B3"],
        "sunset": ["#FC8D62", "#8DA0CB", "#E78AC3", "#A6D854", "#FFD92F"],
    }

    def __init__(self):
        self.supported_charts = [
            "line",
            "bar",
            "pie",
            "table",
            "scatter",
            "area",
            "histogram",
        ]

    def create_chart(
        self, data: pd.DataFrame, config: Dict[str, Any]
    ) -> go.Figure:
        """
        根据配置生成图表

        Args:
            data: 数据源
            config: 图表配置，包含：
                - type: 图表类型
                - x: X轴字段
                - y: Y轴字段（可以是列表）
                - group_by: 分组字段
                - agg_func: 聚合函数 (sum/mean/count/max/min)
                - title: 图表标题
                - color_theme: 配色方案
                - show_legend: 是否显示图例
                - height: 图表高度

        Returns:
            go.Figure: Plotly 图表对象
        """
        chart_type = config.get("type", "bar")

        if chart_type not in self.supported_charts:
            raise ValueError(f"不支持的图表类型: {chart_type}")

        # 应用聚合
        if config.get("agg_func"):
            data = self.aggregate_data(data, config)

        # 根据类型创建图表
        if chart_type == "line":
            fig = self._create_line_chart(data, config)
        elif chart_type == "bar":
            fig = self._create_bar_chart(data, config)
        elif chart_type == "pie":
            fig = self._create_pie_chart(data, config)
        elif chart_type == "table":
            fig = self._create_table(data, config)
        elif chart_type == "scatter":
            fig = self._create_scatter_chart(data, config)
        elif chart_type == "area":
            fig = self._create_area_chart(data, config)
        elif chart_type == "histogram":
            fig = self._create_histogram(data, config)
        else:
            raise ValueError(f"图表类型未实现: {chart_type}")

        # 应用通用样式
        self._apply_common_styles(fig, config)

        return fig

    def _create_line_chart(
        self, data: pd.DataFrame, config: Dict[str, Any]
    ) -> go.Figure:
        """创建折线图"""
        x = config.get("x")
        y = config.get("y")
        group_by = config.get("group_by")

        if group_by:
            fig = px.line(
                data,
                x=x,
                y=y,
                color=group_by,
                color_discrete_sequence=self._get_colors(config),
            )
        else:
            fig = px.line(
                data, x=x, y=y, color_discrete_sequence=self._get_colors(config)
            )

        return fig

    def _create_bar_chart(
        self, data: pd.DataFrame, config: Dict[str, Any]
    ) -> go.Figure:
        """创建柱状图"""
        x = config.get("x")
        y = config.get("y")
        group_by = config.get("group_by")
        orientation = config.get("orientation", "v")  # v: 垂直, h: 水平

        if group_by:
            fig = px.bar(
                data,
                x=x,
                y=y,
                color=group_by,
                barmode=config.get("barmode", "group"),
                color_discrete_sequence=self._get_colors(config),
                orientation=orientation,
            )
        else:
            fig = px.bar(
                data,
                x=x,
                y=y,
                color_discrete_sequence=self._get_colors(config),
                orientation=orientation,
            )

        return fig

    def _create_pie_chart(
        self, data: pd.DataFrame, config: Dict[str, Any]
    ) -> go.Figure:
        """创建饼图"""
        names = config.get("names") or config.get("x")
        values = config.get("values") or config.get("y")

        fig = px.pie(
            data,
            names=names,
            values=values,
            color_discrete_sequence=self._get_colors(config),
            hole=config.get("hole", 0),  # 0: 饼图, >0: 环形图
        )

        return fig

    def _create_table(
        self, data: pd.DataFrame, config: Dict[str, Any]
    ) -> go.Figure:
        """创建表格"""
        columns = config.get("columns", data.columns.tolist())
        display_data = data[columns]

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=list(display_data.columns),
                        fill_color="paleturquoise",
                        align="left",
                        font=dict(size=12, color="black"),
                    ),
                    cells=dict(
                        values=[display_data[col] for col in display_data.columns],
                        fill_color="lavender",
                        align="left",
                        font=dict(size=11),
                    ),
                )
            ]
        )

        return fig

    def _create_scatter_chart(
        self, data: pd.DataFrame, config: Dict[str, Any]
    ) -> go.Figure:
        """创建散点图"""
        x = config.get("x")
        y = config.get("y")
        size = config.get("size")
        color = config.get("color") or config.get("group_by")

        fig = px.scatter(
            data,
            x=x,
            y=y,
            size=size,
            color=color,
            color_discrete_sequence=self._get_colors(config),
        )

        return fig

    def _create_area_chart(
        self, data: pd.DataFrame, config: Dict[str, Any]
    ) -> go.Figure:
        """创建面积图"""
        x = config.get("x")
        y = config.get("y")
        group_by = config.get("group_by")

        if group_by:
            fig = px.area(
                data,
                x=x,
                y=y,
                color=group_by,
                color_discrete_sequence=self._get_colors(config),
            )
        else:
            fig = px.area(
                data, x=x, y=y, color_discrete_sequence=self._get_colors(config)
            )

        return fig

    def _create_histogram(
        self, data: pd.DataFrame, config: Dict[str, Any]
    ) -> go.Figure:
        """创建直方图"""
        x = config.get("x")
        nbins = config.get("nbins", 20)

        fig = px.histogram(
            data,
            x=x,
            nbins=nbins,
            color_discrete_sequence=self._get_colors(config),
        )

        return fig

    def aggregate_data(
        self, data: pd.DataFrame, config: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        数据聚合

        Args:
            data: 原始数据
            config: 聚合配置

        Returns:
            pd.DataFrame: 聚合后的数据
        """
        group_by = config.get("group_by") or config.get("x")
        agg_func = config.get("agg_func", "sum")
        value_col = config.get("y")

        if not group_by or not value_col:
            return data

        # 执行聚合
        if agg_func == "sum":
            result = data.groupby(group_by)[value_col].sum().reset_index()
        elif agg_func == "mean":
            result = data.groupby(group_by)[value_col].mean().reset_index()
        elif agg_func == "count":
            result = data.groupby(group_by)[value_col].count().reset_index()
        elif agg_func == "max":
            result = data.groupby(group_by)[value_col].max().reset_index()
        elif agg_func == "min":
            result = data.groupby(group_by)[value_col].min().reset_index()
        else:
            result = data

        return result

    def apply_filters(
        self, data: pd.DataFrame, filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        应用筛选条件

        Args:
            data: 数据
            filters: 筛选条件

        Returns:
            pd.DataFrame: 筛选后的数据
        """
        result = data.copy()

        # 时间范围筛选
        if "date_range" in filters:
            date_col = filters["date_range"]["column"]
            start_date = filters["date_range"].get("start")
            end_date = filters["date_range"].get("end")

            if start_date:
                result = result[result[date_col] >= start_date]
            if end_date:
                result = result[result[date_col] <= end_date]

        # 快捷时间筛选
        if "quick_date" in filters:
            date_col = filters["quick_date"]["column"]
            period = filters["quick_date"]["period"]

            end_date = datetime.now()
            if period == "today":
                start_date = end_date.replace(hour=0, minute=0, second=0)
            elif period == "yesterday":
                start_date = end_date - timedelta(days=1)
                start_date = start_date.replace(hour=0, minute=0, second=0)
                end_date = start_date + timedelta(days=1)
            elif period == "last_7_days":
                start_date = end_date - timedelta(days=7)
            elif period == "last_30_days":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = None

            if start_date:
                result = result[
                    (result[date_col] >= start_date) & (result[date_col] <= end_date)
                ]

        # 类别筛选
        if "category" in filters:
            for col, values in filters["category"].items():
                if isinstance(values, list):
                    result = result[result[col].isin(values)]
                else:
                    result = result[result[col] == values]

        return result

    def _get_colors(self, config: Dict[str, Any]) -> list:
        """获取配色方案"""
        theme = config.get("color_theme", "default")
        return self.COLOR_THEMES.get(theme, self.COLOR_THEMES["default"])

    def _apply_common_styles(self, fig: go.Figure, config: Dict[str, Any]):
        """应用通用样式配置"""
        # 标题
        title = config.get("title", "")
        if title:
            fig.update_layout(title=dict(text=title, x=0.5, xanchor="center"))

        # 图例
        show_legend = config.get("show_legend", True)
        if not show_legend:
            fig.update_layout(showlegend=False)
        else:
            legend_position = config.get("legend_position", "right")
            if legend_position == "top":
                fig.update_layout(legend=dict(orientation="h", y=1.1))
            elif legend_position == "bottom":
                fig.update_layout(legend=dict(orientation="h", y=-0.2))

        # 高度
        height = config.get("height", 500)
        fig.update_layout(height=height)

        # 坐标轴标签
        if config.get("xaxis_title"):
            fig.update_xaxes(title_text=config["xaxis_title"])
        if config.get("yaxis_title"):
            fig.update_yaxes(title_text=config["yaxis_title"])

        # 数据标签
        if config.get("show_data_labels", False):
            fig.update_traces(texttemplate="%{y}", textposition="outside")

        # 主题
        template = config.get("template", "plotly_white")
        fig.update_layout(template=template)
