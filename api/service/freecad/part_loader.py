import json
from typing import Optional
from service.web_soket_server import get_server_instance
from service.freecad.function import load_object_in_new_doc, save_brep, save_position


class PartLoader:
    def __init__(self):
        self.server = get_server_instance()

    def load_part_to_freecad(self, id: Optional[str] = None, depth: int = 1) -> bool:
        try:
            return self.server.send_message(load_object_in_new_doc(id, depth))
        except Exception as e:
            raise Exception(f"Ошибка при загрузке объекта во FreeCAD: {str(e)}")

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
