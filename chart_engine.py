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
    
    # 颜色主题配置 - 确保所有颜色值都是字符串列表
    COLOR_THEMES = {
        'default': [str(c) for c in px.colors.qualitative.Plotly],
        'blue': [str(c) for c in px.colors.sequential.Blues],
        'orange': [str(c) for c in px.colors.sequential.Oranges],
        'green': [str(c) for c in px.colors.sequential.Greens],
        'purple': [str(c) for c in px.colors.sequential.Purples],
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
        
        # 应用颜色主题或自定义颜色
        custom_colors = config.get('custom_colors', {})  # {group_value: color}
        if custom_colors and group:
            # 使用自定义颜色映射
            color_map = custom_colors
            # 为每个分组设置颜色，确保不重复
            unique_groups = data[group].unique() if group in data.columns else []
            color_sequence = []
            theme_colors = self.COLOR_THEMES.get(color_theme, self.COLOR_THEMES['default'])
            if not isinstance(theme_colors, list):
                theme_colors = list(theme_colors) if hasattr(theme_colors, '__iter__') else [theme_colors]
            theme_colors = [str(c) for c in theme_colors if c]
            
            # 构建颜色序列，优先使用自定义颜色，然后使用主题颜色
            used_colors = set()
            for group_val in unique_groups:
                group_val_str = str(group_val)
                if group_val_str in color_map:
                    # 使用自定义颜色
                    custom_color = color_map[group_val_str]
                    if custom_color not in used_colors:
                        color_sequence.append(custom_color)
                        used_colors.add(custom_color)
                    else:
                        # 自定义颜色重复，使用主题颜色
                        for theme_color in theme_colors:
                            if theme_color not in used_colors:
                                color_sequence.append(theme_color)
                                used_colors.add(theme_color)
                                break
                else:
                    # 使用主题颜色，确保不重复
                    for theme_color in theme_colors:
                        if theme_color not in used_colors:
                            color_sequence.append(theme_color)
                            used_colors.add(theme_color)
                            break
                    # 如果主题颜色都用完了，循环使用
                    if len(color_sequence) <= len(unique_groups):
                        remaining = len(unique_groups) - len(color_sequence)
                        while len(color_sequence) < len(unique_groups):
                            color_sequence.extend(theme_colors[:remaining])
                            remaining = len(unique_groups) - len(color_sequence)
            
            if color_sequence:
                fig.update_layout(color_discrete_map={str(k): v for k, v in zip(unique_groups, color_sequence[:len(unique_groups)])})
        elif color_theme in self.COLOR_THEMES:
            colors = self.COLOR_THEMES[color_theme]
            # 确保 colors 是列表
            if not isinstance(colors, list):
                colors = list(colors) if hasattr(colors, '__iter__') else [colors]
            colors = [str(c) for c in colors if c]
            if group:
                # 对于分组图表，确保每个组使用不同颜色
                unique_groups = data[group].unique() if group in data.columns else []
                num_groups = len(unique_groups)
                # 如果分组数量超过颜色数量，扩展颜色列表（循环使用）
                if num_groups > len(colors):
                    extended_colors = (colors * ((num_groups // len(colors)) + 1))[:num_groups]
                    colors = extended_colors
                # 使用 color_discrete_sequence 确保每个组颜色不同
                fig.update_layout(color_discrete_sequence=colors[:num_groups] if num_groups > 0 else colors)
            else:
                # 对于单线条图表，直接设置颜色
                if colors:
                    fig.update_traces(line=dict(color=colors[0] if len(colors) > 0 else 'blue'))
        
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
        
        # 应用颜色主题或自定义颜色
        custom_colors = config.get('custom_colors', {})  # {group_value: color}
        if custom_colors and group:
            # 使用自定义颜色映射
            unique_groups = data[group].unique() if group in data.columns else []
            color_map = custom_colors
            color_sequence = []
            theme_colors = self.COLOR_THEMES.get(color_theme, self.COLOR_THEMES['default'])
            if not isinstance(theme_colors, list):
                theme_colors = list(theme_colors) if hasattr(theme_colors, '__iter__') else [theme_colors]
            theme_colors = [str(c) for c in theme_colors if c]
            
            used_colors = set()
            for group_val in unique_groups:
                group_val_str = str(group_val)
                if group_val_str in color_map:
                    custom_color = color_map[group_val_str]
                    if custom_color not in used_colors:
                        color_sequence.append(custom_color)
                        used_colors.add(custom_color)
                    else:
                        for theme_color in theme_colors:
                            if theme_color not in used_colors:
                                color_sequence.append(theme_color)
                                used_colors.add(theme_color)
                                break
                else:
                    for theme_color in theme_colors:
                        if theme_color not in used_colors:
                            color_sequence.append(theme_color)
                            used_colors.add(theme_color)
                            break
            
            if color_sequence:
                fig.update_layout(color_discrete_map={str(k): v for k, v in zip(unique_groups, color_sequence[:len(unique_groups)])})
        elif color_theme in self.COLOR_THEMES:
            colors = self.COLOR_THEMES[color_theme]
            # 确保 colors 是列表且所有元素都是字符串
            if not isinstance(colors, list):
                colors = list(colors) if hasattr(colors, '__iter__') else [colors]
            colors = [str(c) for c in colors if c]
            if group:
                # 对于分组图表，确保每个组使用不同颜色
                unique_groups = data[group].unique() if group in data.columns else []
                num_groups = len(unique_groups)
                # 如果分组数量超过颜色数量，扩展颜色列表（循环使用）
                if num_groups > len(colors):
                    extended_colors = (colors * ((num_groups // len(colors)) + 1))[:num_groups]
                    colors = extended_colors
                # 使用 color_discrete_sequence 确保每个组颜色不同
                fig.update_layout(color_discrete_sequence=colors[:num_groups] if num_groups > 0 else colors)
            else:
                # 对于单柱状图，设置 marker color（必须是颜色字符串）
                if colors:
                    fig.update_traces(marker_color=colors[0])
        
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
        
        # 应用颜色主题或自定义颜色
        custom_colors = config.get('custom_colors', {})  # {group_value: color}
        unique_groups = data[group].unique() if group in data.columns else []
        num_values = len(unique_groups)
        
        if custom_colors and group:
            # 使用自定义颜色映射
            color_sequence = []
            theme_colors = self.COLOR_THEMES.get(color_theme, self.COLOR_THEMES['default'])
            if not isinstance(theme_colors, list):
                theme_colors = list(theme_colors) if hasattr(theme_colors, '__iter__') else [theme_colors]
            theme_colors = [str(c) for c in theme_colors if c]
            
            used_colors = set()
            for group_val in unique_groups:
                group_val_str = str(group_val)
                if group_val_str in custom_colors:
                    custom_color = custom_colors[group_val_str]
                    if custom_color not in used_colors:
                        color_sequence.append(custom_color)
                        used_colors.add(custom_color)
                    else:
                        # 自定义颜色重复，使用主题颜色
                        for theme_color in theme_colors:
                            if theme_color not in used_colors:
                                color_sequence.append(theme_color)
                                used_colors.add(theme_color)
                                break
                else:
                    # 使用主题颜色，确保不重复
                    for theme_color in theme_colors:
                        if theme_color not in used_colors:
                            color_sequence.append(theme_color)
                            used_colors.add(theme_color)
                            break
            # 如果颜色不够，扩展主题颜色
            while len(color_sequence) < num_values:
                for theme_color in theme_colors:
                    if len(color_sequence) >= num_values:
                        break
                    color_sequence.append(theme_color)
            
            if color_sequence:
                fig.update_traces(marker_colors=color_sequence[:num_values])
        elif color_theme in self.COLOR_THEMES:
            colors = self.COLOR_THEMES[color_theme]
            # 确保 colors 是列表
            if not isinstance(colors, list):
                colors = list(colors) if hasattr(colors, '__iter__') else [colors]
            colors = [str(c) for c in colors if c]
            # 对于饼图，确保每个组使用不同颜色
            if colors:
                # 如果数据点数量超过颜色数量，扩展颜色列表（循环使用，但确保不重复）
                if num_values > len(colors):
                    # 扩展颜色列表，但尽量使用不同颜色
                    extended_colors = []
                    used_colors = set()
                    for _ in range(num_values):
                        for color in colors:
                            if color not in used_colors:
                                extended_colors.append(color)
                                used_colors.add(color)
                                break
                        else:
                            # 所有颜色都用过了，循环使用
                            extended_colors.extend(colors * ((num_values - len(extended_colors)) // len(colors) + 1))
                            break
                    colors = extended_colors[:num_values]
                fig.update_traces(marker_colors=colors[:num_values])
        
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

