"""
配置管理器
负责数据源配置、图表配置、仪表盘配置的保存和加载
"""

import json
import yaml
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from logger import get_logger

logger = get_logger('config_manager')


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """初始化配置管理器
        
        Args:
            config_dir: 配置目录路径
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.datasources_file = self.config_dir / "datasources.yaml"
        self.charts_file = self.config_dir / "charts.json"
        self.dashboards_file = self.config_dir / "dashboards.json"
    
    # ==========================================
    # 数据源配置管理
    # ==========================================
    
    def load_datasources(self) -> List[Dict[str, Any]]:
        """加载所有数据源配置"""
        if not self.datasources_file.exists():
            logger.debug("数据源配置文件不存在，返回空列表")
            return []
        
        try:
            with open(self.datasources_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                datasources = data.get('datasources', [])
                logger.info(f"加载数据源配置: 共 {len(datasources)} 个")
                return datasources
        except Exception as e:
            logger.error(f"加载数据源配置失败: {e}", exc_info=True)
            return []
    
    def save_datasource(self, datasource_config: Dict[str, Any]) -> bool:
        """保存数据源配置"""
        datasources = self.load_datasources()
        ds_id = datasource_config.get('id')
        ds_name = datasource_config.get('name', 'Unnamed')
        ds_type = datasource_config.get('type', 'unknown')
        
        # 检查是否已存在（根据 ID 或名称）
        existing_idx = None
        for i, ds in enumerate(datasources):
            if ds.get('id') == ds_id or ds.get('name') == ds_name:
                existing_idx = i
                break
        
        # 添加或更新
        datasource_config['updated_at'] = datetime.now().isoformat()
        if existing_idx is not None:
            datasources[existing_idx] = datasource_config
            logger.info(f"更新数据源 [ID: {ds_id}, 名称: {ds_name}, 类型: {ds_type}]")
        else:
            if 'id' not in datasource_config:
                datasource_config['id'] = f"ds_{len(datasources) + 1}_{int(datetime.now().timestamp())}"
            datasource_config['created_at'] = datetime.now().isoformat()
            datasources.append(datasource_config)
            logger.info(f"创建数据源 [ID: {datasource_config['id']}, 名称: {ds_name}, 类型: {ds_type}]")
        
        # 保存到文件
        try:
            with open(self.datasources_file, 'w', encoding='utf-8') as f:
                yaml.dump({'datasources': datasources}, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            logger.error(f"保存数据源配置失败 [ID: {ds_id}]: {e}", exc_info=True)
            return False
    
    def delete_datasource(self, datasource_id: str) -> bool:
        """删除数据源配置"""
        datasources = self.load_datasources()
        original_count = len(datasources)
        datasources = [ds for ds in datasources if ds.get('id') != datasource_id]
        
        if len(datasources) < original_count:
            try:
                with open(self.datasources_file, 'w', encoding='utf-8') as f:
                    yaml.dump({'datasources': datasources}, f, default_flow_style=False, allow_unicode=True)
                logger.info(f"删除数据源 [ID: {datasource_id}]")
                return True
            except Exception as e:
                logger.error(f"删除数据源配置失败 [ID: {datasource_id}]: {e}", exc_info=True)
                return False
        else:
            logger.warning(f"数据源不存在，无法删除 [ID: {datasource_id}]")
            return False
    
    def get_datasource(self, datasource_id: str) -> Optional[Dict[str, Any]]:
        """获取单个数据源配置"""
        datasources = self.load_datasources()
        for ds in datasources:
            if ds.get('id') == datasource_id:
                return ds
        return None
    
    # ==========================================
    # 图表配置管理
    # ==========================================
    
    def load_charts(self) -> List[Dict[str, Any]]:
        """加载所有图表配置"""
        if not self.charts_file.exists():
            logger.debug("图表配置文件不存在，返回空列表")
            return []
        
        try:
            with open(self.charts_file, 'r', encoding='utf-8') as f:
                charts = json.load(f).get('charts', [])
                logger.info(f"加载图表配置: 共 {len(charts)} 个")
                return charts
        except Exception as e:
            logger.error(f"加载图表配置失败: {e}", exc_info=True)
            return []
    
    def save_chart(self, chart_config: Dict[str, Any]) -> bool:
        """保存图表配置"""
        charts = self.load_charts()
        chart_id = chart_config.get('id')
        chart_name = chart_config.get('name', 'Unnamed')
        chart_type = chart_config.get('type', 'unknown')
        
        existing_idx = None
        for i, chart in enumerate(charts):
            if chart.get('id') == chart_id:
                existing_idx = i
                break
        
        chart_config['updated_at'] = datetime.now().isoformat()
        if existing_idx is not None:
            charts[existing_idx] = chart_config
            logger.info(f"更新图表 [ID: {chart_id}, 名称: {chart_name}, 类型: {chart_type}]")
        else:
            if 'id' not in chart_config:
                chart_config['id'] = f"chart_{len(charts) + 1}_{int(datetime.now().timestamp())}"
            chart_config['created_at'] = datetime.now().isoformat()
            charts.append(chart_config)
            logger.info(f"创建图表 [ID: {chart_config['id']}, 名称: {chart_name}, 类型: {chart_type}]")
        
        try:
            with open(self.charts_file, 'w', encoding='utf-8') as f:
                json.dump({'charts': charts}, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存图表配置失败 [ID: {chart_id}]: {e}", exc_info=True)
            return False
    
    def get_chart(self, chart_id: str) -> Optional[Dict[str, Any]]:
        """获取单个图表配置"""
        charts = self.load_charts()
        for chart in charts:
            if chart.get('id') == chart_id:
                return chart
        return None
    
    def delete_chart(self, chart_id: str) -> bool:
        """删除图表配置"""
        charts = self.load_charts()
        original_count = len(charts)
        charts = [chart for chart in charts if chart.get('id') != chart_id]
        
        if len(charts) < original_count:
            try:
                with open(self.charts_file, 'w', encoding='utf-8') as f:
                    json.dump({'charts': charts}, f, indent=2, ensure_ascii=False)
                logger.info(f"删除图表 [ID: {chart_id}]")
                return True
            except Exception as e:
                logger.error(f"删除图表配置失败 [ID: {chart_id}]: {e}", exc_info=True)
                return False
        else:
            logger.warning(f"图表不存在，无法删除 [ID: {chart_id}]")
            return False
    
    # ==========================================
    # 仪表盘配置管理
    # ==========================================
    
    def load_dashboards(self) -> List[Dict[str, Any]]:
        """加载所有仪表盘配置"""
        if not self.dashboards_file.exists():
            logger.debug("仪表盘配置文件不存在，返回空列表")
            return []
        
        try:
            with open(self.dashboards_file, 'r', encoding='utf-8') as f:
                dashboards = json.load(f).get('dashboards', [])
                logger.info(f"加载仪表盘配置: 共 {len(dashboards)} 个")
                return dashboards
        except Exception as e:
            logger.error(f"加载仪表盘配置失败: {e}", exc_info=True)
            return []
    
    def save_dashboard(self, dashboard_config: Dict[str, Any]) -> bool:
        """保存仪表盘配置"""
        dashboards = self.load_dashboards()
        dashboard_id = dashboard_config.get('id')
        dashboard_name = dashboard_config.get('name', 'Unnamed')
        chart_count = len(dashboard_config.get('chart_ids', []))
        
        existing_idx = None
        for i, dashboard in enumerate(dashboards):
            if dashboard.get('id') == dashboard_id:
                existing_idx = i
                break
        
        dashboard_config['updated_at'] = datetime.now().isoformat()
        if existing_idx is not None:
            dashboards[existing_idx] = dashboard_config
            logger.info(f"更新仪表盘 [ID: {dashboard_id}, 名称: {dashboard_name}, 图表数: {chart_count}]")
        else:
            if 'id' not in dashboard_config:
                dashboard_config['id'] = f"dashboard_{len(dashboards) + 1}_{int(datetime.now().timestamp())}"
            dashboard_config['created_at'] = datetime.now().isoformat()
            dashboards.append(dashboard_config)
            logger.info(f"创建仪表盘 [ID: {dashboard_config['id']}, 名称: {dashboard_name}]")
        
        try:
            with open(self.dashboards_file, 'w', encoding='utf-8') as f:
                json.dump({'dashboards': dashboards}, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存仪表盘配置失败 [ID: {dashboard_id}]: {e}", exc_info=True)
            return False
    
    def get_dashboard(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """获取单个仪表盘配置"""
        dashboards = self.load_dashboards()
        for dashboard in dashboards:
            if dashboard.get('id') == dashboard_id:
                return dashboard
        return None
    
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """删除仪表盘配置"""
        dashboards = self.load_dashboards()
        original_count = len(dashboards)
        dashboards = [dashboard for dashboard in dashboards if dashboard.get('id') != dashboard_id]
        
        if len(dashboards) < original_count:
            try:
                with open(self.dashboards_file, 'w', encoding='utf-8') as f:
                    json.dump({'dashboards': dashboards}, f, indent=2, ensure_ascii=False)
                logger.info(f"删除仪表盘 [ID: {dashboard_id}]")
                return True
            except Exception as e:
                logger.error(f"删除仪表盘配置失败 [ID: {dashboard_id}]: {e}", exc_info=True)
                return False
        else:
            logger.warning(f"仪表盘不存在，无法删除 [ID: {dashboard_id}]")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """导出所有配置到单个文件"""
        config = {
            'datasources': self.load_datasources(),
            'charts': self.load_charts(),
            'dashboards': self.load_dashboards(),
            'exported_at': datetime.now().isoformat()
        }
        
        export_path_obj = Path(export_path)
        if export_path_obj.suffix == '.yaml' or export_path_obj.suffix == '.yml':
            with open(export_path_obj, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        else:
            with open(export_path_obj, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    
    def import_config(self, import_path: str) -> bool:
        """从文件导入配置"""
        import_path_obj = Path(import_path)
        
        if import_path_obj.suffix == '.yaml' or import_path_obj.suffix == '.yml':
            with open(import_path_obj, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            with open(import_path_obj, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # 导入数据源
        if 'datasources' in config:
            for ds in config['datasources']:
                self.save_datasource(ds)
        
        # 导入图表
        if 'charts' in config:
            for chart in config['charts']:
                self.save_chart(chart)
        
        # 导入仪表盘
        if 'dashboards' in config:
            for dashboard in config['dashboards']:
                self.save_dashboard(dashboard)
        
        return True

