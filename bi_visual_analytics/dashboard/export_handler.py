"""
导出处理器
负责将仪表盘导出为各种格式
"""

import os
import json
from typing import Dict, Any, List
from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio


class ExportHandler:
    """导出处理器"""

    def __init__(self):
        # 配置 Plotly 默认导出设置
        pio.kaleido.scope.mathjax = None

    def export_chart_as_image(
        self, fig: go.Figure, output_path: str, format: str = "png", **kwargs
    ):
        """
        导出图表为图片

        Args:
            fig: Plotly 图表对象
            output_path: 输出路径
            format: 图片格式 (png/jpeg/svg)
            **kwargs: 其他参数（width, height, scale）
        """
        # 默认参数
        width = kwargs.get("width", 1200)
        height = kwargs.get("height", 600)
        scale = kwargs.get("scale", 2)

        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 导出图片
        fig.write_image(
            output_path, format=format, width=width, height=height, scale=scale
        )

    def export_chart_as_html(
        self, fig: go.Figure, output_path: str, include_plotlyjs: str = "cdn"
    ):
        """
        导出图表为 HTML

        Args:
            fig: Plotly 图表对象
            output_path: 输出路径
            include_plotlyjs: plotly.js 包含方式 ('cdn'/'inline'/False)
        """
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 导出 HTML
        fig.write_html(output_path, include_plotlyjs=include_plotlyjs)

    def export_dashboard_as_html(
        self,
        charts: List[Dict[str, Any]],
        output_path: str,
        title: str = "BI Dashboard",
        include_data: bool = True,
    ):
        """
        导出整个仪表盘为单个 HTML 文件

        Args:
            charts: 图表列表，每个元素包含 {id, fig, title}
            output_path: 输出路径
            title: 仪表盘标题
            include_data: 是否内嵌数据
        """
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 生成 HTML 内容
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"    <title>{title}</title>",
            '    <meta charset="utf-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1">',
            '    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>',
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }",
            "        h1 { text-align: center; color: #333; }",
            "        .chart-container { background: white; padding: 20px; margin: 20px 0; ",
            "                          border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "        .chart-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }",
            "    </style>",
            "</head>",
            "<body>",
            f"    <h1>{title}</h1>",
        ]

        # 添加每个图表
        for chart in charts:
            chart_id = chart.get("id", f"chart-{len(html_parts)}")
            chart_title = chart.get("title", "")
            fig = chart.get("fig")

            if fig:
                html_parts.append('    <div class="chart-container">')
                if chart_title:
                    html_parts.append(f'        <div class="chart-title">{chart_title}</div>')
                html_parts.append(f'        <div id="{chart_id}"></div>')
                html_parts.append("    </div>")

                # 生成图表的 JavaScript
                fig_json = fig.to_json()
                html_parts.append("    <script>")
                html_parts.append(f"        var data_{chart_id} = {fig_json};")
                html_parts.append(
                    f"        Plotly.newPlot('{chart_id}', data_{chart_id}.data, data_{chart_id}.layout);"
                )
                html_parts.append("    </script>")

        html_parts.extend(["</body>", "</html>"])

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))

    def export_dashboard_as_pdf(self, charts: List[Dict[str, Any]], output_path: str):
        """
        导出仪表盘为 PDF

        Args:
            charts: 图表列表
            output_path: 输出路径

        Note:
            需要安装 kaleido: pip install kaleido
        """
        try:
            from PIL import Image
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            import tempfile

        except ImportError:
            raise ImportError(
                "导出 PDF 需要安装额外依赖: pip install pillow reportlab kaleido"
            )

        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 创建 PDF
        c = canvas.Canvas(output_path, pagesize=landscape(A4))
        page_width, page_height = landscape(A4)

        y_position = page_height - 50

        # 添加标题
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y_position, "BI Dashboard Report")
        y_position -= 40

        # 为每个图表创建临时图片
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, chart in enumerate(charts):
                fig = chart.get("fig")
                title = chart.get("title", f"Chart {i+1}")

                if not fig:
                    continue

                # 导出为临时图片
                temp_img_path = os.path.join(temp_dir, f"chart_{i}.png")
                self.export_chart_as_image(
                    fig, temp_img_path, format="png", width=800, height=400
                )

                # 检查是否需要新页面
                if y_position < 250:
                    c.showPage()
                    y_position = page_height - 50

                # 添加图表标题
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y_position, title)
                y_position -= 20

                # 添加图片
                img = ImageReader(temp_img_path)
                img_width = page_width - 100
                img_height = 200

                c.drawImage(
                    img, 50, y_position - img_height, width=img_width, height=img_height
                )
                y_position -= img_height + 30

        c.save()

    def export_data_as_csv(self, data: Any, output_path: str):
        """
        导出数据为 CSV

        Args:
            data: pandas DataFrame 或字典
            output_path: 输出路径
        """
        import pandas as pd

        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 转换为 DataFrame
        if isinstance(data, dict):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("数据必须是 DataFrame 或字典格式")

        # 导出 CSV
        df.to_csv(output_path, index=False, encoding="utf-8-sig")

    def export_config_as_json(self, config: Dict[str, Any], output_path: str):
        """
        导出配置为 JSON

        Args:
            config: 配置字典
            output_path: 输出路径
        """
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 导出 JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
