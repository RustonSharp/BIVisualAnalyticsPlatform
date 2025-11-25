# 数据下钻功能说明文档

## 📋 功能概述

数据下钻功能允许用户从汇总图表中查看详细的数据记录。当用户在仪表盘的图表上双击某个数据点时，系统会显示该数据点对应的所有原始详细数据。

## 🎯 功能特点

### 1. **支持多种图表类型**
- ✅ **柱状图（Bar Chart）**：双击柱状图中的某个柱子，显示该X轴值对应的所有详细数据
- ✅ **折线图（Line Chart）**：双击折线图中的某个数据点，显示该X轴值对应的所有详细数据
- ✅ **组合图（Combo Chart）**：双击组合图中的数据点，显示该X轴值对应的所有详细数据
- ✅ **饼图（Pie Chart）**：双击饼图中的某个扇形，显示该分类的所有详细数据

### 2. **交互方式**
- **触发方式**：双击图表上的数据点
- **显示方式**：在模态框中显示详细数据表格
- **数据范围**：显示最多100条记录（避免数据过多导致页面卡顿）

### 3. **数据筛选逻辑**
- 根据图表类型和双击的位置，自动确定筛选条件
- 对于柱状图/折线图/组合图：使用X轴字段和双击点的X值作为筛选条件
- 对于饼图：使用分组字段或X轴字段和双击点的标签值作为筛选条件

## 🔧 技术实现

### 1. **数据缓存机制**

在渲染图表时，系统会自动缓存每个图表的原始数据：

```python
# 缓存原始数据用于下钻（在应用筛选前的数据）
if not data_cache:
    data_cache = {}
try:
    # 将DataFrame转换为JSON可序列化的格式
    data_cache[chart_id] = df_raw.to_dict('records')
except:
    pass
```

- **存储位置**：`chart-data-cache` Store组件
- **数据格式**：DataFrame转换为字典列表（JSON可序列化）
- **数据范围**：最多1000条原始记录

### 2. **双击事件监听**

使用Plotly的`doubleClickData`事件监听图表双击：

```python
Input({"type": "dashboard-chart", "chart_id": ALL}, "doubleClickData")
```

### 3. **下钻处理流程**

1. **检测双击事件**：监听图表的`doubleClickData`事件
2. **解析双击数据**：从双击事件中提取数据点的信息（X值、Y值、标签等）
3. **获取图表配置**：根据图表ID获取图表配置，确定X轴字段、Y轴字段、分组字段等
4. **加载原始数据**：从数据缓存中获取原始数据，如果缓存中没有则重新加载
5. **构建筛选条件**：根据图表类型和双击的数据点，构建筛选条件
6. **应用筛选**：从原始数据中筛选出匹配的记录
7. **显示结果**：在模态框中以表格形式显示筛选后的详细数据

### 4. **筛选条件构建逻辑**

#### 柱状图/折线图/组合图
```python
if chart_type in ['bar', 'line', 'combo']:
    # 使用X轴字段和双击点的X值作为筛选条件
    if 'x' in point and point['x'] is not None:
        filter_value = point['x']
        if x_field and x_field in original_data.columns:
            filter_conditions[x_field] = filter_value
            drill_down_title = f"{x_field} = {filter_value} 的详细数据"
```

#### 饼图
```python
elif chart_type == 'pie':
    # 使用分组字段或X轴字段和双击点的标签值作为筛选条件
    if 'label' in point and point['label'] is not None:
        filter_value = point['label']
        filter_field = group_field or x_field
        if filter_field and filter_field in original_data.columns:
            filter_conditions[filter_field] = filter_value
            drill_down_title = f"{filter_field} = {filter_value} 的详细数据"
```

### 5. **数据筛选实现**

根据字段类型采用不同的筛选方式：

```python
# 应用筛选条件
for field, value in filter_conditions.items():
    try:
        if pd.api.types.is_numeric_dtype(filtered_data[field]):
            # 数值类型：精确匹配
            filtered_data = filtered_data[filtered_data[field] == value]
        else:
            # 字符串类型：字符串匹配
            filtered_data = filtered_data[filtered_data[field].astype(str) == str(value)]
    except:
        pass
```

### 6. **UI组件**

#### 模态框结构
- **标题**：显示"数据下钻详情"和返回按钮
- **内容区**：显示数据表格
  - 标题：显示筛选条件（如"日期 = 2024-01-01 的详细数据"）
  - 记录数：显示匹配的记录总数
  - 数据表格：最多显示100条记录
- **底部按钮**：关闭按钮

## 📊 使用示例

### 示例1：柱状图下钻

假设有一个销售数据的柱状图：
- **X轴**：日期（date）
- **Y轴**：销售额（sales）

用户双击某个日期的柱子（例如"2024-01-01"），系统会：
1. 显示标题："date = 2024-01-01 的详细数据"
2. 显示所有日期为"2024-01-01"的详细销售记录
3. 显示记录总数（例如"共找到 15 条记录"）

### 示例2：饼图下钻

假设有一个产品销售占比的饼图：
- **分组字段**：产品类别（category）

用户双击某个类别（例如"电子产品"），系统会：
1. 显示标题："category = 电子产品 的详细数据"
2. 显示所有类别为"电子产品"的详细记录
3. 显示记录总数

## ⚙️ 配置和限制

### 数据限制
- **原始数据缓存**：最多1000条记录
- **下钻结果显示**：最多显示100条记录（避免表格过大）

### 性能优化
- 数据缓存机制避免重复加载数据
- 只显示匹配的记录，减少数据传输
- 限制显示记录数，避免页面卡顿

### 错误处理
- 如果原始数据无法加载，显示警告消息
- 如果没有匹配的数据，显示提示信息
- 如果处理过程中出错，显示错误消息

## 🔍 代码位置

### 主要文件
- **`pages/dashboard_page.py`**：
  - 第369-400行：下钻模态框UI定义
  - 第607-614行：原始数据缓存逻辑
  - 第1473-1633行：下钻处理回调函数

### 关键组件
- **`drill-down-data` Store**：存储下钻数据状态
- **`chart-data-cache` Store**：缓存图表原始数据
- **`modal-drill-down` Modal**：下钻详情模态框
- **`drill-down-content` Div**：下钻内容显示区域

## 🎨 UI提示

在每个图表卡片下方，系统会显示提示信息：
```html
html.Small(
    "💡 提示：双击图表数据点可查看详细数据",
    className="text-muted d-block mt-2"
)
```

## 🔮 未来扩展

可以考虑的增强功能：
1. **多级下钻**：支持从汇总数据下钻到更详细的数据，可以再次下钻
2. **下钻图表**：在下钻结果中可以选择字段生成新的图表
3. **导出下钻数据**：可以将下钻结果导出为CSV或Excel文件
4. **自定义筛选**：允许用户自定义筛选条件，而不仅仅是基于双击的点
5. **数据统计**：在下钻结果中显示统计信息（平均值、总和等）

## 📝 总结

数据下钻功能实现了从汇总图表到详细数据的无缝探索，提供了直观的数据分析体验。通过双击图表数据点，用户可以快速查看相关的详细记录，无需手动筛选或查询数据。

