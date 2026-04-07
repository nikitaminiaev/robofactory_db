import pytest
from uuid import UUID
from unittest.mock import MagicMock
from service.freecad.hierarchy_loader import HierarchyLoader


class MockModule:
    def __init__(self, module_id):
        self.id = module_id
        self.name = f"module_{module_id}"
        self.bounding_contour = MagicMock()


class TestHierarchyLoader:

    def test_compute_absolute_coords_no_parent(self):
        """Тест: без родителя координаты равны относительным"""
        mock_repo = MagicMock()
        loader = HierarchyLoader(mock_repo)

        child_coords = {"x": 10.0, "y": 20.0, "z": 30.0, "angle": 0.0, "axis": {"x": 0, "y": 0, "z": 1}}
        result = loader._compute_absolute_coords(None, child_coords)

        assert result["x"] == 10.0
        assert result["y"] == 20.0
        assert result["z"] == 30.0

    def test_compute_absolute_coords_with_parent(self):
        """Тест: с родителем координаты складываются"""
        mock_repo = MagicMock()
        loader = HierarchyLoader(mock_repo)

        parent_coords = {"x": 100.0, "y": 200.0, "z": 300.0, "angle": 0.0, "axis": {"x": 0, "y": 0, "z": 1}}
        child_coords = {"x": 10.0, "y": 20.0, "z": 30.0, "angle": 0.0, "axis": {"x": 0, "y": 0, "z": 1}}
        result = loader._compute_absolute_coords(parent_coords, child_coords)

        assert result["x"] == 110.0
        assert result["y"] == 220.0
        assert result["z"] == 330.0

    def test_compute_absolute_coords_no_child(self):
        """Тест: без ребенка координаты равны родительским"""
        mock_repo = MagicMock()
        loader = HierarchyLoader(mock_repo)

        parent_coords = {"x": 100.0, "y": 200.0, "z": 300.0, "angle": 0.5, "axis": {"x": 0, "y": 0, "z": 1}}
        result = loader._compute_absolute_coords(parent_coords, {})

        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert result["z"] == 300.0

    def test_default_coordinates(self):
        """Тест: дефолтные координаты"""
        mock_repo = MagicMock()
        loader = HierarchyLoader(mock_repo)

        result = loader._default_coordinates()

        assert result["x"] == 0.0
        assert result["y"] == 0.0
        assert result["z"] == 0.0
        assert result["angle"] == 0.0
        assert result["axis"] == {"x": 0.0, "y": 0.0, "z": 0.0}

    def test_axis_angle_to_quaternion(self):
        """Тест: конвертация axis-angle в quaternion"""
        mock_repo = MagicMock()
        loader = HierarchyLoader(mock_repo)

        result = loader._axis_angle_to_quaternion(0.0, {"x": 0, "y": 0, "z": 1})

        assert result["w"] == 1.0
        assert result["x"] == 0.0
        assert result["y"] == 0.0
        assert result["z"] == 0.0

    def test_quaternion_to_axis_angle(self):
        """Тест: конвертация quaternion в axis-angle"""
        mock_repo = MagicMock()
        loader = HierarchyLoader(mock_repo)

        result = loader._quaternion_to_axis_angle({"x": 0, "y": 0, "z": 0, "w": 1})

        assert result["angle"] == 0.0

    def test_multiply_quaternions_identity(self):
        """Тест: умножение quaternion на identity"""
        mock_repo = MagicMock()
        loader = HierarchyLoader(mock_repo)

        identity = {"x": 0, "y": 0, "z": 0, "w": 1}
        q = {"x": 0.1, "y": 0.2, "z": 0.3, "w": 0.9}

        result = loader._multiply_quaternions(identity, q)

        assert abs(result["x"] - 0.1) < 0.001
        assert abs(result["y"] - 0.2) < 0.001
        assert abs(result["z"] - 0.3) < 0.001
        assert abs(result["w"] - 0.9) < 0.001

    def test_get_hierarchy_with_absolute_coordinates_empty_root(self):
        """Тест: несуществующий корень возвращает пустой список"""
        mock_repo = MagicMock()
        mock_repo.get_module_with_relations_by_id.return_value = None

        loader = HierarchyLoader(mock_repo)
        result = loader.get_hierarchy_with_absolute_coordinates(
            UUID('12345678-1234-5678-1234-567812345678'),
            []
        )

        assert result == []

    def test_get_hierarchy_with_absolute_coordinates_single_level(self):
        """Тест: один уровень вложенности"""
        root_id = UUID('12345678-1234-5678-1234-567812345678')
        child_id = UUID('87654321-4321-8765-4321-876543218765')

        mock_repo = MagicMock()
        mock_repo.get_module_with_relations_by_id.return_value = MockModule(root_id)
        mock_repo.get_children_coordinates.return_value = [
            {
                "parent_child_module_id": "pcm-001",
                "child_id": str(child_id),
                "coordinates": {"x": 10.0, "y": 20.0, "z": 30.0, "angle": 0.0, "axis": {"x": 0, "y": 0, "z": 1}}
            }
        ]

        loader = HierarchyLoader(mock_repo)
        result = loader.get_hierarchy_with_absolute_coordinates(root_id, [])

        assert len(result) == 2  # корень + ребёнок
        assert result[0]["object_id"] == str(root_id)
        assert result[0]["depth"] == 0
        assert result[1]["object_id"] == str(child_id)
        assert result[1]["depth"] == 1
        assert result[1]["absolute_coordinates"]["x"] == 10.0

    def test_get_hierarchy_with_absolute_coordinates_two_levels(self):
        """Тест: два уровня вложенности с накоплением координат"""
        root_id = UUID('11111111-1111-1111-1111-111111111111')
        child1_id = UUID('22222222-2222-2222-2222-222222222222')
        child2_id = UUID('33333333-3333-3333-3333-333333333333')

        mock_repo = MagicMock()
        mock_repo.get_module_with_relations_by_id.return_value = MockModule(root_id)
        
        def mock_get_children(parent_id):
            if parent_id == root_id:
                return [{
                    "parent_child_module_id": "pcm-1",
                    "child_id": str(child1_id),
                    "coordinates": {"x": 10.0, "y": 0.0, "z": 0.0, "angle": 0.0, "axis": {"x": 0, "y": 0, "z": 1}}
                }]
            elif parent_id == child1_id:
                return [{
                    "parent_child_module_id": "pcm-2",
                    "child_id": str(child2_id),
                    "coordinates": {"x": 5.0, "y": 0.0, "z": 0.0, "angle": 0.0, "axis": {"x": 0, "y": 0, "z": 1}}
                }]
            return []

        mock_repo.get_children_coordinates.side_effect = mock_get_children

        loader = HierarchyLoader(mock_repo)
        
        child_depths = [
            {"child_id": str(child1_id), "parent_child_module_id": "pcm-1", "depth": 2}
        ]
        
        result = loader.get_hierarchy_with_absolute_coordinates(root_id, child_depths)

        root_entry = next(r for r in result if r["depth"] == 0)
        child1_entry = next(r for r in result if r["object_id"] == str(child1_id))
        child2_entry = next(r for r in result if r["object_id"] == str(child2_id))

        assert root_entry["absolute_coordinates"]["x"] == 0.0
        assert child1_entry["absolute_coordinates"]["x"] == 10.0
        assert child2_entry["absolute_coordinates"]["x"] == 15.0  # 10 + 5

    def test_get_hierarchy_respects_depth_limit(self):
        """Тест: глубина ограничивается правильно"""
        root_id = UUID('11111111-1111-1111-1111-111111111111')
        child1_id = UUID('22222222-2222-2222-2222-222222222222')
        child2_id = UUID('33333333-3333-3333-3333-333333333333')

        mock_repo = MagicMock()
        mock_repo.get_module_with_relations_by_id.return_value = MockModule(root_id)
        
        def mock_get_children(parent_id):
            if parent_id == root_id:
                return [{
                    "parent_child_module_id": "pcm-1",
                    "child_id": str(child1_id),
                    "coordinates": {"x": 10.0, "y": 0.0, "z": 0.0, "angle": 0.0, "axis": {"x": 0, "y": 0, "z": 1}}
                }]
            elif parent_id == child1_id:
                return [{
                    "parent_child_module_id": "pcm-2",
                    "child_id": str(child2_id),
                    "coordinates": {"x": 5.0, "y": 0.0, "z": 0.0, "angle": 0.0, "axis": {"x": 0, "y": 0, "z": 1}}
                }]
            return []

        mock_repo.get_children_coordinates.side_effect = mock_get_children

        loader = HierarchyLoader(mock_repo)
        
        child_depths = [
            {"child_id": str(child1_id), "parent_child_module_id": "pcm-1", "depth": 1}  # только 1 уровень
        ]
        
        result = loader.get_hierarchy_with_absolute_coordinates(root_id, child_depths)

        result_ids = [r["object_id"] for r in result]
        
        assert str(root_id) in result_ids
        assert str(child1_id) in result_ids
        assert str(child2_id) not in result_ids  # не загружается из-за глубины 1
