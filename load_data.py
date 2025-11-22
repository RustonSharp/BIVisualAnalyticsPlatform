"""Data loading utilities for three types of sources:

1. Local file upload (CSV / Excel)
2. Database connection (PostgreSQL / MySQL)
3. HTTP API endpoint (JSON)

This module only focuses on data loading logic. You can
integrate these functions with Streamlit, Dash, or other
UI frameworks to provide real upload forms / input boxes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd
import requests


# --------------------------------------------
# 1. Local file loader (CSV / Excel)
# --------------------------------------------


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

	if file_type is None:
		lower = file_path.lower()
		if lower.endswith(".csv"):
			file_type = "csv"
		elif lower.endswith(".xls") or lower.endswith(".xlsx"):
			file_type = "excel"
		else:
			raise ValueError("Cannot infer file type, please specify 'csv' or 'excel'.")

	if file_type == "csv":
		return pd.read_csv(file_path)
	if file_type in {"xlsx", "xls", "excel"}:
		return pd.read_excel(file_path)

	raise ValueError(f"Unsupported file_type: {file_type}")


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

	url = config.to_sqlalchemy_url()
	engine = create_engine(url)
	with engine.connect() as conn:
		df = pd.read_sql(sql, conn)
	return df


# --------------------------------------------
# 3. HTTP API loader
# --------------------------------------------


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
		return pd.DataFrame(data)

	# If it's a dict, try to find list-like value under common keys
	if isinstance(data, dict):
		for key in ("data", "results", "items", "rows"):
			value = data.get(key)
			if isinstance(value, list):
				return pd.DataFrame(value)

	# Fallback: let pandas try to normalize
	return pd.json_normalize(data)


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


