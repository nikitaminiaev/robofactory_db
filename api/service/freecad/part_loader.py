import json
from typing import Optional, List, Dict, Any
from service.web_soket_server import get_server_instance
from service.freecad.function import load_object_in_new_doc, save_brep, save_position, create_empty_part


class PartLoader:
    def __init__(self):
        self.server = get_server_instance()

    def load_part_to_freecad(
        self,
        id: Optional[str] = None,
        child_depths: List[Dict[str, Any]] = None,
        absolute_coordinates: List[Dict[str, Any]] = None
    ) -> bool:
        try:
            if child_depths is None:
                child_depths = []
            if absolute_coordinates is None:
                absolute_coordinates = []
            return self.server.send_message(
                load_object_in_new_doc(id, child_depths, absolute_coordinates)
            )
        except Exception as e:
            raise Exception(f"Ошибка при загрузке объекта во FreeCAD: {str(e)}")

    def create_empty_part_in_freecad(self, module_id: str, module_name: str) -> bool:
        try:
            return self.server.send_message(create_empty_part(module_id, module_name))
        except Exception as e:
            raise Exception(f"Ошибка при отправке команды Create CAD во FreeCAD: {str(e)}")

    def trigger_save_brep(self, module_id: str) -> bool:
        try:
            return self.server.send_message(save_brep(module_id))
        except Exception as e:
            raise Exception(f"Ошибка при отправке команды Save BREP во FreeCAD: {str(e)}")

    def trigger_save_position(self, module_id: str) -> bool:
        try:
            return self.server.send_message(save_position(module_id))
        except Exception as e:
            raise Exception(f"Ошибка при отправке команды Save Position во FreeCAD: {str(e)}")
