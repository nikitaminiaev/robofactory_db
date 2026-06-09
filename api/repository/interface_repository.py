from uuid import UUID
from typing import Any, Optional, List, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import BaseRepository
from models import InterfaceObject, InterfaceMapping, Module, RolePort
from models.associations import parent_child_module, parent_child_module_role_assignment


class InterfaceRepository(BaseRepository):

    def _to_dict(self, iface: InterfaceObject) -> dict:
        obj = cast(Any, iface)
        return {
            "id": str(obj.id),
            "name": obj.name,
            "direction": obj.direction,
            "physical_form": obj.physical_form,
            "parameters": obj.parameters,
            "is_mandatory": obj.is_mandatory,
            "is_service": obj.is_service,
            "module_id": str(obj.module_id) if obj.module_id else None,
            "description": obj.description,
            "ttx": obj.ttx,
            "coordinates": obj.coordinates,
            "created_ts": obj.created_ts.isoformat() if obj.created_ts else None,
            "updated_ts": obj.updated_ts.isoformat() if obj.updated_ts else None,
        }

    def get_module_interfaces(self, module_id: UUID) -> List[dict]:
        with self.db_session.session() as db:
            interfaces = (
                db.query(InterfaceObject)
                .filter(InterfaceObject.module_id == module_id)
                .order_by(InterfaceObject.name)
                .all()
            )
            return [self._to_dict(i) for i in interfaces]

    def get_interface_by_id(self, interface_id: UUID) -> Optional[dict]:
        with self.db_session.session() as db:
            iface = db.query(InterfaceObject).filter(InterfaceObject.id == interface_id).first()
            return self._to_dict(iface) if iface else None

    def create_interface(
        self,
        module_id: UUID,
        name: str,
        direction: str = "bidirectional",
        physical_form: Optional[str] = None,
        parameters: Optional[dict] = None,
        is_mandatory: bool = True,
        is_service: bool = False,
        description: Optional[str] = None,
        ttx: Optional[str] = None,
    ) -> dict:
        with self.db_session.session() as db:
            module = db.query(Module).filter(Module.id == module_id).first()
            if not module:
                raise ValueError(f"Module with ID '{module_id}' not found")

            iface = InterfaceObject(
                name=name,
                direction=direction,
                physical_form=physical_form,
                parameters=parameters,
                is_mandatory=is_mandatory,
                is_service=is_service,
                module_id=module_id,
                description=description,
                ttx=ttx,
            )
            db.add(iface)
            db.commit()
            db.refresh(iface)
            return self._to_dict(iface)

    def update_interface(
        self,
        interface_id: UUID,
        name: Optional[str] = None,
        module_id: Optional[UUID] = None,
        direction: Optional[str] = None,
        physical_form: Optional[str] = None,
        parameters: Optional[dict] = None,
        is_mandatory: Optional[bool] = None,
        is_service: Optional[bool] = None,
        description: Optional[str] = None,
        ttx: Optional[str] = None,
    ) -> Optional[dict]:
        with self.db_session.session() as db:
            iface = db.query(InterfaceObject).filter(InterfaceObject.id == interface_id).first()
            if not iface:
                return None

            obj = cast(Any, iface)
            if module_id is not None and obj.module_id != module_id:
                raise ValueError("Интерфейс не принадлежит указанному модулю")

            if name is not None:
                obj.name = name
            if direction is not None:
                obj.direction = direction
            if physical_form is not None:
                obj.physical_form = physical_form
            if parameters is not None:
                obj.parameters = parameters
            if is_mandatory is not None:
                obj.is_mandatory = is_mandatory
            if is_service is not None:
                obj.is_service = is_service
            if description is not None:
                obj.description = description
            if ttx is not None:
                obj.ttx = ttx

            db.commit()
            db.refresh(iface)
            return self._to_dict(iface)

    def delete_interface(self, interface_id: UUID, module_id: Optional[UUID] = None) -> bool:
        with self.db_session.session() as db:
            iface = db.query(InterfaceObject).filter(InterfaceObject.id == interface_id).first()
            if not iface:
                return False
            if module_id is not None and cast(Any, iface).module_id != module_id:
                return False
            db.delete(iface)
            db.commit()
            return True


