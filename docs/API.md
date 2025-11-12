# API 文档

## 目录

- [数据源适配器 API](#数据源适配器-api)
- [图表引擎 API](#图表引擎-api)
- [配置管理器 API](#配置管理器-api)
- [仪表盘管理 API](#仪表盘管理-api)
- [导出处理器 API](#导出处理器-api)

---

## 数据源适配器 API

### DataSourceAdapter (基类)

所有数据源适配器的抽象基类。

#### 方法

##### `connect(config: Dict[str, Any]) -> bool`

建立数据源连接。

**参数：**
- `config` (dict): 连接配置字典

**返回：**
- `bool`: 连接是否成功

**示例：**
```python
adapter = CSVAdapter()
success = adapter.connect({"file_path": "data.csv"})
```

##### `fetch_data(query: Optional[Dict[str, Any]]) -> pd.DataFrame`

获取数据。

**参数：**
- `query` (dict, 可选): 查询条件

**返回：**
- `pd.DataFrame`: 数据结果

##### `get_schema() -> Dict[str, Any]`

获取数据源的字段信息。

**返回：**
- `dict`: 字段名称和类型的映射

---

### CSVAdapter

CSV/Excel 文件适配器。

#### 配置参数

```python
config = {
    "file_path": str,        # 文件路径（必需）
    "encoding": str,         # 编码方式，默认 "utf-8"
    "separator": str,        # CSV 分隔符，默认 ","
    "sheet_name": str/int,   # Excel 工作表名称或索引，默认 0
}
```

#### 查询参数

```python
query = {
    "columns": List[str],    # 要返回的列名列表
    "limit": int,           # 返回行数限制
    "filters": List[dict],  # 筛选条件
}
```

#### 示例

```python
from bi_visual_analytics.adapters import CSVAdapter

# 连接 CSV 文件
adapter = CSVAdapter()
adapter.connect({
    "file_path": "sales.csv",
    "encoding": "utf-8",
    "separator": ","
})

# 获取所有数据
all_data = adapter.fetch_data()

# 获取指定列
specific_data = adapter.fetch_data({
    "columns": ["date", "sales"],
    "limit": 100
})

# 预览数据
preview = adapter.preview_data(10)

# 获取字段信息
schema = adapter.get_schema()
# 返回: {"columns": [...], "types": {...}, "row_count": 1000}
```

---

### DatabaseAdapter

关系型数据库适配器（支持 PostgreSQL、MySQL）。

#### 配置参数

```python
config = {
    "db_type": str,          # 数据库类型: "postgresql" 或 "mysql"（必需）
    "host": str,             # 主机地址（必需）
    "port": int,             # 端口号（必需）
    "database": str,         # 数据库名（必需）
    "username": str,         # 用户名（必需）
    "password": str,         # 密码（必需）
    "table": str,            # 表名（可选）
}
```

#### 查询参数

```python
query = {
    "sql": str,             # 自定义 SQL 查询
    "table": str,           # 表名
    "columns": List[str],   # 列名列表
    "limit": int,           # 行数限制
    "where": str,           # WHERE 条件
}
```

#### 示例

```python
from bi_visual_analytics.adapters import DatabaseAdapter

# 连接 PostgreSQL
adapter = DatabaseAdapter()
adapter.connect({
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "sales_db",
    "username": "user",
    "password": "password",
    "table": "sales"
})

# 使用自定义 SQL
data = adapter.fetch_data({
    "sql": "SELECT * FROM sales WHERE date >= '2024-01-01'"
})

# 使用简化查询
data = adapter.fetch_data({
    "table": "sales",
    "columns": ["date", "revenue"],
    "limit": 1000
})

# 获取所有表名
tables = adapter.get_tables()
```

---

### APIAdapter

REST API 数据适配器。

#### 配置参数

```python
config = {
    "url": str,                      # API 地址（必需）
    "method": str,                   # 请求方法: "GET" 或 "POST"，默认 "GET"
    "headers": Dict[str, str],       # 请求头
    "params": Dict[str, Any],        # 请求参数
    "data": Dict[str, Any],          # POST 请求体
    "auth": Dict[str, str],          # 认证信息
    "json_path": str,                # JSON 数据路径
}
```

#### 示例

```python
from bi_visual_analytics.adapters import APIAdapter

# 连接 API
adapter = APIAdapter()
adapter.connect({
    "url": "https://api.example.com/sales",
    "method": "GET",
    "headers": {
        "Content-Type": "application/json"
    },
    "auth": {
        "api_key": "your_api_key"
    },
    "json_path": "data.results"
})

# 获取数据
data = adapter.fetch_data()

# 刷新数据（重新请求）
adapter.refresh()
```

---

## 图表引擎 API

### ChartEngine

图表生成核心引擎。

#### 支持的图表类型

- `line` - 折线图
- `bar` - 柱状图
- `pie` - 饼图
- `table` - 表格
- `scatter` - 散点图
- `area` - 面积图
- `histogram` - 直方图

#### 方法

##### `create_chart(data: pd.DataFrame, config: Dict[str, Any]) -> go.Figure`

根据配置生成图表。

**图表配置参数：**

```python
config = {
    # 基础配置
    "type": str,              # 图表类型（必需）
    "x": str,                # X 轴字段（必需）
    "y": str,                # Y 轴字段（必需）
    
    # 数据处理
    "group_by": str,         # 分组字段
    "agg_func": str,         # 聚合函数: sum/mean/count/max/min
    
    # 样式配置
    "title": str,            # 图表标题
    "color_theme": str,      # 配色方案: default/business/ocean/earth/sunset
    "show_legend": bool,     # 是否显示图例，默认 True
    "legend_position": str,  # 图例位置: top/bottom/left/right
    "height": int,           # 图表高度（像素），默认 500
    
    # 坐标轴
    "xaxis_title": str,      # X 轴标题
    "yaxis_title": str,      # Y 轴标题
    
    # 其他
    "show_data_labels": bool, # 是否显示数据标签
    "template": str,          # Plotly 主题模板
}
```

**示例：**

```python
from bi_visual_analytics.charts import ChartEngine
import pandas as pd

engine = ChartEngine()
df = pd.read_csv("sales.csv")

# 创建折线图
fig = engine.create_chart(
    data=df,
    config={
        "type": "line",
        "x": "date",
        "y": "sales",
        "title": "月度销售趋势",
        "color_theme": "business",
        "height": 600
    }
)

# 显示图表
fig.show()

# 保存为图片
fig.write_image("chart.png")
```

##### `aggregate_data(data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame`

数据聚合。

**参数：**
```python
config = {
    "group_by": str,    # 分组字段
    "agg_func": str,    # 聚合函数
    "y": str,          # 数值字段
}
```

**示例：**
```python
agg_data = engine.aggregate_data(df, {
    "group_by": "category",
    "agg_func": "sum",
    "y": "sales"
})
```

##### `apply_filters(data: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame`

应用筛选条件。

**筛选器配置：**

```python
filters = {
    # 时间范围筛选
    "date_range": {
        "column": "date",
        "start": "2024-01-01",
        "end": "2024-12-31"
    },
    
    # 快捷时间筛选
    "quick_date": {
        "column": "date",
        "period": "last_30_days"  # today/yesterday/last_7_days/last_30_days
    },
    
    # 类别筛选
    "category": {
        "region": ["华东", "华南"],
        "product": "笔记本电脑"
    }
}
```

**示例：**
```python
filtered_data = engine.apply_filters(df, {
    "quick_date": {
        "column": "date",
        "period": "last_30_days"
    },
    "category": {
        "region": ["华东", "华南"]
    }
})
```

---

## 配置管理器 API

### ConfigManager

配置文件读写与验证。

#### 方法

##### `load_datasource_config(path: str) -> Dict[str, Any]`

加载数据源配置（支持 YAML/JSON）。

**示例：**
```python
from bi_visual_analytics.utils import ConfigManager

manager = ConfigManager()
config = manager.load_datasource_config("config/my_datasource.yaml")
```

##### `save_datasource_config(config: Dict[str, Any], path: str)`

保存数据源配置。

**示例：**
```python
manager.save_datasource_config({
    "name": "销售数据",
    "type": "csv",
    "file_path": "sales.csv"
}, "config/sales_datasource.yaml")
```

##### `load_dashboard_config(path: str) -> Dict[str, Any]`

加载仪表盘配置（JSON）。

##### `save_dashboard_config(config: Dict[str, Any], path: str)`

保存仪表盘配置。

##### `validate_datasource_config(config: Dict[str, Any]) -> bool`

验证数据源配置格式。

##### `validate_dashboard_config(config: Dict[str, Any]) -> bool`

验证仪表盘配置格式。

---

## 仪表盘管理 API

### LayoutManager

仪表盘布局管理器。

#### 方法

##### `add_component(component_id: str, component_type: str, config: Dict, position: Dict)`

添加组件到布局。

**参数：**
```python
position = {
    "x": int,  # X 坐标（0-11）
    "y": int,  # Y 坐标
    "w": int,  # 宽度（1-12）
    "h": int,  # 高度
}
```

**示例：**
```python
from bi_visual_analytics.dashboard import LayoutManager

layout = LayoutManager(columns=12, row_height=100)
layout.add_component(
    component_id="chart1",
    component_type="chart",
    config={"type": "line", "x": "date", "y": "sales"},
    position={"x": 0, "y": 0, "w": 6, "h": 4}
)
```

##### `export_layout() -> Dict[str, Any]`

导出布局配置。

##### `load_layout(layout_config: Dict[str, Any])`

加载布局配置。

---

## 导出处理器 API

### ExportHandler

导出功能处理器。

#### 方法

##### `export_chart_as_image(fig: go.Figure, output_path: str, format: str, **kwargs)`

导出图表为图片。

**参数：**
- `format`: "png" / "jpeg" / "svg"
- `width`: 图片宽度，默认 1200
- `height`: 图片高度，默认 600
- `scale`: 缩放比例，默认 2

**示例：**
```python
from bi_visual_analytics.dashboard import ExportHandler

handler = ExportHandler()
handler.export_chart_as_image(
    fig=my_chart,
    output_path="chart.png",
    format="png",
    width=1600,
    height=800
)
```

##### `export_dashboard_as_html(charts: List[Dict], output_path: str, title: str)`

导出仪表盘为 HTML。

**示例：**
```python
handler.export_dashboard_as_html(
    charts=[
        {"id": "chart1", "fig": fig1, "title": "销售趋势"},
        {"id": "chart2", "fig": fig2, "title": "产品占比"}
    ],
    output_path="dashboard.html",
    title="销售分析仪表盘"
)
```

##### `export_dashboard_as_pdf(charts: List[Dict], output_path: str)`

导出仪表盘为 PDF。

##### `export_data_as_csv(data: pd.DataFrame, output_path: str)`

导出数据为 CSV。

---

## 完整示例

### 端到端数据分析流程

```python
from bi_visual_analytics.adapters import CSVAdapter
from bi_visual_analytics.charts import ChartEngine
from bi_visual_analytics.dashboard import ExportHandler

# 1. 连接数据源
adapter = CSVAdapter()
adapter.connect({"file_path": "data/sales.csv"})
data = adapter.fetch_data()

# 2. 创建图表引擎
engine = ChartEngine()

# 3. 应用筛选
filtered_data = engine.apply_filters(data, {
    "quick_date": {
        "column": "date",
        "period": "last_30_days"
    }
})

# 4. 生成多个图表
fig1 = engine.create_chart(filtered_data, {
    "type": "line",
    "x": "date",
    "y": "sales",
    "title": "销售趋势"
})

fig2 = engine.create_chart(filtered_data, {
    "type": "pie",
    "names": "category",
    "values": "sales",
    "title": "类别占比"
})

# 5. 导出仪表盘
handler = ExportHandler()
handler.export_dashboard_as_html(
    charts=[
        {"id": "trend", "fig": fig1, "title": "销售趋势"},
        {"id": "category", "fig": fig2, "title": "类别占比"}
    ],
    output_path="sales_dashboard.html",
    title="销售分析仪表盘"
)
```

---

## 错误处理

所有 API 在遇到错误时会抛出相应的异常：

- `FileNotFoundError`: 文件不存在
- `ValueError`: 参数值错误
- `RuntimeError`: 运行时错误（如未连接数据源）
- `ConnectionError`: 连接失败（数据库/API）

**建议使用 try-except 处理：**

```python
try:
    adapter = CSVAdapter()
    adapter.connect({"file_path": "data.csv"})
    data = adapter.fetch_data()
except FileNotFoundError as e:
    print(f"文件不存在: {e}")
except Exception as e:
    print(f"发生错误: {e}")
```

---

## 更多资源

- [用户手册](USER_GUIDE.md)
- [配置示例](../config/)
- [项目主页](../README.md)
