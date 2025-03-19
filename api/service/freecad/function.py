def create_cube():
    return """
import FreeCAD
import Part
doc = FreeCAD.newDocument('Example')
box = Part.makeBox(10, 10, 10)
cube = doc.addObject('Part::Feature', 'Cube')
cube.Shape = box
doc.recompute()
# Возвращаем результат
result = {'object_created': cube.Name, 'document_name': doc.Name}
"""

def create_part_from_brep(brep_string: str, label: str, coordinates: dict = None, id: int = None):
    return f"""
import FreeCAD
import Part
doc = FreeCAD.newDocument('Example')

# Создаем объект Part
part_obj = doc.addObject('App::Part', '{label}')
body_obj = doc.addObject('Part::Feature', 'Body')

# Создаем форму из BREP строки
shape = Part.Shape()
shape.importBrepFromString('''{brep_string}''')
body_obj.Shape = shape

# Добавляем body в part
part_obj.Group = [body_obj]

if {id} is not None:
    part_obj.Id = {id}
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