class InterfaceMappingRepository(BaseRepository):

    def _to_dict(self, mapping: InterfaceMapping) -> dict:
        obj = cast(Any, mapping)
        return {
            "id": str(obj.id),
            "module_id": str(obj.module_id),
            "role_port_id": str(obj.role_port_id),
            "interface_id": str(obj.interface_id),
            "created_ts": obj.created_ts.isoformat() if obj.created_ts else None,
        }

    def _enrich(self, mapping: dict) -> dict:
        mapping["interface_name"] = ""
        mapping["role_port_name"] = ""
        mapping["role_name"] = ""
        mapping["role_id"] = None
        with self.db_session.session() as db:
            iface = db.query(InterfaceObject).filter(InterfaceObject.id == UUID(mapping["interface_id"])).first()
            if iface:
                mapping["interface_name"] = iface.name

            port = db.query(RolePort).filter(RolePort.id == UUID(mapping["role_port_id"])).first()
            if port:
                mapping["role_port_name"] = port.name
                mapping["role_id"] = str(port.role_id)
                from models import ModuleRole
                role = db.query(ModuleRole).filter(ModuleRole.id == port.role_id).first()
                if role:
                    mapping["role_name"] = role.name
        return mapping

    def get_module_mappings(self, module_id: UUID) -> List[dict]:
        with self.db_session.session() as db:
            mappings = (
                db.query(InterfaceMapping)
                .filter(InterfaceMapping.module_id == module_id)
                .all()
            )
            return [self._enrich(self._to_dict(m)) for m in mappings]

    def _is_external_role_port(self, db: Session, module_id: UUID, port: RolePort) -> bool:
        row = db.execute(
            select(parent_child_module_role_assignment.c.role_id)
            .join(
                parent_child_module,
                parent_child_module.c.id == parent_child_module_role_assignment.c.parent_child_module_id,
            )
            .where(
                parent_child_module.c.child_id == module_id,
                parent_child_module_role_assignment.c.role_id == port.role_id,
            )
            .limit(1)
        ).first()
        return row is not None

    def create_mapping(self, module_id: UUID, role_port_id: UUID, interface_id: UUID) -> dict:
        with self.db_session.session() as db:
            module = db.query(Module).filter(Module.id == module_id).first()
            if not module:
                raise ValueError(f"Module with ID '{module_id}' not found")

            port = db.query(RolePort).filter(RolePort.id == role_port_id).first()
            if not port:
                raise ValueError(f"RolePort with ID '{role_port_id}' not found")
            if not self._is_external_role_port(db, module_id, port):
                raise ValueError("Порт не принадлежит внешней роли этого модуля")

            iface = db.query(InterfaceObject).filter(InterfaceObject.id == interface_id).first()
            if not iface:
                raise ValueError(f"InterfaceObject with ID '{interface_id}' not found")
            if iface.module_id != module_id:
                raise ValueError("Интерфейс не принадлежит указанному модулю")

            existing = (
                db.query(InterfaceMapping)
                .filter(
                    InterfaceMapping.module_id == module_id,
                    InterfaceMapping.role_port_id == role_port_id,
                    InterfaceMapping.interface_id == interface_id,
                )
                .first()
            )
            if existing:
                return self._enrich(self._to_dict(existing))

            mapping = InterfaceMapping(
                module_id=module_id,
                role_port_id=role_port_id,
                interface_id=interface_id,
            )
            db.add(mapping)
            db.commit()
            db.refresh(mapping)
            return self._enrich(self._to_dict(mapping))

    def delete_mapping(self, mapping_id: UUID, module_id: Optional[UUID] = None) -> bool:
        with self.db_session.session() as db:
            mapping = db.query(InterfaceMapping).filter(InterfaceMapping.id == mapping_id).first()
            if not mapping:
                return False
            if module_id is not None and cast(Any, mapping).module_id != module_id:
                return False
            db.delete(mapping)
            db.commit()
            return True

    def get_role_port_mappings(self, role_port_id: UUID) -> List[dict]:
        with self.db_session.session() as db:
            mappings = (
                db.query(InterfaceMapping)
                .filter(InterfaceMapping.role_port_id == role_port_id)
                .all()
            )
            return [self._enrich(self._to_dict(m)) for m in mappings]
