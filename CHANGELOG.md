# 更新日志 (CHANGELOG)

## [未发布] - 2024-11-12

### ✨ 新增功能

#### 文件上传功能
- **CSV/Excel 文件上传**: 在数据源配置界面添加了文件上传按钮
  - 点击按钮可选择本地 CSV 或 Excel 文件
  - 支持 `.csv`, `.xls`, `.xlsx` 格式
  - 自动上传文件到 `uploads/` 目录
  - 上传成功后自动填充文件路径
  - 显示上传状态提示（成功/失败/不支持的格式）

- **双重文件选择方式**:
  - 方式一: 点击上传按钮选择文件（推荐）
  - 方式二: 手动输入文件路径

- **文件类型识别**:
  - 根据文件扩展名自动识别文件类型
  - Excel 文件自动读取第一个工作表
  - CSV 文件支持自定义编码和分隔符

### 📝 文档更新

- 新增 `docs/FILE_UPLOAD_GUIDE.md` - 文件上传功能详细使用指南
- 更新 `README.md` - 添加 Web 界面操作说明
- 新增 `create_sample_excel.py` - Excel 示例数据生成脚本

### 🔧 技术改进

- **依赖库**:
  - 已包含 `openpyxl>=3.1.0` 用于 Excel 读取
  - 已包含 `xlrd>=2.0.0` 用于旧版 Excel 支持

- **代码改进**:
  - `app.py`: 新增 `base64` 和 `io` 导入支持文件上传
  - `app.py`: 新增 `handle_file_upload` 回调函数处理文件上传
  - `datasource_ui.py`: CSV 配置表单添加 `dcc.Upload` 组件
  - `.gitignore`: 添加 `uploads/` 目录排除

### 🎨 UI 改进

- CSV/Excel 数据源配置界面重新设计
- 添加上传按钮图标（Font Awesome 图标）
- 上传状态使用彩色 Alert 组件显示
- 保留原有手动输入路径功能作为备选

### 📦 文件结构变化

```
新增:
  uploads/                      # 用户上传文件目录（不提交到版本控制）
  create_sample_excel.py        # Excel 示例数据生成脚本
  docs/FILE_UPLOAD_GUIDE.md     # 文件上传功能使用指南
  
修改:
  app.py                        # 添加文件上传处理逻辑
  bi_visual_analytics/components/datasource_ui.py  # 添加上传按钮
  .gitignore                    # 忽略 uploads/ 目录
  README.md                     # 更新功能说明
```

### 🐛 Bug 修复

- 无

### ⚠️ 已知问题

- Excel 文件当前仅支持读取第一个工作表
- 大文件上传（>100MB）可能较慢
- 上传文件不会自动清理，需手动管理 `uploads/` 目录

### 📋 待办事项

- [ ] 添加文件大小限制提示
- [ ] 支持 Excel 多工作表选择
- [ ] 添加文件预览功能
- [ ] 实现上传文件列表管理
- [ ] 添加文件自动清理机制
- [ ] 支持拖拽上传文件

---

## [1.0.0] - 初始版本

### 功能特性

- ✅ 多数据源适配器（CSV、Database、API）
- ✅ 7 种图表类型
- ✅ 拖拽式图表设计器
- ✅ 交互式仪表盘
- ✅ 数据筛选和聚合
- ✅ 多格式导出（PNG/PDF/HTML/CSV）
- ✅ 配置管理（YAML/JSON）
- ✅ 日志系统
- ✅ 完整文档

### 技术栈

- Python 3.8+
- Plotly Dash 2.14+
- pandas 2.0+
- SQLAlchemy 2.0+
- Bootstrap UI

---

## 版本说明

版本号格式: `主版本.次版本.修订号`

- **主版本**: 不兼容的 API 变更
- **次版本**: 向后兼容的功能新增
- **修订号**: 向后兼容的问题修正

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request
