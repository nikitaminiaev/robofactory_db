import pytest
from uuid import UUID
from unittest.mock import Mock, MagicMock
from service.basic_object_extractor import BasicObjectExtractor


class TestBasicObjectExtractor:

    def test_extract_top_level_basic_objects_depth_1(self):
        # Setup mock repository
        mock_repo = MagicMock()
        mock_modules = [MagicMock(), MagicMock()]
        mock_repo.get_top_level_modules_with_relations.return_value = mock_modules
        
        extractor = BasicObjectExtractor(mock_repo)
        
        # Call method
        result = extractor.extract_top_level_basic_objects(limit=10, offset=0, depth=1)
        
        # Assertions
        assert result == mock_modules
        mock_repo.get_top_level_modules_with_relations.assert_called_once_with(10, 0)

    def test_extract_top_level_basic_objects_depth_2(self):
        # Setup mock repository
        mock_repo = MagicMock()
        
        # Depth 1
        mock_modules_depth1 = [MagicMock(), MagicMock()]
        mock_modules_depth1[0].id = UUID('11111111-1111-1111-1111-111111111111')
        mock_modules_depth1[1].id = UUID('22222222-2222-2222-2222-222222222222')
        
        # Depth 2 - children of depth1
        mock_modules_depth2 = [MagicMock(), MagicMock()]
        
        mock_repo.get_top_level_modules_with_relations.side_effect = [
            mock_modules_depth1,  # First call for top level
            mock_modules_depth2,  # Second call for children
            []  # Third call returns empty (no more children)
        ]
        
        extractor = BasicObjectExtractor(mock_repo)
        
        # Call method
        result = extractor.extract_top_level_basic_objects(limit=10, offset=0, depth=2)
        
        # Assertions
        expected = mock_modules_depth1 + mock_modules_depth2
        assert result == expected
        assert mock_repo.get_top_level_modules_with_relations.call_count == 3

    def test_extract_top_level_basic_objects_no_children(self):
        # Setup mock repository with no children
        mock_repo = MagicMock()
        mock_modules = [MagicMock(), MagicMock()]
        mock_repo.get_top_level_modules_with_relations.side_effect = [
            mock_modules,  # Top level
            []  # No children
        ]
        
        extractor = BasicObjectExtractor(mock_repo)
        
        # Call method
        result = extractor.extract_top_level_basic_objects(limit=10, offset=0, depth=2)
        
        # Assertions
        assert result == mock_modules  # Only top level, no children added
        assert mock_repo.get_top_level_modules_with_relations.call_count == 2

    def test_extract_children_of_basic_object(self):
        # Setup mock repository
        mock_repo = MagicMock()
        mock_children = [MagicMock(), MagicMock(), MagicMock()]
        mock_repo.get_children_modules_with_relations.return_value = mock_children
        
        extractor = BasicObjectExtractor(mock_repo)
        
        # Call method
        module_id = UUID('12345678-1234-5678-1234-567812345678')
        result = extractor.extract_children_of_basic_object(module_id)
        
        # Assertions
        assert result == mock_children
        mock_repo.get_children_modules_with_relations.assert_called_once_with(module_id)