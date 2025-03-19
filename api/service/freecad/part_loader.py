import json
from dto.freecad.basic_object import BasicObject
from service.web_soket_server import get_server_instance
from service.freecad.function import create_part_from_brep

class PartLoader:
    def __init__(self):
        self.server = get_server_instance()
    
    def load_part_to_freecad(self, basic_object: BasicObject) -> bool:
        """
        Загружает объект во FreeCAD через WebSocket
        
        Args:
            basic_object (BasicObject): DTO объект с данными для загрузки
            
        Returns:
            bool: True если сообщение успешно отправлено, False в противном случае
        """
        try:
            if not self.server.is_running():
                raise Exception("WebSocket-сервер не запущен")
            
            if not basic_object.brep_string:
                raise Exception("BREP строка отсутствует")
            
            python_code = create_part_from_brep(
                brep_string=basic_object.brep_string,
                label=basic_object.name,
                coordinates=basic_object.coordinates,
                id=basic_object.id
            )
            
            # Формируем сообщение для отправки
            message = json.dumps({
                "python_code": python_code,
                "object_id": str(basic_object.id),
                "object_name": basic_object.name
            })
            
            # Отправляем сообщение
            return self.server.send_message(message)
            
        except Exception as e:
            raise Exception(f"Ошибка при загрузке объекта во FreeCAD: {str(e)}")
