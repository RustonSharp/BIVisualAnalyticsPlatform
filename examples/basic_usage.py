"""
示例脚本：使用 BI Platform 进行数据分析
展示核心 API 的使用方法
"""

import sys
import os

# 添加项目路径到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bi_visual_analytics.adapters import CSVAdapter
from bi_visual_analytics.charts import ChartEngine
from bi_visual_analytics.utils import ConfigManager
from bi_visual_analytics.dashboard import ExportHandler


def example_csv_adapter():
    """示例 1：使用 CSV 适配器"""
    print("\n=== 示例 1：CSV 数据源 ===")

    adapter = CSVAdapter()

    # 连接数据源
    success = adapter.connect({"file_path": "data/sample_sales.csv", "encoding": "utf-8"})

    if success:
        print("✓ 成功连接到 CSV 文件")

        # 获取数据概览
        schema = adapter.get_schema()
        print(f"✓ 数据字段: {schema['columns']}")
        print(f"✓ 数据行数: {schema['row_count']}")

        # 预览数据
        preview = adapter.preview_data(5)
        print("\n前 5 行数据:")
        print(preview)

        # 获取全部数据
        data = adapter.fetch_data()
        return data
    else:
        print("✗ 连接失败")
        return None


def example_chart_engine(data):
    """示例 2：使用图表引擎"""
    print("\n=== 示例 2：生成图表 ===")

    engine = ChartEngine()

    # 创建折线图
    print("\n生成折线图...")
    fig_line = engine.create_chart(
        data=data,
        config={
            "type": "line",
            "x": "date",
            "y": "sales",
            "agg_func": "sum",
            "title": "每日销售额趋势",
            "color_theme": "business",
            "height": 500,
        },
    )
    print("✓ 折线图已生成")

    # 创建柱状图
    print("\n生成柱状图...")
    fig_bar = engine.create_chart(
        data=data,
        config={
            "type": "bar",
            "x": "region",
            "y": "sales",
            "agg_func": "sum",
            "title": "各地区销售额对比",
            "color_theme": "ocean",
        },
    )
    print("✓ 柱状图已生成")

    # 创建饼图
    print("\n生成饼图...")
    fig_pie = engine.create_chart(
        data=data,
        config={
            "type": "pie",
            "names": "category",
            "values": "sales",
            "title": "产品类别销售占比",
            "color_theme": "sunset",
            "hole": 0.4,  # 环形图
        },
    )
    print("✓ 饼图已生成")

    return [fig_line, fig_bar, fig_pie]


def example_data_filtering(data):
    """示例 3：数据筛选"""
    print("\n=== 示例 3：数据筛选 ===")

    engine = ChartEngine()

    # 时间范围筛选
    print("\n应用时间筛选（最近 30 天）...")
    filtered_data = engine.apply_filters(
        data, {"quick_date": {"column": "date", "period": "last_30_days"}}
    )
    print(f"✓ 筛选后数据行数: {len(filtered_data)}")

    # 类别筛选
    print("\n应用类别筛选（仅华东、华南地区）...")
    filtered_data = engine.apply_filters(
        filtered_data, {"category": {"region": ["华东", "华南"]}}
    )
    print(f"✓ 筛选后数据行数: {len(filtered_data)}")

    return filtered_data


def example_data_aggregation(data):
    """示例 4：数据聚合"""
    print("\n=== 示例 4：数据聚合 ===")

    engine = ChartEngine()

    # 按地区聚合销售额
    print("\n按地区聚合销售额...")
    agg_data = engine.aggregate_data(
        data, {"group_by": "region", "agg_func": "sum", "y": "sales"}
    )
    print("✓ 聚合结果:")
    print(agg_data)

    return agg_data


def example_export_handler(charts):
    """示例 5：导出功能"""
    print("\n=== 示例 5：导出图表 ===")

    handler = ExportHandler()

    # 创建导出目录
    os.makedirs("exports", exist_ok=True)

    # 导出第一个图表为 PNG
    print("\n导出折线图为 PNG...")
    handler.export_chart_as_image(charts[0], "exports/line_chart.png", format="png")
    print("✓ 已保存到 exports/line_chart.png")

    # 导出仪表盘为 HTML
    print("\n导出仪表盘为 HTML...")
    chart_list = [
        {"id": "line", "fig": charts[0], "title": "销售趋势"},
        {"id": "bar", "fig": charts[1], "title": "地区对比"},
        {"id": "pie", "fig": charts[2], "title": "类别占比"},
    ]

    handler.export_dashboard_as_html(
        charts=chart_list, output_path="exports/dashboard.html", title="销售分析仪表盘"
    )
    print("✓ 已保存到 exports/dashboard.html")


def example_config_manager():
    """示例 6：配置管理"""
    print("\n=== 示例 6：配置管理 ===")

    manager = ConfigManager()

    # 加载数据源配置
    print("\n加载数据源配置...")
    try:
        config = manager.load_datasource_config("config/datasource_csv_template.yaml")
        print("✓ 配置加载成功:")
        print(f"  - 名称: {config.get('name')}")
        print(f"  - 类型: {config.get('type')}")
        print(f"  - 文件路径: {config.get('file_path')}")
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")

    # 创建新配置
    print("\n创建新的数据源配置...")
    new_config = {
        "name": "测试数据源",
        "type": "csv",
        "file_path": "data/test.csv",
        "encoding": "utf-8",
    }

    try:
        manager.save_datasource_config(new_config, "config/test_datasource.yaml")
        print("✓ 配置已保存到 config/test_datasource.yaml")
    except Exception as e:
        print(f"✗ 保存失败: {e}")


def main():
    """主函数：运行所有示例"""
    print("=" * 60)
    print("BI Visual Analytics Platform - 示例脚本")
    print("=" * 60)

    # 示例 1：加载数据
    data = example_csv_adapter()

    if data is not None:
        # 示例 2：生成图表
        charts = example_chart_engine(data)

        # 示例 3：数据筛选
        filtered_data = example_data_filtering(data)

        # 示例 4：数据聚合
        agg_data = example_data_aggregation(data)

        # 示例 5：导出
        example_export_handler(charts)

        # 示例 6：配置管理
        example_config_manager()

        print("\n" + "=" * 60)
        print("✓ 所有示例运行完成！")
        print("请查看 exports/ 目录查看导出的文件")
        print("=" * 60)
    else:
        print("\n✗ 数据加载失败，请检查 data/sample_sales.csv 文件是否存在")


if __name__ == "__main__":
    main()
