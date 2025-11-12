"""
创建 Excel 示例文件
"""
import pandas as pd
import os

# 创建测试 Excel 数据
data = {
    '日期': pd.date_range('2024-01-01', periods=30, freq='D'),
    '产品': ['产品A', '产品B', '产品C'] * 10,
    '销售额': [15000, 22000, 18000, 16000, 24000, 19000, 17000, 25000, 20000, 18000,
              21000, 26000, 22000, 19000, 27000, 23000, 20000, 28000, 24000, 21000,
              25000, 29000, 26000, 22000, 30000, 27000, 23000, 31000, 28000, 24000],
    '销量': [150, 220, 180, 160, 240, 190, 170, 250, 200, 180,
            210, 260, 220, 190, 270, 230, 200, 280, 240, 210,
            250, 290, 260, 220, 300, 270, 230, 310, 280, 240],
    '地区': ['华东', '华南', '华北'] * 10,
}

df = pd.DataFrame(data)

# 确保 data 目录存在
os.makedirs('data', exist_ok=True)

# 保存为 Excel 文件
excel_path = 'data/sample_sales.xlsx'
df.to_excel(excel_path, index=False, sheet_name='销售数据')

print(f"Excel 示例文件已创建: {excel_path}")
print(f"数据行数: {len(df)}")
print(f"列名: {list(df.columns)}")
print("\n数据预览:")
print(df.head())
