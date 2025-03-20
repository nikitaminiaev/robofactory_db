import json
from typing import Optional
from service.web_soket_server import get_server_instance
from service.freecad.function import load_object_in_new_doc

class PartLoader:
    def __init__(self):
        self.server = get_server_instance()
    
    def load_part_to_freecad(self, id: Optional[str] = None) -> bool:
        try:
            return self.server.send_message(load_object_in_new_doc(id))
        except Exception as e:
            raise Exception(f"Ошибка при загрузке объекта во FreeCAD: {str(e)}")
