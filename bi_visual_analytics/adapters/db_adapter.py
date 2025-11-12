"""
数据库适配器
支持 PostgreSQL、MySQL 等关系型数据库
"""

from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from bi_visual_analytics.adapters.base import DataSourceAdapter


class DatabaseAdapter(DataSourceAdapter):
    """关系型数据库适配器"""

    def __init__(self):
        super().__init__()
        self.engine = None
        self.table_name = None

    def connect(self, config: Dict[str, Any]) -> bool:
        """
        连接到数据库

        Args:
            config: 配置字典，包含：
                - db_type: 数据库类型 (postgresql/mysql)
                - host: 主机地址
                - port: 端口
                - database: 数据库名
                - username: 用户名
                - password: 密码
                - table: 表名（可选）

        Returns:
            bool: 连接是否成功
        """
        try:
            db_type = config.get("db_type", "postgresql")
            host = config.get("host", "localhost")
            port = config.get("port")
            database = config.get("database")
            username = config.get("username")
            password = config.get("password")
            self.table_name = config.get("table")

            # 设置默认端口
            if not port:
                port = 5432 if db_type == "postgresql" else 3306

            # 构建连接字符串
            if db_type == "postgresql":
                conn_str = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            elif db_type == "mysql":
                conn_str = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
            else:
                raise ValueError(f"不支持的数据库类型: {db_type}")

            # 创建引擎
            self.engine = create_engine(conn_str, pool_pre_ping=True)

            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            self.config = config
            self.connected = True

            # 如果指定了表名，获取表结构
            if self.table_name:
                self._load_table_schema()

            return True

        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            self.connected = False
            return False

    def fetch_data(self, query: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        获取数据

        Args:
            query: 查询条件，支持：
                - sql: 自定义 SQL 查询
                - table: 表名
                - columns: 列名列表
                - limit: 行数限制
                - where: WHERE 条件

        Returns:
            pd.DataFrame: 查询结果
        """
        if not self.connected or self.engine is None:
            raise RuntimeError("未连接到数据库")

        try:
            # 如果提供了自定义 SQL
            if query and "sql" in query:
                return pd.read_sql(query["sql"], self.engine)

            # 构建查询
            table = query.get("table", self.table_name) if query else self.table_name
            if not table:
                raise ValueError("未指定表名")

            columns = "*"
            if query and "columns" in query:
                columns = ", ".join(query["columns"])

            sql = f"SELECT {columns} FROM {table}"

            # 添加 WHERE 条件
            if query and "where" in query:
                sql += f" WHERE {query['where']}"

            # 添加 LIMIT
            if query and "limit" in query:
                sql += f" LIMIT {query['limit']}"

            return pd.read_sql(sql, self.engine)

        except Exception as e:
            raise RuntimeError(f"查询失败: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """
        获取表结构信息

        Returns:
            dict: 表结构信息
        """
        if not self.connected:
            raise RuntimeError("未连接到数据库")

        return self.schema

    def get_tables(self) -> list:
        """
        获取数据库中所有表名

        Returns:
            list: 表名列表
        """
        if not self.connected or self.engine is None:
            raise RuntimeError("未连接到数据库")

        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def _load_table_schema(self):
        """加载表结构信息"""
        if not self.table_name or self.engine is None:
            return

        # 查询少量数据以推断类型
        df = pd.read_sql(f"SELECT * FROM {self.table_name} LIMIT 100", self.engine)

        self.schema = {
            "table": self.table_name,
            "columns": list(df.columns),
            "types": self._infer_column_types(df),
        }

    def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            self.engine.dispose()
        super().disconnect()
