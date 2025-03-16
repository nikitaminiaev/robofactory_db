

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
result = {'object_created': cube.Name, 'dimensions': [10, 10, 10]}
"""