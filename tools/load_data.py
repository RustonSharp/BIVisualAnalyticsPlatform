"""数据加载工具模块，支持三种数据源类型：

1. 本地文件上传（CSV / Excel）
2. 数据库连接（PostgreSQL / MySQL）
3. HTTP API 接口（JSON）

本模块专注于数据加载逻辑。您可以
将这些函数与 Streamlit、Dash 或其他
UI 框架集成，以提供真实的上传表单/输入框。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd
import requests
from logger import get_logger, log_performance

logger = get_logger('load_data')


# --------------------------------------------
# 1. Local file loader (CSV / Excel)
# --------------------------------------------


@log_performance
def load_from_file(file_path: str, file_type: Optional[str] = None) -> pd.DataFrame:
	"""Load data from a local CSV or Excel file.

	Parameters
	----------
	file_path:
		Local path of the uploaded file.
	file_type:
		Optional hint: "csv", "xlsx", or "excel". If omitted,
		the type will be inferred from file extension.
	"""
	logger.debug(f"加载文件 [路径: {file_path}, 类型: {file_type}]")

	if file_type is None:
		lower = file_path.lower()
		if lower.endswith(".csv"):
			file_type = "csv"
		elif lower.endswith(".xls") or lower.endswith(".xlsx"):
			file_type = "excel"
		else:
			error_msg = "Cannot infer file type, please specify 'csv' or 'excel'."
			logger.error(f"无法推断文件类型: {file_path}")
			raise ValueError(error_msg)

	try:
		if file_type == "csv":
			df = pd.read_csv(file_path)
		elif file_type in {"xlsx", "xls", "excel"}:
			df = pd.read_excel(file_path)
		else:
			raise ValueError(f"Unsupported file_type: {file_type}")
		
		logger.info(f"文件加载成功 [路径: {file_path}, 类型: {file_type}, 行数: {len(df)}, 列数: {len(df.columns)}]")
		return df
	except Exception as e:
		logger.error(f"文件加载失败 [路径: {file_path}, 类型: {file_type}]: {e}", exc_info=True)
		raise


# --------------------------------------------
# 2. Database loader (PostgreSQL / MySQL)
# --------------------------------------------


@dataclass
class DBConfig:
	"""Simple database config for PostgreSQL / MySQL."""

	engine: str  # "postgresql" or "mysql"
	host: str
	port: int
	user: str
	password: str
	database: str

	def to_sqlalchemy_url(self) -> str:
		"""Build an SQLAlchemy-style URL string.

		Examples
		--------
		postgresql://user:pwd@host:5432/dbname
		mysql+pymysql://user:pwd@host:3306/dbname
		"""

		if self.engine == "postgresql":
			driver = "postgresql+psycopg2"
		elif self.engine == "mysql":
			driver = "mysql+pymysql"
		else:
			raise ValueError("engine must be 'postgresql' or 'mysql'")

		return f"{driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


def load_from_database(config: DBConfig, sql: str) -> pd.DataFrame:
	"""Load data from PostgreSQL / MySQL using pandas.read_sql.

	Notes
	-----
	Requires external packages depending on engine:
	- PostgreSQL: psycopg2-binary
	- MySQL: pymysql
	"""

	from sqlalchemy import create_engine  # imported lazily

	logger.debug(f"从数据库加载数据 [引擎: {config.engine}, 数据库: {config.database}, SQL: {sql[:50]}...]")
	try:
		url = config.to_sqlalchemy_url()
		engine = create_engine(url)
		with engine.connect() as conn:
			df = pd.read_sql(sql, conn)
		logger.info(f"数据库数据加载成功 [引擎: {config.engine}, 数据库: {config.database}, 行数: {len(df)}, 列数: {len(df.columns)}]")
		return df
	except Exception as e:
		logger.error(f"数据库数据加载失败 [引擎: {config.engine}, 数据库: {config.database}]: {e}", exc_info=True)
		raise


# --------------------------------------------
# 3. HTTP API loader
# --------------------------------------------


@log_performance
def load_from_api(
	url: str,
	method: str = "GET",
	params: Optional[Dict[str, Any]] = None,
	headers: Optional[Dict[str, str]] = None,
	json_body: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
	"""Load data from an HTTP API that returns JSON.

	This function assumes the API returns either:
	- a list of objects (each object -> one row), or
	- a dict containing a top-level list under a key like
	  "data" or "results" (simple heuristics).
	"""
	logger.debug(f"从API加载数据 [URL: {url}, 方法: {method}]")
	try:
		method = method.upper()
		if method == "GET":
			resp = requests.get(url, params=params, headers=headers, timeout=30)
		elif method == "POST":
			resp = requests.post(url, params=params, headers=headers, json=json_body, timeout=30)
		else:
			raise ValueError("Only GET and POST are supported for now.")

		resp.raise_for_status()
		data = resp.json()

		# If it's already a list, treat it directly as rows
		if isinstance(data, list):
			df = pd.DataFrame(data)
			logger.info(f"API数据加载成功 [URL: {url}, 行数: {len(df)}, 列数: {len(df.columns)}]")
			return df

		# If it's a dict, try to find list-like value under common keys
		if isinstance(data, dict):
			for key in ("data", "results", "items", "rows"):
				value = data.get(key)
				if isinstance(value, list):
					df = pd.DataFrame(value)
					logger.info(f"API数据加载成功 [URL: {url}, 行数: {len(df)}, 列数: {len(df.columns)}]")
					return df

		# Fallback: let pandas try to normalize
		df = pd.json_normalize(data)
		logger.info(f"API数据加载成功 [URL: {url}, 行数: {len(df)}, 列数: {len(df.columns)}]")
		return df
	except Exception as e:
		logger.error(f"API数据加载失败 [URL: {url}, 方法: {method}]: {e}", exc_info=True)
		raise


__all__ = [
	"load_from_file",
	"DBConfig",
	"load_from_database",
	"load_from_api",
]


if __name__ == "__main__":
	# Very small manual test examples. Replace paths / URLs
	# with your own when actually running.

	# 1) Local file example (CSV)
	df_file = load_from_file("./sample_data.csv")
	print(df_file.head())

	# 2) Database example
	# db_cfg = DBConfig(
	#     engine="postgresql",
	#     host="localhost",
	#     port=5432,
	#     user="user",
	#     password="password",
	#     database="mydb",
	# )
	# df_db = load_from_database(db_cfg, "SELECT * FROM your_table LIMIT 10")
	# print(df_db.head())

	# 3) API example
	# df_api = load_from_api("https://api.example.com/data")
	# print(df_api.head())

