import json


def save_brep(module_id: str) -> str:
    """Команда FreeCAD: экспортировать BREP первого тела и сохранить в модуль."""
    return json.dumps({
        "function_call": "save_brep",
        "arguments": {"module_id": module_id},
    })


def save_position(module_id: str) -> str:
    """Команда FreeCAD: обновить координаты всех дочерних объектов текущей сборки."""
    return json.dumps({
        "function_call": "save_position",
        "arguments": {"module_id": module_id},
    })


def create_part_from_brep(brep_string: str, label: str, coordinates: dict = None, id: str = ''):
    return f"""
import FreeCAD
import Part
doc = FreeCAD.newDocument('{label}')

# Создаем объект Part
part_obj = doc.addObject('App::Part', '{label}')
body_obj = doc.addObject('Part::Feature', 'Body')

# Создаем форму из BREP строки
shape = Part.Shape()
shape.importBrepFromString('''{brep_string}''')
body_obj.Shape = shape

# Добавляем body в part
part_obj.Group = [body_obj]

if '{id}' != '':
    part_obj.Id = '{id}'
# Устанавливаем координаты если они есть
if {coordinates}:
    part_obj.Placement.Base.x = {coordinates.get('x', 0.0)}
    part_obj.Placement.Base.y = {coordinates.get('y', 0.0)}
    part_obj.Placement.Base.z = {coordinates.get('z', 0.0)}
    part_obj.Placement.Rotation.Angle = {coordinates.get('angle', 0.0)}
    part_obj.Placement.Rotation.Axis.x = {coordinates.get('axis', {}).get('x', 0.0)}
    part_obj.Placement.Rotation.Axis.y = {coordinates.get('axis', {}).get('y', 0.0)}
    part_obj.Placement.Rotation.Axis.z = {coordinates.get('axis', {}).get('z', 0.0)}

doc.recompute()
Gui.SendMsgToActiveView("ViewFit")
# Возвращаем результат
result = {{'object_created': part_obj.Name, 'document_name': doc.Name}}
"""

def load_object_in_new_doc(obj_id: str):
    return f'''
            {{
                "function_call": "load_object_in_new_doc",
                "arguments": {{
                    "obj_id": "{obj_id}"
                }}
            }}
            '''