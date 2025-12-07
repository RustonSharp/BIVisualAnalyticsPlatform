"""
数据源适配器
统一的数据源接口，支持 CSV/Excel、数据库、API
"""

import pandas as pd
import os
import json
import warnings
from typing import Dict, Any, Optional, List, cast
from pathlib import Path
from tools import load_from_file, load_from_database, load_from_api, DBConfig
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
                if not file_path or not isinstance(file_path, str):
                    return False
                file_path_str = cast(str, file_path)
                if not os.path.exists(file_path_str):
                    return False
                # 测试读取前几行
                self._cache = load_from_file(file_path_str)
                return True
            
            elif self.type == 'database':
                host = self.config.get('host')
                user = self.config.get('user')
                password = self.config.get('password')
                database = self.config.get('database')
                
                if not all([host, user, password, database]):
                    return False
                
                if not all(isinstance(x, str) for x in [host, user, password, database]):
                    return False
                
                db_config = DBConfig(
                    engine=self.config.get('engine', 'postgresql'),
                    host=cast(str, host),
                    port=self.config.get('port', 5432),
                    user=cast(str, user),
                    password=cast(str, password),
                    database=cast(str, database)
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
                if not url or not isinstance(url, str):
                    return False
                # 简单测试请求
                load_from_api(
                    cast(str, url),
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
            df: pd.DataFrame
            
            if self.type == 'file':
                file_path = self.config.get('file_path')
                if not file_path or not isinstance(file_path, str):
                    raise ValueError("文件路径无效或未配置")
                df = load_from_file(cast(str, file_path))
            
            elif self.type == 'database':
                host = self.config.get('host')
                user = self.config.get('user')
                password = self.config.get('password')
                database = self.config.get('database')
                
                if not all([host, user, password, database]):
                    raise ValueError("数据库配置不完整")
                
                if not all(isinstance(x, str) for x in [host, user, password, database]):
                    raise ValueError("数据库配置参数类型错误")
                
                db_config = DBConfig(
                    engine=self.config.get('engine', 'postgresql'),
                    host=cast(str, host),
                    port=self.config.get('port', 5432),
                    user=cast(str, user),
                    password=cast(str, password),
                    database=cast(str, database)
                )
                sql = self.config.get('sql', 'SELECT * FROM ' + str(self.config.get('table', 'LIMIT 100')))
                df = load_from_database(db_config, sql)
            
            elif self.type == 'api':
                url = self.config.get('url')
                if not url or not isinstance(url, str):
                    raise ValueError("API URL 无效或未配置")
                df = load_from_api(
                    cast(str, url),
                    method=self.config.get('method', 'GET'),
                    params=self.config.get('params'),
                    headers=self.config.get('headers'),
                    json_body=self.config.get('json_body')
                )
            else:
                raise ValueError(f"不支持的数据源类型: {self.type}")
            
            # 确保 df 是 DataFrame 类型
            df = cast(pd.DataFrame, df)
            
            # 应用限制
            if limit:
                df = df.head(limit)
            
            # 应用筛选（简单实现）
            if filters:
                for col, condition in filters.items():
                    if isinstance(condition, dict):
                        if 'min' in condition:
                            df = cast(pd.DataFrame, df[df[col] >= condition['min']])
                        if 'max' in condition:
                            df = cast(pd.DataFrame, df[df[col] <= condition['max']])
                        if 'values' in condition:
                            df = cast(pd.DataFrame, df[df[col].isin(condition['values'])])
            
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
            col_series = cast(pd.Series, df[col])
            col_info = {
                'name': col,
                'dtype': str(col_series.dtype),
                'type': self._infer_field_type(col_series)
            }
            
            # 添加统计信息
            if pd.api.types.is_numeric_dtype(col_series):
                min_val = col_series.min()
                max_val = col_series.max()
                mean_val = col_series.mean()
                # pd.isna 对于标量返回 bool，对于数组返回数组
                # 这里我们处理的是标量值（min/max/mean 的结果）
                min_is_na = bool(pd.isna(min_val))  # type: ignore
                max_is_na = bool(pd.isna(max_val))  # type: ignore
                mean_is_na = bool(pd.isna(mean_val))  # type: ignore
                
                col_info['stats'] = {
                    'min': None if min_is_na else float(min_val),
                    'max': None if max_is_na else float(max_val),
                    'mean': None if mean_is_na else float(mean_val),
                }
            else:
                col_info['stats'] = {
                    'unique_count': int(col_series.nunique())
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
        
        # 尝试转换为日期（使用常见格式）
        sample_data = series.dropna().head(10)
        if len(sample_data) == 0:
            return 'text'
        
        # 常见日期格式列表（按常见程度排序）
        common_date_formats = [
            # ISO 格式（最常见）
            '%Y-%m-%d',           # 2024-01-01
            '%Y/%m/%d',           # 2024/01/01
            '%Y-%m-%d %H:%M:%S',  # 2024-01-01 12:00:00
            '%Y/%m/%d %H:%M:%S',  # 2024/01/01 12:00:00
            '%Y-%m-%dT%H:%M:%S',  # 2024-01-01T12:00:00 (ISO 8601)
            '%Y-%m-%dT%H:%M:%S.%f', # 2024-01-01T12:00:00.000000 (ISO 8601 with microseconds)
            '%Y-%m-%dT%H:%M:%SZ',   # 2024-01-01T12:00:00Z (UTC)
            
            # 欧式格式（日-月-年）
            '%d-%m-%Y',           # 01-01-2024
            '%d/%m/%Y',           # 01/01/2024
            '%d.%m.%Y',           # 01.01.2024
            '%d-%m-%Y %H:%M:%S',  # 01-01-2024 12:00:00
            '%d/%m/%Y %H:%M:%S',  # 01/01/2024 12:00:00
            
            # 美式格式（月-日-年）
            '%m-%d-%Y',           # 01-01-2024
            '%m/%d/%Y',           # 01/01/2024
            '%m.%d.%Y',           # 01.01.2024
            '%m-%d-%Y %H:%M:%S',  # 01-01-2024 12:00:00
            '%m/%d/%Y %H:%M:%S',  # 01/01/2024 12:00:00
            
            # 中文格式
            '%Y年%m月%d日',        # 2024年01月01日
            '%Y年%m月%d日 %H:%M:%S', # 2024年01月01日 12:00:00
            
            # 点分隔格式
            '%Y.%m.%d',           # 2024.01.01
            '%Y.%m.%d %H:%M:%S',  # 2024.01.01 12:00:00
            
            # 无分隔符格式
            '%Y%m%d',             # 20240101
            '%Y%m%d%H%M%S',       # 20240101120000
            
            # 英文月份格式
            '%d %B %Y',           # 01 January 2024
            '%B %d, %Y',          # January 01, 2024
            '%d %b %Y',           # 01 Jan 2024
            '%b %d, %Y',          # Jan 01, 2024
            '%d %B %Y %H:%M:%S',  # 01 January 2024 12:00:00
            '%B %d, %Y %H:%M:%S', # January 01, 2024 12:00:00
            
            # 其他常见格式
            '%Y-%m-%d %H:%M',     # 2024-01-01 12:00
            '%Y/%m/%d %H:%M',     # 2024/01/01 12:00
            '%d-%m-%Y %H:%M',     # 01-01-2024 12:00
            '%m-%d-%Y %H:%M',     # 01-01-2024 12:00
        ]
        
        # 先尝试使用 format 参数（避免警告）
        for date_format in common_date_formats:
            try:
                # 检查是否大部分值都能成功解析
                parsed = pd.to_datetime(sample_data, format=date_format, errors='coerce')
                if parsed.notna().sum() >= len(sample_data) * 0.8:  # 至少80%能解析
                    return 'date'
            except (ValueError, TypeError):
                continue
        
        # 如果指定格式都失败，尝试自动推断（使用 errors='coerce' 避免警告）
        # 注意：不指定 format 参数时，pandas 会自动推断，但可能产生警告
        # 使用 errors='coerce' 可以避免抛出异常，无法解析的值会变成 NaT
        # 使用 warnings.filterwarnings 来抑制日期格式推断的警告
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='Could not infer format')
                parsed = pd.to_datetime(sample_data, errors='coerce')
                if parsed.notna().sum() >= len(sample_data) * 0.8:  # 至少80%能解析
                    return 'date'
        except (ValueError, TypeError):
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

