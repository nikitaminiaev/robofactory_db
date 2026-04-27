from typing import Optional
from uuid import UUID

from sqlalchemy import select

from . import BaseRepository
from models import Module, Stream
from models.associations import module_role_assignment, module_role_stream, module_stream


class StreamRepository(BaseRepository):
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
                stream.description = description

            existing = db.execute(
                select(module_role_stream.c.stream_id).where(
                    module_role_stream.c.module_id == module_id,
                    module_role_stream.c.source_role_id == source_role_id,
                    module_role_stream.c.target_role_id == target_role_id,
                )
            ).first()

            old_stream_id = existing.stream_id if existing else None
            if existing:
                db.execute(
                    module_role_stream.update()
                    .where(
                        module_role_stream.c.module_id == module_id,
                        module_role_stream.c.source_role_id == source_role_id,
                        module_role_stream.c.target_role_id == target_role_id,
                    )
                    .values(stream_id=stream.id)
                )
            else:
                db.execute(
                    module_role_stream.insert().values(
                        module_id=module_id,
                        source_role_id=source_role_id,
                        target_role_id=target_role_id,
                        stream_id=stream.id,
                    )
                )

            self._ensure_module_stream(db, module_id, stream.id)
            if old_stream_id and old_stream_id != stream.id:
                self._remove_unused_module_stream(db, module_id, old_stream_id)

            db.commit()
            db.refresh(stream)

            return {
                "id": str(stream.id),
                "name": stream.name,
                "description": stream.description,
                "source_role_id": str(source_role_id),
                "target_role_id": str(target_role_id),
            }

    def delete_module_role_stream(
        self,
        module_id: UUID,
        source_role_id: UUID,
        target_role_id: UUID,
    ) -> None:
        with self.db_session.session() as db:
            existing = db.execute(
                select(module_role_stream.c.stream_id).where(
                    module_role_stream.c.module_id == module_id,
                    module_role_stream.c.source_role_id == source_role_id,
                    module_role_stream.c.target_role_id == target_role_id,
                )
            ).first()
            if not existing:
                return

            db.execute(
                module_role_stream.delete().where(
                    module_role_stream.c.module_id == module_id,
                    module_role_stream.c.source_role_id == source_role_id,
                    module_role_stream.c.target_role_id == target_role_id,
                )
            )
            self._remove_unused_module_stream(db, module_id, existing.stream_id)
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
