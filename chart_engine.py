"""
图表生成引擎
根据配置生成各种类型的图表
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional, List, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import Series


class ChartEngine:
    """图表生成引擎"""
    
    # 颜色主题配置
    COLOR_THEMES = {
        'default': px.colors.qualitative.Plotly,
        'blue': px.colors.sequential.Blues,
        'orange': px.colors.sequential.Oranges,
        'green': px.colors.sequential.Greens,
        'purple': px.colors.sequential.Purples,
    }
    
    def __init__(self):
        """初始化图表引擎"""
        pass
    
    def create_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """根据配置创建图表
        
        Args:
            data: 数据 DataFrame
            config: 图表配置
                - type: 图表类型 (line/bar/pie/table/combo)
                - x: X 轴字段
                - y: Y 轴字段（列表）
                - group: 分组字段
                - title: 图表标题
                - color_theme: 颜色主题
                - show_labels: 显示数据标签
                - show_legend: 显示图例
                - agg_function: 聚合函数
        
        Returns:
            Plotly Figure 对象
        """
        chart_type = config.get('type', 'line')
        
        # 数据聚合
        data = self._aggregate_data(data, config)
        
        if chart_type == 'line':
            return self._create_line_chart(data, config)
        elif chart_type == 'bar':
            return self._create_bar_chart(data, config)
        elif chart_type == 'pie':
            return self._create_pie_chart(data, config)
        elif chart_type == 'table':
            return self._create_table_chart(data, config)
        elif chart_type == 'combo':
            return self._create_combo_chart(data, config)
        else:
            raise ValueError(f"不支持的图表类型: {chart_type}")
    
    def _aggregate_data(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """数据聚合"""
        agg_function = config.get('agg_function', 'sum')
        x = config.get('x')
        y = config.get('y', [])
        group = config.get('group')
        
        if not x or not y:
            return data
        
        # 确定分组列
        group_cols = [x]
        if group:
            if isinstance(group, str):
                group_cols.append(group)
            elif isinstance(group, list):
                group_cols.extend(group)
        
        # 聚合函数映射
        agg_dict = {}
        if isinstance(y, str):
            y = [y]
        
        for col in y:
            if pd.api.types.is_numeric_dtype(data[col]):
                if agg_function == 'sum':
                    agg_dict[col] = 'sum'
                elif agg_function == 'avg':
                    agg_dict[col] = 'mean'
                elif agg_function == 'count':
                    agg_dict[col] = 'count'
                elif agg_function == 'max':
                    agg_dict[col] = 'max'
                elif agg_function == 'min':
                    agg_dict[col] = 'min'
            else:
                agg_dict[col] = 'count'
        
        if agg_dict:
            # 执行分组聚合
            grouped_result = data.groupby(group_cols, as_index=False).agg(agg_dict)
            # 类型转换：groupby().agg() 在 as_index=False 时应该返回 DataFrame
            # 但在某些情况下类型检查器无法正确推断，需要显式转换
            if not isinstance(grouped_result, pd.DataFrame):
                # 如果返回的不是 DataFrame，尝试转换
                data = pd.DataFrame(grouped_result) if hasattr(grouped_result, 'to_frame') else data
            else:
                data = grouped_result
            # 重命名聚合后的列
            for col in y:
                if col in data.columns and col in agg_dict:
                    if agg_dict[col] == 'mean':
                        data = data.rename(columns={col: col})
        
        return data
    
    def _create_line_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """创建折线图"""
        x = config.get('x')
        y = config.get('y')
        group = config.get('group')
        title = config.get('title', '折线图')
        color_theme = config.get('color_theme', 'default')
        show_labels = config.get('show_labels', False)
        show_legend = config.get('show_legend', True)
        
        if isinstance(y, list):
            y = y[0] if y else None
        
        if not x or not y:
            raise ValueError("折线图需要指定 X 轴和 Y 轴字段")
        
        # 创建图表
        if group:
            fig = px.line(
                data,
                x=x,
                y=y,
                color=group,
                title=title,
                markers=True
            )
        else:
            fig = px.line(
                data,
                x=x,
                y=y,
                title=title,
                markers=True
            )
        
        # 应用颜色主题
        if color_theme in self.COLOR_THEMES:
            fig.update_traces(line=dict(color=self.COLOR_THEMES[color_theme][0]))
            if group:
                fig.update_traces(line_color_discrete_sequence=self.COLOR_THEMES[color_theme])
        
        # 数据标签
        if show_labels:
            fig.update_traces(textposition="top center", texttemplate='%{y}')
        
        # 图例
        fig.update_layout(showlegend=show_legend)
        
        # 更新布局
        fig.update_layout(template='plotly_white', height=400)
        
        return fig
    
    def _create_bar_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """创建柱状图"""
        x = config.get('x')
        y = config.get('y')
        group = config.get('group')
        title = config.get('title', '柱状图')
        color_theme = config.get('color_theme', 'default')
        show_labels = config.get('show_labels', False)
        show_legend = config.get('show_legend', True)
        
        if isinstance(y, list):
            y = y[0] if y else None
        
        if not x or not y:
            raise ValueError("柱状图需要指定 X 轴和 Y 轴字段")
        
        # 创建图表
        if group:
            fig = px.bar(
                data,
                x=x,
                y=y,
                color=group,
                title=title
            )
        else:
            fig = px.bar(
                data,
                x=x,
                y=y,
                title=title
            )
        
        # 应用颜色主题
        if color_theme in self.COLOR_THEMES:
            if group:
                fig.update_traces(marker_color_discrete_sequence=self.COLOR_THEMES[color_theme])
            else:
                fig.update_traces(marker_color=self.COLOR_THEMES[color_theme][0])
        
        # 数据标签
        if show_labels:
            fig.update_traces(textposition="outside", texttemplate='%{y}')
        
        # 图例
        fig.update_layout(showlegend=show_legend)
        
        # 更新布局
        fig.update_layout(template='plotly_white', height=400)
        
        return fig
    
    def _create_pie_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """创建饼图"""
        group = config.get('group') or config.get('x')
        y = config.get('y')
        title = config.get('title', '饼图')
        color_theme = config.get('color_theme', 'default')
        show_labels = config.get('show_labels', True)
        show_legend = config.get('show_legend', True)
        
        if isinstance(y, list):
            y = y[0] if y else None
        
        if not group or not y:
            raise ValueError("饼图需要指定分组字段和数值字段")
        
        # 创建图表
        fig = px.pie(
            data,
            values=y,
            names=group,
            title=title
        )
        
        # 应用颜色主题
        if color_theme in self.COLOR_THEMES:
            fig.update_traces(marker_colors=self.COLOR_THEMES[color_theme])
        
        # 数据标签
        if show_labels:
            fig.update_traces(textposition='inside', textinfo='percent+label')
        else:
            fig.update_traces(textposition='inside', textinfo='percent')
        
        # 图例
        fig.update_layout(showlegend=show_legend)
        
        # 更新布局
        fig.update_layout(template='plotly_white', height=400)
        
        return fig
    
    def _create_table_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """创建表格图表"""
        title = config.get('title', '数据表格')
        limit = config.get('limit', 100)
        
        # 限制行数
        data = data.head(limit)
        
        # 创建表格
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(data.columns),
                fill_color='paleturquoise',
                align='left'
            ),
            cells=dict(
                values=[data[col].tolist() for col in data.columns],
                fill_color='lavender',
                align='left'
            )
        )])
        
        fig.update_layout(title=title, height=400)
        
        return fig
    
    def _create_combo_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """创建组合图（折线+柱状）"""
        x = config.get('x')
        y = config.get('y', [])
        title = config.get('title', '组合图')
        color_theme = config.get('color_theme', 'default')
        show_legend = config.get('show_legend', True)
        
        if not x or not y:
            raise ValueError("组合图需要指定 X 轴和至少一个 Y 轴字段")
        
        if isinstance(y, str):
            y = [y]
        
        # 创建图表
        fig = go.Figure()
        
        # 第一个 Y 轴用柱状图
        if len(y) > 0:
            fig.add_trace(go.Bar(
                x=data[x],
                y=data[y[0]],
                name=y[0],
                yaxis='y',
                offsetgroup=1
            ))
        
        # 第二个 Y 轴用折线图
        if len(y) > 1:
            fig.add_trace(go.Scatter(
                x=data[x],
                y=data[y[1]],
                name=y[1],
                mode='lines+markers',
                yaxis='y2',
                line=dict(color='red')
            ))
            
            # 添加第二个 Y 轴
            fig.update_layout(
                yaxis2=dict(
                    title=y[1],
                    overlaying='y',
                    side='right'
                )
            )
        
        fig.update_layout(
            title=title,
            xaxis_title=x,
            yaxis_title=y[0] if y else '',
            template='plotly_white',
            height=400,
            showlegend=show_legend
        )
        
        return fig
    
    def apply_filters(self, data: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """应用筛选条件"""
        if not isinstance(data, pd.DataFrame) or data.empty:
            return pd.DataFrame()
        
        filtered_data: pd.DataFrame = data.copy()
        
        for col, condition in filters.items():
            # 检查列是否存在
            if col not in filtered_data.columns:
                continue
            
            # 获取列 Series，明确类型
            # 使用 loc 访问列以确保类型推断正确
            col_series = filtered_data.loc[:, col]
            if not isinstance(col_series, pd.Series):
                continue
            
            # 应用筛选条件
            if isinstance(condition, dict):
                mask: Optional[pd.Series] = None
                if 'min' in condition:
                    mask = col_series >= condition['min']
                if 'max' in condition:
                    max_mask = col_series <= condition['max']
                    mask = max_mask if mask is None else (mask & max_mask)
                if 'values' in condition:
                    values_mask = col_series.isin(condition['values'])
                    mask = values_mask if mask is None else (mask & values_mask)
                
                if mask is not None and isinstance(mask, pd.Series):
                    result = filtered_data[mask]
                    if isinstance(result, pd.DataFrame):
                        filtered_data = result
            elif isinstance(condition, list):
                mask = col_series.isin(condition)
                if isinstance(mask, pd.Series):
                    result = filtered_data[mask]
                    if isinstance(result, pd.DataFrame):
                        filtered_data = result
            else:
                mask = col_series == condition
                if isinstance(mask, pd.Series):
                    result = filtered_data[mask]
                    if isinstance(result, pd.DataFrame):
                        filtered_data = result
        
        return filtered_data

