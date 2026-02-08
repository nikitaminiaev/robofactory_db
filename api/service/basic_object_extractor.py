from uuid import UUID
from models import Module
from repository.module_repository import ModuleRepository


class BasicObjectExtractor:
    def __init__(self, module_repository: ModuleRepository):
        self.module_repository = module_repository

    def extract_top_level_basic_objects(self, limit: int = 10, offset: int = 0, depth: int = 1) -> list[Module]:
        top_level_modules = self.module_repository.get_top_level_modules_with_relations(limit, offset)
        current_ids = [module.id for module in top_level_modules]
        
        basic_objects = top_level_modules.copy()
        
        for _ in range(depth):
            if not current_ids:
                break
            child_modules = self.module_repository.get_top_level_modules_with_relations(limit, offset, current_ids)
            if not child_modules:
                break
            basic_objects.extend(child_modules)
            current_ids = [module.id for module in child_modules]
        
        return basic_objects
    
    def extract_children_of_basic_object(self, id: UUID) -> list[Module]:
        return self.module_repository.get_children_modules_with_relations(id)
