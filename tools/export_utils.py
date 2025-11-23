"""仪表盘导出工具函数"""
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any
import plotly.graph_objects as go


def generate_dashboard_html(
    dashboard_config: Dict[str, Any],
    figures_with_titles: List[Tuple[go.Figure, str, str]]
) -> str:
    """生成仪表盘的HTML内容
    
    Args:
        dashboard_config: 仪表盘配置
        figures_with_titles: 图表列表，每个元素为 (figure, title, chart_type)
    
    Returns:
        HTML内容字符串
    """
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dashboard_config.get('name', '仪表盘')}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #f8f9fa;
            padding: 20px;
        }}
        .dashboard-header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .dashboard-title {{
            font-size: 2rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }}
        .dashboard-description {{
            color: #666;
            font-size: 1rem;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .chart-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }}
        .chart-content {{
            min-height: 400px;
        }}
        .footer {{
            text-align: center;
            color: #999;
            padding: 20px;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="dashboard-header">
            <h1 class="dashboard-title">{dashboard_config.get('name', '仪表盘')}</h1>
            <p class="dashboard-description">{dashboard_config.get('description', '数据可视化仪表盘')}</p>
            <p class="text-muted small">导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
"""
    
    for idx, (fig, title, chart_type) in enumerate(figures_with_titles):
        chart_html = fig.to_html(include_plotlyjs=False, div_id=f"dashboard-chart-{idx}", full_html=False)
        html_content += f"""
        <div class="chart-container">
            <h3 class="chart-title">{title}</h3>
            <div class="chart-content">
                {chart_html}
            </div>
        </div>
"""
    
    html_content += """
        <div class="footer">
            <p>由 BI 数据可视化与分析平台生成</p>
        </div>
    </div>
</body>
</html>"""
    
    return html_content


def html_to_png(html_path: Path, output_path: Path) -> bool:
    """将HTML文件转换为PNG图片
    
    Args:
        html_path: HTML文件路径
        output_path: 输出PNG文件路径
    
    Returns:
        是否转换成功
    """
    # 方法1: 尝试使用imgkit (需要wkhtmltopdf)
    try:
        import imgkit  # type: ignore
        print(f"[HTML转PNG] 尝试使用imgkit转换...")
        options = {
            'format': 'png',
            'width': 1400,
            'disable-smart-shrinking': True
        }
        imgkit.from_file(str(html_path), str(output_path), options=options)
        print(f"[HTML转PNG] 使用imgkit转换成功: {output_path}")
        return True
    except (ImportError, Exception) as e:
        print(f"[HTML转PNG] imgkit不可用或失败: {str(e)}")
    
    # 方法2: 尝试使用Playwright
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        print(f"[HTML转PNG] 尝试使用Playwright转换...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1400, "height": 2000})
            html_file_url = f"file://{html_path.absolute()}"
            page.goto(html_file_url)
            page.wait_for_timeout(3000)  # 等待图表渲染
            page.screenshot(path=str(output_path), full_page=True)
            browser.close()
        print(f"[HTML转PNG] 使用Playwright转换成功: {output_path}")
        return True
    except (ImportError, Exception) as e:
        print(f"[HTML转PNG] Playwright不可用或失败: {str(e)}")
    
    return False


def html_to_pdf(html_path: Path, output_path: Path) -> bool:
    """将HTML文件转换为PDF文件
    
    Args:
        html_path: HTML文件路径
        output_path: 输出PDF文件路径
    
    Returns:
        是否转换成功
    """
    # 方法1: 尝试使用imgkit (需要wkhtmltopdf)
    try:
        import imgkit  # type: ignore
        print(f"[HTML转PDF] 尝试使用imgkit转换...")
        options = {
            'format': 'pdf',
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'disable-smart-shrinking': True
        }
        imgkit.from_file(str(html_path), str(output_path), options=options)
        print(f"[HTML转PDF] 使用imgkit转换成功: {output_path}")
        return True
    except (ImportError, Exception) as e:
        print(f"[HTML转PDF] imgkit不可用或失败: {str(e)}")
    
    # 方法2: 尝试使用Playwright
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        print(f"[HTML转PDF] 尝试使用Playwright转换...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1200, "height": 1600})
            html_file_url = f"file://{html_path.absolute()}"
            page.goto(html_file_url)
            page.wait_for_timeout(3000)  # 等待图表渲染
            page.pdf(path=str(output_path), format='A4', print_background=True)
            browser.close()
        print(f"[HTML转PDF] 使用Playwright转换成功: {output_path}")
        return True
    except (ImportError, Exception) as e:
        print(f"[HTML转PDF] Playwright不可用或失败: {str(e)}")
    
    return False


def export_dashboard_to_html(
    dashboard_config: Dict[str, Any],
    figures_with_titles: List[Tuple[go.Figure, str, str]],
    export_dir: Path,
    timestamp: str
) -> Path:
    """导出仪表盘为HTML文件
    
    Args:
        dashboard_config: 仪表盘配置
        figures_with_titles: 图表列表
        export_dir: 导出目录
        timestamp: 时间戳
    
    Returns:
        导出文件路径
    """
    dashboard_name = (dashboard_config.get('name', 'dashboard')).replace(" ", "_").replace("/", "_")
    export_path = export_dir / f"{dashboard_name}_{timestamp}.html"
    
    html_content = generate_dashboard_html(dashboard_config, figures_with_titles)
    
    with open(export_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[HTML导出] 仪表盘已导出为HTML: {export_path}")
    return export_path


def export_dashboard_to_png(
    dashboard_config: Dict[str, Any],
    figures_with_titles: List[Tuple[go.Figure, str, str]],
    export_dir: Path,
    timestamp: str
) -> Path:
    """导出仪表盘为PNG图片（先转HTML再转PNG）
    
    Args:
        dashboard_config: 仪表盘配置
        figures_with_titles: 图表列表
        export_dir: 导出目录
        timestamp: 时间戳
    
    Returns:
        导出文件路径
    
    Raises:
        Exception: 如果转换失败
    """
    dashboard_name = (dashboard_config.get('name', 'dashboard')).replace(" ", "_").replace("/", "_")
    export_path = export_dir / f"{dashboard_name}_{timestamp}.png"
    
    # 步骤1: 生成HTML内容
    print(f"[PNG导出] 步骤1: 生成HTML内容...")
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dashboard_config.get('name', '仪表盘')}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: white;
            font-family: Arial, sans-serif;
        }}
        .chart-container {{
            margin-bottom: 30px;
            page-break-after: auto;
        }}
        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }}
    </style>
</head>
<body>
"""
    
    for idx, (fig, title, chart_type) in enumerate(figures_with_titles):
        chart_html = fig.to_html(include_plotlyjs=False, div_id=f"chart-{idx}", full_html=False)
        html_content += f"""
    <div class="chart-container">
        <div class="chart-title">{title}</div>
        {chart_html}
    </div>
"""
    
    html_content += """
</body>
</html>"""
    
    # 步骤2: 保存HTML临时文件
    temp_html_path = export_dir / f"temp_dashboard_{timestamp}.html"
    print(f"[PNG导出] 步骤2: 保存HTML到临时文件: {temp_html_path}")
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    try:
        # 步骤3: 尝试将HTML转PNG
        print(f"[PNG导出] 步骤3: 将HTML转换为PNG...")
        html_converted = html_to_png(temp_html_path, export_path)
        
        # 如果HTML转PNG失败，回退到Kaleido直接转换
        if not html_converted:
            print(f"[PNG导出] HTML转PNG失败，回退到Kaleido直接转换...")
            try:
                import kaleido
                # 如果只有一个图表，直接转换
                if len(figures_with_titles) == 1:
                    fig, title, chart_type = figures_with_titles[0]
                    img_bytes = fig.to_image(format="png", width=1200, height=800, scale=1, engine='kaleido')
                    with open(export_path, 'wb') as f:
                        f.write(img_bytes)
                else:
                    # 多个图表需要组合
                    from PIL import Image
                    chart_images = []
                    for idx, (fig, title, chart_type) in enumerate(figures_with_titles):
                        temp_img = export_dir / f"temp_chart_{idx}_{timestamp}.png"
                        img_bytes = fig.to_image(format="png", width=1000, height=600, scale=1, engine='kaleido')
                        with open(temp_img, 'wb') as f:
                            f.write(img_bytes)
                        chart_images.append((Image.open(temp_img), title))
                        temp_img.unlink()
                    
                    # 组合图片
                    chart_width = 1000
                    chart_height = 600
                    spacing = 50
                    total_height = sum(chart_height + spacing for _, _ in chart_images) - spacing
                    combined_img = Image.new('RGB', (chart_width, total_height), color=0xFFFFFF)
                    y_offset = 0
                    for img, _ in chart_images:
                        combined_img.paste(img, (0, y_offset))
                        y_offset += chart_height + spacing
                    combined_img.save(str(export_path))
                print(f"[PNG导出] 使用Kaleido转换成功: {export_path}")
            except Exception as e:
                print(f"[PNG导出] Kaleido转换失败: {str(e)}")
                raise Exception("无法将HTML转换为PNG，请安装imgkit、playwright或kaleido库")
    finally:
        # 清理临时HTML文件
        if temp_html_path.exists():
            temp_html_path.unlink()
            print(f"[PNG导出] 临时HTML文件已清理")
    
    print(f"[PNG导出] PNG导出完成: {export_path}")
    return export_path


def export_dashboard_to_pdf(
    dashboard_config: Dict[str, Any],
    figures_with_titles: List[Tuple[go.Figure, str, str]],
    export_dir: Path,
    timestamp: str
) -> Path:
    """导出仪表盘为PDF文件（先转HTML再转PDF）
    
    Args:
        dashboard_config: 仪表盘配置
        figures_with_titles: 图表列表
        export_dir: 导出目录
        timestamp: 时间戳
    
    Returns:
        导出文件路径
    
    Raises:
        Exception: 如果转换失败
    """
    dashboard_name = (dashboard_config.get('name', 'dashboard')).replace(" ", "_").replace("/", "_")
    export_path = export_dir / f"{dashboard_name}_{timestamp}.pdf"
    
    # 步骤1: 生成HTML内容（使用完整的HTML模板，和HTML导出一样）
    print(f"[PDF导出] 步骤1: 生成HTML内容...")
    html_content = generate_dashboard_html(dashboard_config, figures_with_titles)
    
    # 步骤2: 保存HTML临时文件
    temp_html_path = export_dir / f"temp_dashboard_{timestamp}.html"
    print(f"[PDF导出] 步骤2: 保存HTML到临时文件: {temp_html_path}")
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    try:
        # 步骤3: 尝试将HTML转PDF
        print(f"[PDF导出] 步骤3: 将HTML转换为PDF...")
        html_converted = html_to_pdf(temp_html_path, export_path)
        
        # 如果HTML转PDF失败，回退到reportlab方案
        if not html_converted:
            print(f"[PDF导出] HTML转PDF失败，回退到reportlab方案...")
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from PIL import Image
                import io as io_module
                
                c = canvas.Canvas(str(export_path), pagesize=A4)
                page_width, page_height = A4
                
                temp_images = []
                for idx, (fig, title, chart_type) in enumerate(figures_with_titles):
                    print(f"[PDF导出] 正在处理图表 {idx+1}/{len(figures_with_titles)}: {title}")
                    try:
                        img_bytes = fig.to_image(format="png", width=1000, height=600, scale=2, engine='kaleido')
                    except Exception as e:
                        print(f"[PDF导出] 图表 {idx+1} 图像生成失败，尝试不使用engine参数: {str(e)}")
                        img_bytes = fig.to_image(format="png", width=1000, height=600, scale=2)
                    img = Image.open(io_module.BytesIO(img_bytes))
                    
                    img_width, img_height = img.size
                    scale = min((page_width - 100) / img_width, (page_height - 150) / img_height)
                    new_width = img_width * scale
                    new_height = img_height * scale
                    
                    img = img.resize((int(new_width), int(new_height)), Image.Resampling.LANCZOS)
                    
                    temp_img_path = export_dir / f"temp_chart_{idx}_{timestamp}.png"
                    img.save(temp_img_path)
                    temp_images.append(temp_img_path)
                    
                    if idx > 0:
                        c.showPage()
                    
                    c.setFont("Helvetica-Bold", 16)
                    title_width = c.stringWidth(title, "Helvetica-Bold", 16)
                    c.drawString((page_width - title_width) / 2, page_height - 50, title)
                    
                    x = (page_width - new_width) / 2
                    y = page_height - 100 - new_height
                    c.drawImage(str(temp_img_path), x, y, width=new_width, height=new_height)
                
                c.save()
                
                # 清理临时图片
                for temp_img in temp_images:
                    if temp_img.exists():
                        temp_img.unlink()
                
                print(f"[PDF导出] 使用reportlab转换成功: {export_path}")
            except ImportError:
                # 如果没有reportlab，尝试使用kaleido直接导出PDF
                if len(figures_with_titles) == 1:
                    figures_with_titles[0][0].write_image(str(export_path), format="pdf", width=1200, height=800)
                    print(f"[PDF导出] 使用Kaleido导出PDF: {export_path}")
                else:
                    raise Exception("PDF导出需要安装imgkit（需要wkhtmltopdf）、playwright或reportlab库。")
            except Exception as e:
                print(f"[PDF导出] reportlab转换失败: {str(e)}")
                raise Exception(f"PDF导出失败：{str(e)}。请安装imgkit（需要wkhtmltopdf）、playwright或reportlab库。")
    finally:
        # 清理临时HTML文件
        if temp_html_path.exists():
            temp_html_path.unlink()
            print(f"[PDF导出] 临时HTML文件已清理")
    
    print(f"[PDF导出] PDF导出完成: {export_path}")
    return export_path

