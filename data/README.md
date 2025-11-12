# 数据目录说明

此目录用于存放数据文件。

## 📁 目录用途

- 存放 CSV 文件
- 存放 Excel 文件
- 存放其他数据源文件

## 📝 使用说明

### 生成示例数据

运行以下脚本生成示例数据文件：

```bash
# 生成 CSV 示例文件
python examples/basic_usage.py

# 生成 Excel 示例文件
python create_sample_excel.py
```

### 文件命名建议

- 使用有意义的英文名称
- 避免中文和特殊字符
- 例如: `sales_2024.csv`, `product_data.xlsx`

## ⚠️ 注意事项

- `data/` 目录中的所有数据文件已被 `.gitignore` 忽略
- 不会提交到版本控制系统
- 仅 `.gitkeep` 和 `README.md` 会被保留
- 建议将敏感数据文件存放在此目录

## 🔗 相关文档

- [文件上传指南](../docs/FILE_UPLOAD_GUIDE.md)
- [用户指南](../docs/USER_GUIDE.md)
- [快速开始](../QUICKSTART.md)
