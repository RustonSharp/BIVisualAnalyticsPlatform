# 快速启动指南

## 🚀 3 分钟启动 BI 平台

### 步骤 1: 安装依赖

打开终端（PowerShell 或 CMD），进入项目目录：

```powershell
cd d:\Code\BIVisualAnalyticsPlatform
pip install -r requirements.txt
```

### 步骤 2: 运行示例脚本（可选）

验证安装是否成功：

```powershell
python examples\basic_usage.py
```

这将：
- ✅ 加载示例数据
- ✅ 生成 3 个图表（折线图、柱状图、饼图）
- ✅ 导出为 PNG 和 HTML 文件到 `exports/` 目录

### 步骤 3: 启动 Web 应用

```powershell
python app.py
```

看到以下信息表示启动成功：

```
Dash is running on http://0.0.0.0:8050/

 * Serving Flask app 'app'
 * Debug mode: on
```

### 步骤 4: 访问应用

在浏览器中打开：**http://localhost:8050**

---

## 📊 第一个图表

### 使用 Web 界面（推荐初学者）

1. 点击 **"数据源"** → 选择 "CSV / Excel 文件"
2. 文件路径填写：`data/sample_sales.csv`
3. 点击 **"测试连接"** → **"保存配置"**
4. 进入 **"图表设计"** → 选择 "折线图"
   - X 轴：date
   - Y 轴：sales
   - 聚合函数：求和
5. 点击 **"生成图表"** 查看预览

### 使用 Python 代码

创建文件 `my_first_chart.py`：

```python
from bi_visual_analytics.adapters import CSVAdapter
from bi_visual_analytics.charts import ChartEngine

# 1. 加载数据
adapter = CSVAdapter()
adapter.connect({"file_path": "data/sample_sales.csv"})
data = adapter.fetch_data()

# 2. 生成图表
engine = ChartEngine()
fig = engine.create_chart(
    data=data,
    config={
        "type": "line",
        "x": "date",
        "y": "sales",
        "agg_func": "sum",
        "title": "每日销售趋势"
    }
)

# 3. 显示图表
fig.show()
```

运行：
```powershell
python my_first_chart.py
```

---

## 🧪 运行测试

验证核心功能：

```powershell
python tests\test_basic.py
```

---

## 📁 项目文件说明

```
BIVisualAnalyticsPlatform/
├── app.py                    # 主应用（运行此文件启动 Web 应用）
├── bi_visual_analytics/      # 核心库
├── data/
│   └── sample_sales.csv      # 示例数据（50 行销售记录）
├── config/                   # 配置模板
├── docs/                     # 文档
│   ├── API.md               # API 参考文档
│   └── USER_GUIDE.md        # 用户手册
├── examples/
│   └── basic_usage.py       # 示例代码
└── tests/
    └── test_basic.py        # 单元测试
```

---

## 💡 常见操作

### 修改端口

编辑 `app.py` 最后一行：

```python
app.run_server(debug=True, host="0.0.0.0", port=8888)  # 改为 8888
```

### 使用自己的数据

将 CSV 文件放到 `data/` 目录，在 Web 界面中配置路径即可。

### 导出图表

在 "导出" 菜单中选择格式（PNG/PDF/HTML），输入文件名即可。

---

## 🆘 遇到问题？

### 问题 1: `ImportError: No module named 'dash'`

**解决**: 重新安装依赖

```powershell
pip install -r requirements.txt
```

### 问题 2: 端口被占用

**解决**: 修改端口或关闭占用 8050 端口的程序

查看占用：
```powershell
netstat -ano | findstr :8050
```

### 问题 3: 浏览器打不开

**解决**: 
1. 检查防火墙是否阻止
2. 尝试使用 `http://127.0.0.1:8050` 而不是 localhost

---

## 📚 下一步

- 📖 阅读 [用户手册](docs/USER_GUIDE.md) 了解高级功能
- 🔧 查看 [API 文档](docs/API.md) 学习编程接口
- 💻 运行 `examples/basic_usage.py` 查看更多示例

---

**祝使用愉快！有问题随时查看文档或提交 Issue。**
