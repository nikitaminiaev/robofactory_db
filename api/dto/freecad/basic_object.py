from models import Module
from pathlib import Path
import os


class BasicObject:
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.name = data.get('name', 'N/A')
        self.children: list[str] = data.get('children', [])
        self.parents: list[str] = data.get('parents', [])

        # Обработка случая, когда coordinates равно None
        coordinates = data.get('coordinates') or {}
        self.coordinates = {
            "x": coordinates.get('x', 0.0),
            "y": coordinates.get('y', 0.0),
            "z": coordinates.get('z', 0.0),
            "angle": coordinates.get('angle', 0.0),
            "axis": coordinates.get('axis', {}) or {"x": 0.0, "y": 0.0, "z": 0.0}
        }
        # Handle case where bounding_contour is None
        bounding_contour = data.get('bounding_contour', {})
        if bounding_contour is None:
            self.file_path = None
            self.brep_string = None
        else:
            brep_files = bounding_contour.get('brep_files', {})
            if brep_files is None or not brep_files:
                self.file_path = None
                self.brep_string = None
            else:
                # brep_files теперь содержит словарь {имя_файла: относительный_путь}
                # Найдем файл brep_string
                brep_file_path = brep_files.get('brep_string')
                if brep_file_path:
                    # Построим полный путь к файлу
                    full_path = Path("resources/brep_files") / brep_file_path
                    try:
                        if full_path.exists():
                            self.brep_string = full_path.read_text()
                            self.file_path = str(full_path)
                        else:
                            self.file_path = None
                            self.brep_string = None
                    except Exception:
                        self.file_path = None
                        self.brep_string = None
                else:
                    self.file_path = None
                    self.brep_string = None
    
    @classmethod
    def from_module(cls, module: Module):
        module_dict = module.to_dict()
        
        # Преобразование списка словарей в список id
        module_dict['children'] = [child['id'] for child in module_dict.get('children', [])]
        module_dict['parents'] = [parent['id'] for parent in module_dict.get('parents', [])]
        
        # Добавляем структуру координат, если её нет
        if 'coordinates' not in module_dict or module_dict['coordinates'] is None:
            module_dict['coordinates'] = {
                "x": 0.0, "y": 0.0, "z": 0.0, 
                "angle": 0.0, 
                "axis": {"x": 0.0, "y": 0.0, "z": 0.0}
            }
        
        return cls(module_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'children': self.children,
            'parents': self.parents,
            'coordinates': self.coordinates,
            'bounding_contour': {
                'brep_files': {
                    'path': self.file_path,
                    'brep_string': self.brep_string
                }
            } if self.brep_string else None
        }