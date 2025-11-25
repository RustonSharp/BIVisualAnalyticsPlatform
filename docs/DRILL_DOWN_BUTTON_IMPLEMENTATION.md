# "查看详情"按钮实现说明

## 📋 功能概述

为了改善用户体验，避免数据筛选和数据下钻功能的混淆，我们在每个图表卡片上添加了"查看详情"按钮。用户可以通过以下两种方式查看详细数据：

1. **双击图表数据点**（原有方式）
2. **单击数据点后，点击"查看详情"按钮**（新增方式）

## 🎯 实现方案

### 1. UI组件

在每个图表卡片的头部添加"查看详情"按钮：

```python
dbc.Button(
    [html.I(className="fas fa-search me-1"), "查看详情"],
    id={"type": "btn-drill-down-chart", "chart_id": chart_id},
    color="info",
    size="sm",
    outline=True,
    className="me-2",
)
```

### 2. 数据存储

添加 `chart-last-click-data` Store 来存储每个图表最后点击的数据点：

```python
dcc.Store(id="chart-last-click-data", data={})  # {chart_id: click_data}
```

### 3. 点击数据记录

在 `handle_chart_click` 回调中，每次用户点击图表数据点时，记录点击数据：

```python
# 更新最后点击数据（用于下钻）
if not last_click_data:
    last_click_data = {}
last_click_data = last_click_data.copy()
last_click_data[source_chart_id] = click_data
```

### 4. 下钻处理

更新 `handle_drill_down` 回调，支持两种触发方式：

1. **双击事件**：直接使用双击数据
2. **按钮点击**：使用存储的最后点击数据

如果用户没有先点击数据点就点击按钮，会显示提示："请先点击图表上的数据点，然后再点击查看详情按钮"

## 🔄 工作流程

### 方式1：双击查看（原有方式）
```
用户双击图表数据点
  ↓
触发 doubleClickData 事件
  ↓
handle_drill_down 回调处理
  ↓
显示详细数据模态框
```

### 方式2：按钮查看（新增方式）
```
用户单击图表数据点
  ↓
handle_chart_click 回调记录点击数据
  ↓
用户点击"查看详情"按钮
  ↓
handle_drill_down 回调读取最后点击数据
  ↓
显示详细数据模态框
```

## ✅ 优势

1. **操作更明确**：用户可以通过明确的按钮操作，而不是记住双击
2. **减少混淆**：区分了单击（筛选）和按钮点击（下钻）
3. **更好的用户体验**：符合常见UI模式（点击选择，然后按钮操作）
4. **向后兼容**：保留双击功能，不影响现有用户

## 📝 使用说明

用户有两种方式查看详细数据：

1. **快速方式**：直接双击图表上的数据点
2. **明确方式**：
   - 先单击图表上的数据点（这会触发筛选，并记录点击数据）
   - 然后点击图表卡片上的"查看详情"按钮

## 🔧 技术细节

### Store 数据结构

```python
chart-last-click-data: {
    "chart_id_1": {
        "points": [...],
        "xaxis": {...},
        "yaxis": {...}
    },
    "chart_id_2": {...}
}
```

### 回调触发顺序

1. 用户单击数据点 → `handle_chart_click` 触发
2. 更新 `chart-filter-state`（筛选）
3. 更新 `chart-last-click-data`（记录点击）
4. 用户点击按钮 → `handle_drill_down` 触发
5. 从 `chart-last-click-data` 读取点击数据
6. 处理并显示详细数据

