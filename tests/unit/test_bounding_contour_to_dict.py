import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

from models.bounding_contour import BoundingContour


MODULE_ID = uuid.uuid4()


def _make_contour(brep_files):
    contour = BoundingContour.create(is_assembly=False, brep_files=brep_files, module_id=MODULE_ID)
    contour.id = uuid.uuid4()
    contour.parent_id = None
    contour.created_ts = None
    contour.updated_ts = None
    return contour


def _mock_resolved_path(content: str, exists: bool = True):
    path = MagicMock(spec=Path)
    path.exists.return_value = exists
    path.read_text.return_value = content
    path.__str__.return_value = f"/fake/{content[:8]}.brep"
    return path


@patch('models.bounding_contour.resolve_brep_absolute_path')
def test_to_dict_web_uploaded_brep_exposes_brep_string(mock_resolve):
    """BREP, загруженный через web-форму под реальным именем файла,
    должен отдаваться и под ключом brep_string."""
    content = "DBRep_DrawableShape CASCADE Topology V1"
    mock_resolve.return_value = _mock_resolved_path(content)
    contour = _make_contour({"COMPOUND029.brep": "modules/x/brep_files/COMPOUND029.brep"})

    result = contour.to_dict()

    assert result["brep_files"]["COMPOUND029.brep"] == content
    assert result["brep_files"]["brep_string"] == content
    assert result["brep_files"]["path"]


@patch('models.bounding_contour.resolve_brep_absolute_path')
def test_to_dict_freecad_saved_brep_unchanged(mock_resolve):
    """Модули, сохранённые из FreeCAD (ключ 'brep_string'), сериализуются как раньше."""
    content = "DBRep_DrawableShape FREECAD SHAPE"
    mock_resolve.return_value = _mock_resolved_path(content)
    contour = _make_contour({"brep_string": "modules/y/brep_files/brep_string.brep"})

    result = contour.to_dict()

    assert result["brep_files"]["brep_string"] == content
    assert result["brep_files"]["path"]


@patch('models.bounding_contour.resolve_brep_absolute_path')
def test_to_dict_missing_files_no_brep_string(mock_resolve):
    """Если файлы не существуют/пустые, ключ brep_string не добавляем."""
    missing_path = _mock_resolved_path("ignored", exists=False)
    mock_resolve.return_value = missing_path
    contour = _make_contour({"COMPOUND029.brep": "modules/x/brep_files/COMPOUND029.brep"})

    result = contour.to_dict()

    assert "brep_string" not in result["brep_files"]
    assert result["brep_files"]["COMPOUND029.brep"] == ""