"""
统一日志管理模块
提供统一的日志记录接口，便于问题追踪和性能分析
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, cast


class LoggerManager:
    """日志管理器"""
    
    _instance: Optional['LoggerManager'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器"""
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """配置日志系统"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 创建主日志记录器
        logger = logging.getLogger("BIVisualAnalyticsPlatform")
        logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if logger.handlers:
            self._logger = logger
            return
        
        # 日志格式
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. 控制台处理器 - 输出INFO及以上级别
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        
        # 2. 文件处理器 - 所有级别，按日期轮转
        log_file = log_dir / "app.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',
            interval=1,
            backupCount=30,  # 保留30天的日志
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # 3. 错误日志文件 - 只记录ERROR及以上级别
        error_log_file = log_dir / "error.log"
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(error_log_file),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
        # 4. 性能日志文件 - 记录性能相关信息
        performance_log_file = log_dir / "performance.log"
        performance_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(performance_log_file),
            when='midnight',
            interval=1,
            backupCount=7,  # 性能日志保留7天
            encoding='utf-8'
        )
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(detailed_formatter)
        # 创建性能日志记录器
        performance_logger = logging.getLogger("BIVisualAnalyticsPlatform.performance")
        performance_logger.addHandler(performance_handler)
        performance_logger.setLevel(logging.INFO)
        performance_logger.propagate = False  # 不传播到主日志记录器
        
        self._logger = logger
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称，如果为None则返回主日志记录器
        
        Returns:
            logging.Logger实例
        """
        if name:
            return logging.getLogger(f"BIVisualAnalyticsPlatform.{name}")
        if self._logger is None:
            # 如果logger未初始化，初始化它
            self._setup_logger()
        # 此时 self._logger 一定不是 None，使用 cast 告知类型检查器
        return cast(logging.Logger, self._logger)
    
    def set_level(self, level: int):
        """
        设置日志级别
        
        Args:
            level: 日志级别 (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)
        """
        if self._logger is None:
            self._setup_logger()
        # 此时 self._logger 一定不是 None，使用 cast 告知类型检查器
        logger = cast(logging.Logger, self._logger)
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)


# 创建全局日志管理器实例
_logger_manager = LoggerManager()

# 便捷函数
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，例如 'dashboard', 'chart_engine' 等
    
    Returns:
        logging.Logger实例
    
    Examples:
        >>> logger = get_logger('dashboard')
        >>> logger.info('Dashboard loaded')
        >>> logger.error('Failed to load chart', exc_info=True)
    """
    return _logger_manager.get_logger(name)


def get_performance_logger() -> logging.Logger:
    """
    获取性能日志记录器
    
    Returns:
        性能日志记录器实例
    
    Examples:
        >>> perf_logger = get_performance_logger()
        >>> perf_logger.info('Chart generation took 0.5s')
    """
    return logging.getLogger("BIVisualAnalyticsPlatform.performance")


# 性能分析装饰器
import functools
import time


def log_performance(func):
    """
    性能分析装饰器，自动记录函数执行时间
    
    Examples:
        >>> @log_performance
        >>> def generate_chart(data, config):
        >>>     # ... 图表生成逻辑
        >>>     return chart
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        perf_logger = get_performance_logger()
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__qualname__}"
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            perf_logger.info(
                f"PERF | {func_name} | Success | {elapsed_time:.3f}s"
            )
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            perf_logger.error(
                f"PERF | {func_name} | Failed | {elapsed_time:.3f}s | Error: {str(e)}"
            )
            raise
    
    return wrapper


def log_execution_time(operation_name: str):
    """
    上下文管理器，用于记录代码块执行时间
    
    Args:
        operation_name: 操作名称
    
    Examples:
        >>> with log_execution_time('Load dashboard data'):
        >>>     data = load_dashboard_data(dashboard_id)
    """
    class ExecutionTimeLogger:
        def __init__(self, name: str):
            self.name = name
            self.start_time: Optional[float] = None
            self.perf_logger = get_performance_logger()
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.start_time is None:
                # 如果 start_time 为 None，使用当前时间作为默认值
                elapsed_time = 0.0
            else:
                elapsed_time = time.time() - self.start_time
            if exc_type is None:
                self.perf_logger.info(
                    f"PERF | {self.name} | Success | {elapsed_time:.3f}s"
                )
            else:
                self.perf_logger.error(
                    f"PERF | {self.name} | Failed | {elapsed_time:.3f}s | Error: {str(exc_val)}"
                )
            return False  # 不抑制异常
    
    return ExecutionTimeLogger(operation_name)


# 初始化日志系统
if __name__ == "__main__":
    # 测试日志系统
    logger = get_logger("test")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    perf_logger = get_performance_logger()
    perf_logger.info("Performance test: Operation took 0.123s")
    
    print("日志系统测试完成，请检查 logs/ 目录下的日志文件")

