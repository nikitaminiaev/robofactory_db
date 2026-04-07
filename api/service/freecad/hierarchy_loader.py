from typing import List, Dict, Any, Optional
from uuid import UUID

from repository.module_repository import ModuleRepository


class HierarchyLoader:
    def __init__(self, repo: ModuleRepository):
        self.repo = repo

    def get_hierarchy_with_absolute_coordinates(
        self,
        root_id: UUID,
        child_depths: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Рекурсивно получает иерархию объектов с вычисленными абсолютными координатами.
        
        Args:
            root_id: UUID корневого объекта
            child_depths: массив объектов {child_id, parent_child_module_id, depth}
        
        Returns:
            Список всех объектов в иерархии с абсолютными координатами:
            [{
                "object_id": "uuid",
                "parent_child_module_id": "uuid",
                "absolute_coordinates": {...},
                "depth": 1
            }, ...]
            
        Примечание: depth=0 соответствует корневому объекту, depth=1 - его детям, и т.д.
        """
        child_depths_dict = {
            (cd.get('child_id'), cd.get('parent_child_module_id')): cd.get('depth', 1)
            for cd in child_depths
        }
        
        root_module = self.repo.get_module_with_relations_by_id(root_id)
        if not root_module:
            return []
        
        result = []
        visited = set()  # Защита от зацикливания
        
        # Добавляем корневой объект с depth=0 (это относительно самого себя, т.е. нули)
        result.append({
            "object_id": str(root_module.id),
            "parent_child_module_id": None,
            "absolute_coordinates": self._default_coordinates(),
            "depth": 0
        })
        
        children_with_coords = self.repo.get_children_coordinates(root_id)
        
        self._process_children(
            result=result,
            parent_id=root_id,
            parent_absolute_coords=None,
            children_with_coords=children_with_coords,
            child_depths_dict=child_depths_dict,
            current_depth=0,
            visited=visited
        )
        
        return result

    def _process_children(
        self,
        result: List[Dict[str, Any]],
        parent_id: UUID,
        parent_absolute_coords: Optional[Dict[str, Any]],
        children_with_coords: List[Dict[str, Any]],
        child_depths_dict: Dict[tuple, int],
        current_depth: int,
        visited: set = None
    ):
        """Рекурсивно обрабатывает дочерние объекты."""
        
        if visited is None:
            visited = set()
        
        for child_entry in children_with_coords:
            child_id = child_entry["child_id"]
            pcm_id = child_entry["parent_child_module_id"]
            relative_coords = child_entry.get("coordinates") or {}
            
            # Защита от зацикливания
            visit_key = (child_id, pcm_id)
            if child_id == str(parent_id) or visit_key in visited:
                continue
            visited.add(visit_key)
            
            key = (child_id, pcm_id)
            depth = child_depths_dict.get(key, 1)
            
            if depth <= 0:
                continue
            
            absolute_coords = self._compute_absolute_coords(
                parent_absolute_coords,
                relative_coords
            )
            
            result.append({
                "object_id": child_id,
                "parent_child_module_id": pcm_id,
                "absolute_coordinates": absolute_coords,
                "depth": current_depth + 1
            })
            
            if depth > 1:
                next_children = self.repo.get_children_coordinates(UUID(child_id))
                self._process_children(
                    result=result,
                    parent_id=UUID(child_id),
                    parent_absolute_coords=absolute_coords,
                    children_with_coords=next_children,
                    child_depths_dict=child_depths_dict,
                    current_depth=current_depth + 1,
                    visited=visited
                )

    def _compute_absolute_coords(
        self,
        parent_coords: Optional[Dict[str, Any]],
        child_coords: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Вычисляет абсолютные координаты ребёнка.
        
        Position: child_abs = parent_abs + child_rel (только если parent_coords не None)
        Rotation: quaternion умножение parent * child
        
        Args:
            parent_coords: абсолютные координаты родителя (могут быть None для корня)
            child_coords: относительные координаты ребёнка из parent_child_module
        
        Returns:
            Абсолютные координаты для ребёнка
        """
        if not parent_coords:
            return child_coords.copy() if child_coords else self._default_coordinates()
        
        if not child_coords:
            return parent_coords.copy()
        
        parent_pos = parent_coords.get("x", 0), parent_coords.get("y", 0), parent_coords.get("z", 0)
        child_pos = child_coords.get("x", 0), child_coords.get("y", 0), child_coords.get("z", 0)
        
        abs_x = parent_pos[0] + child_pos[0]
        abs_y = parent_pos[1] + child_pos[1]
        abs_z = parent_pos[2] + child_pos[2]
        
        parent_rot = self._axis_angle_to_quaternion(
            parent_coords.get("angle", 0),
            parent_coords.get("axis", {"x": 0, "y": 0, "z": 0})
        )
        child_rot = self._axis_angle_to_quaternion(
            child_coords.get("angle", 0),
            child_coords.get("axis", {"x": 0, "y": 0, "z": 0})
        )
        
        abs_rot = self._multiply_quaternions(parent_rot, child_rot)
        abs_axis_angle = self._quaternion_to_axis_angle(abs_rot)
        
        return {
            "x": abs_x,
            "y": abs_y,
            "z": abs_z,
            "angle": abs_axis_angle["angle"],
            "axis": abs_axis_angle["axis"]
        }

    def _default_coordinates(self) -> Dict[str, Any]:
        return {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "angle": 0.0,
            "axis": {"x": 0.0, "y": 0.0, "z": 0.0}
        }

    def _axis_angle_to_quaternion(self, angle: float, axis: Dict[str, float]) -> Dict[str, float]:
        """Конвертирует axis-angle в quaternion."""
        ax = axis.get("x", 0)
        ay = axis.get("y", 0)
        az = axis.get("z", 0)
        
        norm = (ax * ax + ay * ay + az * az) ** 0.5
        if norm < 1e-10:
            return {"x": 0, "y": 0, "z": 0, "w": 1}
        
        ax, ay, az = ax / norm, ay / norm, az / norm
        half_angle = angle / 2
        sin_half = (half_angle ** 0.5 if half_angle >= 0 else -(abs(half_angle) ** 0.5))
        import math
        sin_half = math.sin(half_angle)
        cos_half = math.cos(half_angle)
        
        return {
            "x": ax * sin_half,
            "y": ay * sin_half,
            "z": az * sin_half,
            "w": cos_half
        }

    def _quaternion_to_axis_angle(self, q: Dict[str, float]) -> Dict[str, Any]:
        """Конвертирует quaternion в axis-angle."""
        import math
        
        x, y, z, w = q.get("x", 0), q.get("y", 0), q.get("z", 0), q.get("w", 1)
        
        norm = (x * x + y * y + z * z + w * w) ** 0.5
        if norm < 1e-10:
            return {"angle": 0, "axis": {"x": 0, "y": 0, "z": 0}}
        
        x, y, z, w = x / norm, y / norm, z / norm, w / norm
        
        if abs(w) > 1:
            w = 1 if w > 0 else -1
        
        angle = 2 * math.acos(w)
        
        if abs(angle) < 1e-10:
            return {"angle": 0, "axis": {"x": 0, "y": 0, "z": 0}}
        
        sin_half = (1 - w * w) ** 0.5
        if abs(sin_half) < 1e-10:
            return {"angle": angle, "axis": {"x": 1, "y": 0, "z": 0}}
        
        ax = x / sin_half
        ay = y / sin_half
        az = z / sin_half
        
        return {"angle": angle, "axis": {"x": ax, "y": ay, "z": az}}

    def _multiply_quaternions(self, q1: Dict[str, float], q2: Dict[str, float]) -> Dict[str, float]:
        """Умножает два quaternion: q1 * q2."""
        x1, y1, z1, w1 = q1.get("x", 0), q1.get("y", 0), q1.get("z", 0), q1.get("w", 1)
        x2, y2, z2, w2 = q2.get("x", 0), q2.get("y", 0), q2.get("z", 0), q2.get("w", 1)
        
        return {
            "x": w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            "y": w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            "z": w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            "w": w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        }
