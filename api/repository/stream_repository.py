from typing import Any, Optional, cast
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import aliased

from . import BaseRepository
from models import Module, ModuleRole, Stream
from models.associations import (
    module_role_assignment,
    module_role_stream,
    module_stream,
    parent_child_module,
    parent_child_module_role_assignment,
)


class StreamRepository(BaseRepository):
    def search_streams(self, query: Optional[str] = None, limit: int = 20) -> list[dict]:
        with self.db_session.session() as db:
            stmt = db.query(Stream).order_by(Stream.name)
            if query:
                stmt = stmt.filter(Stream.name.ilike(f"%{query}%"))
            streams = stmt.limit(limit).all()

        return [
            {"id": str(stream.id), "name": stream.name, "description": stream.description}
            for stream in streams
        ]

    def get_module_role_streams(self, module_id: UUID) -> list[dict]:
        with self.db_session.session() as db:
            rows = db.execute(
                select(
                    module_role_stream.c.source_role_id,
                    module_role_stream.c.target_role_id,
                    Stream.id,
                    Stream.name,
                    Stream.description,
                )
                .join(Stream, Stream.id == module_role_stream.c.stream_id)
                .where(module_role_stream.c.module_id == module_id)
                .order_by(module_role_stream.c.source_role_id, module_role_stream.c.target_role_id)
            ).fetchall()

        return [
            {
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "source_role_id": str(row.source_role_id),
                "target_role_id": str(row.target_role_id),
            }
            for row in rows
        ]

    def get_external_role_streams(self, child_id: UUID) -> list[dict]:
        external_roles = (
            select(
                parent_child_module.c.parent_id.label("parent_module_id"),
                parent_child_module_role_assignment.c.role_id.label("external_role_id"),
            )
            .join(
                parent_child_module_role_assignment,
                parent_child_module_role_assignment.c.parent_child_module_id == parent_child_module.c.id,
            )
            .where(parent_child_module.c.child_id == child_id)
            .subquery()
        )
        source_role = aliased(ModuleRole)
        target_role = aliased(ModuleRole)
        external_role = aliased(ModuleRole)

        with self.db_session.session() as db:
            rows = db.execute(
                select(
                    external_roles.c.parent_module_id,
                    external_roles.c.external_role_id,
                    Module.name.label("parent_module_name"),
                    module_role_stream.c.source_role_id,
                    source_role.name.label("source_role_name"),
                    module_role_stream.c.target_role_id,
                    target_role.name.label("target_role_name"),
                    Stream.id,
                    Stream.name,
                    Stream.description,
                    external_role.name.label("external_role_name"),
                )
                .join(Module, Module.id == external_roles.c.parent_module_id)
                .join(
                    module_role_stream,
                    module_role_stream.c.module_id == external_roles.c.parent_module_id,
                )
                .join(Stream, Stream.id == module_role_stream.c.stream_id)
                .join(source_role, source_role.id == module_role_stream.c.source_role_id)
                .join(target_role, target_role.id == module_role_stream.c.target_role_id)
                .join(external_role, external_role.id == external_roles.c.external_role_id)
                .where(
                    or_(
                        module_role_stream.c.source_role_id == external_roles.c.external_role_id,
                        module_role_stream.c.target_role_id == external_roles.c.external_role_id,
                    )
                )
                .order_by(Module.name, source_role.name, target_role.name, Stream.name)
            ).fetchall()

        streams_by_key: dict[tuple, dict] = {}
        for row in rows:
            key = (
                row.parent_module_id,
                row.source_role_id,
                row.target_role_id,
                row.id,
            )
            stream = streams_by_key.get(key)
            external_role_data = {
                "id": str(row.external_role_id),
                "name": row.external_role_name,
            }
            if stream:
                if external_role_data not in stream["external_roles"]:
                    stream["external_roles"].append(external_role_data)
                continue

            streams_by_key[key] = {
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "parent_module_id": str(row.parent_module_id),
                "parent_module_name": row.parent_module_name,
                "source_role_id": str(row.source_role_id),
                "source_role_name": row.source_role_name,
                "target_role_id": str(row.target_role_id),
                "target_role_name": row.target_role_name,
                "external_roles": [external_role_data],
            }

        return list(streams_by_key.values())

    def upsert_module_role_stream(
        self,
        module_id: UUID,
        source_role_id: UUID,
        target_role_id: UUID,
        name: str,
        description: Optional[str],
    ) -> dict:
        with self.db_session.session() as db:
            module = db.query(Module).filter(Module.id == module_id).first()
            if not module:
                raise ValueError(f"Модуль с ID '{module_id}' не найден")

            self._ensure_roles_belong_to_module(db, module_id, source_role_id, target_role_id)
            stream = db.query(Stream).filter(Stream.name == name).first()
            if not stream:
                stream = Stream(name=name, description=description)
                db.add(stream)
                db.flush()
            elif description is not None:
                cast(Any, stream).description = description

            stream_obj = cast(Any, stream)
            existing = db.execute(
                select(module_role_stream.c.stream_id).where(
                    module_role_stream.c.module_id == module_id,
                    module_role_stream.c.source_role_id == source_role_id,
                    module_role_stream.c.target_role_id == target_role_id,
                    module_role_stream.c.stream_id == stream_obj.id,
                )
            ).first()

            if not existing:
                db.execute(
                    module_role_stream.insert().values(
                        module_id=module_id,
                        source_role_id=source_role_id,
                        target_role_id=target_role_id,
                        stream_id=stream_obj.id,
                    )
                )

            self._ensure_module_stream(db, module_id, stream_obj.id)

            db.commit()
            db.refresh(stream)

            return {
                "id": str(stream_obj.id),
                "name": stream_obj.name,
                "description": stream_obj.description,
                "source_role_id": str(source_role_id),
                "target_role_id": str(target_role_id),
            }

    def delete_module_role_stream(
        self,
        module_id: UUID,
        source_role_id: UUID,
        target_role_id: UUID,
        stream_id: Optional[UUID] = None,
    ) -> None:
        with self.db_session.session() as db:
            where_clause = [
                module_role_stream.c.module_id == module_id,
                module_role_stream.c.source_role_id == source_role_id,
                module_role_stream.c.target_role_id == target_role_id,
            ]
            if stream_id:
                where_clause.append(module_role_stream.c.stream_id == stream_id)

            existing_rows = db.execute(
                select(module_role_stream.c.stream_id).where(*where_clause)
            ).fetchall()
            if not existing_rows:
                return

            db.execute(
                module_role_stream.delete().where(*where_clause)
            )
            for row in existing_rows:
                self._remove_unused_module_stream(db, module_id, row.stream_id)
            db.commit()

    def _ensure_roles_belong_to_module(self, db, module_id: UUID, source_role_id: UUID, target_role_id: UUID) -> None:
        role_ids = {
            row.role_id
            for row in db.execute(
                select(module_role_assignment.c.role_id).where(
                    module_role_assignment.c.module_id == module_id,
                    module_role_assignment.c.role_id.in_([source_role_id, target_role_id]),
                )
            ).fetchall()
        }
        if source_role_id in role_ids and target_role_id in role_ids:
            return
        raise ValueError("Обе роли должны быть назначены текущему модулю")

    def _ensure_module_stream(self, db, module_id: UUID, stream_id: UUID) -> None:
        existing = db.execute(
            select(module_stream.c.stream_id).where(
                module_stream.c.module_id == module_id,
                module_stream.c.stream_id == stream_id,
            )
        ).first()
        if existing:
            return
        db.execute(module_stream.insert().values(module_id=module_id, stream_id=stream_id))

    def _remove_unused_module_stream(self, db, module_id: UUID, stream_id: UUID) -> None:
        used = db.execute(
            select(module_role_stream.c.stream_id).where(
                module_role_stream.c.module_id == module_id,
                module_role_stream.c.stream_id == stream_id,
            )
        ).first()
        if used:
            return
        db.execute(
            module_stream.delete().where(
                module_stream.c.module_id == module_id,
                module_stream.c.stream_id == stream_id,
            )
        )
