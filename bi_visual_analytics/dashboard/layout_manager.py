"""
仪表盘布局管理器
负责仪表盘的布局和组件管理
"""

from typing import Dict, Any, List, Optional
import json


class LayoutManager:
    """仪表盘布局管理器"""

    def __init__(self, columns: int = 12, row_height: int = 100):
        """
        初始化布局管理器

        Args:
            columns: 栅格列数
            row_height: 每行高度（像素）
        """
        self.columns = columns
        self.row_height = row_height
        self.components = []

    def add_component(
        self,
        component_id: str,
        component_type: str,
        config: Dict[str, Any],
        position: Dict[str, int],
    ):
        """
        添加组件到布局

        Args:
            component_id: 组件 ID
            component_type: 组件类型 (chart/filter/text/kpi)
            config: 组件配置
            position: 位置信息 {x, y, w, h}
        """
        component = {
            "id": component_id,
            "type": component_type,
            "config": config,
            "position": position,
        }

        # 验证位置
        self._validate_position(position)

        self.components.append(component)

    def remove_component(self, component_id: str) -> bool:
        """
        移除组件

        Args:
            component_id: 组件 ID

        Returns:
            bool: 是否成功移除
        """
        original_length = len(self.components)
        self.components = [c for c in self.components if c["id"] != component_id]
        return len(self.components) < original_length

    def update_component_position(
        self, component_id: str, position: Dict[str, int]
    ) -> bool:
        """
        更新组件位置

        Args:
            component_id: 组件 ID
            position: 新位置 {x, y, w, h}

        Returns:
            bool: 是否成功更新
        """
        self._validate_position(position)

        for component in self.components:
            if component["id"] == component_id:
                component["position"] = position
                return True

        return False

    def get_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        获取组件配置

        Args:
            component_id: 组件 ID

        Returns:
            dict: 组件配置，如果不存在返回 None
        """
        for component in self.components:
            if component["id"] == component_id:
                return component

        return None

    def get_all_components(self) -> List[Dict[str, Any]]:
        """获取所有组件"""
        return self.components

    def export_layout(self) -> Dict[str, Any]:
        """
        导出布局配置

        Returns:
            dict: 布局配置
        """
        return {
            "columns": self.columns,
            "row_height": self.row_height,
            "components": self.components,
        }

    def load_layout(self, layout_config: Dict[str, Any]):
        """
        加载布局配置

        Args:
            layout_config: 布局配置
        """
        self.columns = layout_config.get("columns", 12)
        self.row_height = layout_config.get("row_height", 100)
        self.components = layout_config.get("components", [])

    def _validate_position(self, position: Dict[str, int]):
        """
        验证位置参数

        Args:
            position: 位置信息

        Raises:
            ValueError: 位置参数无效
        """
        required_keys = ["x", "y", "w", "h"]
        for key in required_keys:
            if key not in position:
                raise ValueError(f"位置信息缺少 '{key}' 参数")

        # 验证范围
        if position["x"] < 0 or position["x"] >= self.columns:
            raise ValueError(f"x 坐标必须在 0-{self.columns-1} 之间")

        if position["w"] <= 0 or position["x"] + position["w"] > self.columns:
            raise ValueError(f"宽度超出栅格范围")

        if position["y"] < 0 or position["h"] <= 0:
            raise ValueError("y 坐标和高度必须大于 0")

    def auto_layout(self, components: List[Dict[str, Any]]):
        """
        自动布局组件

        Args:
            components: 组件列表
        """
        self.components = []
        current_y = 0

        for i, component in enumerate(components):
            # 默认每个组件占据半行，高度为 4 个单位
            width = 6
            height = 4

            # 根据类型调整大小
            if component.get("type") == "kpi":
                width = 3
                height = 2
            elif component.get("type") == "table":
                width = 12
                height = 6

            # 计算位置
            x = (i * width) % self.columns
            if x == 0 and i > 0:
                current_y += height

            position = {"x": x, "y": current_y, "w": width, "h": height}

            self.add_component(
                component_id=component.get("id", f"component-{i}"),
                component_type=component.get("type", "chart"),
                config=component.get("config", {}),
                position=position,
            )
