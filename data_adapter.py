"""
数据源适配器
统一的数据源接口，支持 CSV/Excel、数据库、API
"""

import pandas as pd
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from load_data import load_from_file, load_from_database, load_from_api, DBConfig
from logger import get_logger, log_performance

logger = get_logger('data_adapter')


class DataSourceAdapter:
    """统一数据源适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化适配器
        
        Args:
            config: 数据源配置字典
        """
        self.config = config
        self.type = config.get('type')  # 'file', 'database', 'api'
        self.name = config.get('name', 'Unnamed')
        self.id = config.get('id')
        self._cache = None  # 缓存数据
        self._schema = None  # 缓存字段信息
    
    def connect(self) -> bool:
        """建立连接并测试"""
        try:
            if self.type == 'file':
                file_path = self.config.get('file_path')
                if not os.path.exists(file_path):
                    return False
                # 测试读取前几行
                self._cache = load_from_file(file_path)
                return True
            
            elif self.type == 'database':
                db_config = DBConfig(
                    engine=self.config.get('engine', 'postgresql'),
                    host=self.config.get('host'),
                    port=self.config.get('port', 5432),
                    user=self.config.get('user'),
                    password=self.config.get('password'),
                    database=self.config.get('database')
                )
                # 测试连接
                from sqlalchemy import create_engine
                url = db_config.to_sqlalchemy_url()
                engine = create_engine(url)
                with engine.connect() as conn:
                    # 简单查询测试连接
                    pd.read_sql("SELECT 1", conn)
                return True
            
            elif self.type == 'api':
                url = self.config.get('url')
                # 简单测试请求
                response = load_from_api(
                    url,
                    method=self.config.get('method', 'GET'),
                    params=self.config.get('params'),
                    headers=self.config.get('headers')
                )
                return True
            
            return False
        except Exception as e:
            logger.error(f"数据源连接失败 [类型: {self.type}, 名称: {self.name}]: {e}", exc_info=True)
            return False
    
    @log_performance
    def fetch_data(self, limit: Optional[int] = None, filters: Optional[Dict] = None) -> pd.DataFrame:
        """获取数据
        
        Args:
            limit: 限制返回行数
            filters: 筛选条件（暂不支持）
        
        Returns:
            DataFrame
        """
        try:
            logger.debug(f"开始获取数据 [类型: {self.type}, 名称: {self.name}, 限制: {limit}]")
            if self.type == 'file':
                file_path = self.config.get('file_path')
                df = load_from_file(file_path)
            
            elif self.type == 'database':
                db_config = DBConfig(
                    engine=self.config.get('engine', 'postgresql'),
                    host=self.config.get('host'),
                    port=self.config.get('port', 5432),
                    user=self.config.get('user'),
                    password=self.config.get('password'),
                    database=self.config.get('database')
                )
                sql = self.config.get('sql', 'SELECT * FROM ' + self.config.get('table', 'LIMIT 100'))
                df = load_from_database(db_config, sql)
            
            elif self.type == 'api':
                df = load_from_api(
                    self.config.get('url'),
                    method=self.config.get('method', 'GET'),
                    params=self.config.get('params'),
                    headers=self.config.get('headers'),
                    json_body=self.config.get('json_body')
                )
            else:
                raise ValueError(f"不支持的数据源类型: {self.type}")
            
            # 应用限制
            if limit:
                df = df.head(limit)
            
            # 应用筛选（简单实现）
            if filters:
                for col, condition in filters.items():
                    if isinstance(condition, dict):
                        if 'min' in condition:
                            df = df[df[col] >= condition['min']]
                        if 'max' in condition:
                            df = df[df[col] <= condition['max']]
                        if 'values' in condition:
                            df = df[df[col].isin(condition['values'])]
            
            self._cache = df
            logger.info(f"数据获取成功 [类型: {self.type}, 名称: {self.name}, 行数: {len(df)}, 列数: {len(df.columns)}]")
            return df
        
        except Exception as e:
            logger.error(f"获取数据失败 [类型: {self.type}, 名称: {self.name}]: {e}", exc_info=True)
            return pd.DataFrame()
    
    @log_performance
    def get_schema(self) -> Dict[str, Any]:
        """获取字段信息（类型、统计信息等）"""
        logger.debug(f"获取数据源字段信息 [类型: {self.type}, 名称: {self.name}]")
        if self._schema is not None:
            logger.debug("使用缓存的字段信息")
            return self._schema
        
        # 获取数据（限制行数以加快速度）
        df = self.fetch_data(limit=1000)
        
        schema = {
            'columns': [],
            'row_count': len(df)
        }
        
        for col in df.columns:
            col_info = {
                'name': col,
                'dtype': str(df[col].dtype),
                'type': self._infer_field_type(df[col])
            }
            
            # 添加统计信息
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info['stats'] = {
                    'min': float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    'max': float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    'mean': float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                }
            else:
                col_info['stats'] = {
                    'unique_count': int(df[col].nunique())
                }
            
            schema['columns'].append(col_info)
        
        self._schema = schema
        return schema
    
    def _infer_field_type(self, series: pd.Series) -> str:
        """推断字段类型"""
        # 数值类型
        if pd.api.types.is_numeric_dtype(series):
            if pd.api.types.is_integer_dtype(series):
                return 'integer'
            else:
                return 'numeric'
        
        # 日期类型
        if pd.api.types.is_datetime64_any_dtype(series):
            return 'date'
        
        # 尝试转换为日期
        try:
            pd.to_datetime(series.dropna().head(5))
            return 'date'
        except:
            pass
        
        # 文本类型
        return 'text'
    
    def clear_cache(self):
        """清除缓存"""
        self._cache = None
        self._schema = None


class DataSourceManager:
    """数据源管理器（单例）"""
    
    _instance = None
    _adapters: Dict[str, DataSourceAdapter] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_adapter(self, datasource_id: str, config: Optional[Dict[str, Any]] = None) -> Optional[DataSourceAdapter]:
        """获取适配器实例"""
        if datasource_id in self._adapters:
            return self._adapters[datasource_id]
        
        if config:
            adapter = DataSourceAdapter(config)
            self._adapters[datasource_id] = adapter
            return adapter
        
        return None
    
    def clear_adapter(self, datasource_id: str):
        """清除适配器"""
        if datasource_id in self._adapters:
            del self._adapters[datasource_id]
    
    def clear_all(self):
        """清除所有适配器"""
        self._adapters.clear()

