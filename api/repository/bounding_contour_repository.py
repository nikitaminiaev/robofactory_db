from typing import Optional, Dict
from uuid import UUID
from pathlib import Path
from models import BoundingContour
from . import BaseRepository
from service.brep_storage import save_brep_file
from service.constants import BREP_FILES_PATH


class BoundingContourRepository(BaseRepository):

    def get_by_module_id(self, module_id: UUID) -> Optional[BoundingContour]:
        with self.db_session.session() as db:
            return db.query(BoundingContour).filter(
                BoundingContour.module_id == module_id
            ).first()

    def update_brep_files(self, module_id: UUID, brep_files: Dict[str, str]) -> BoundingContour:
        with self.db_session.session() as db:
            contour = db.query(BoundingContour).filter(
                BoundingContour.module_id == module_id
            ).first()
            if not contour:
                raise ValueError(f"BoundingContour for module {module_id} not found")
            current_files = contour.brep_files or {}
            contour.brep_files = {**current_files, **brep_files}

            db.add(contour)
            db.flush()
            db.commit()

            return contour

    def copy_bounding_contour(self, original_module_id: UUID, new_module_id: UUID) -> Optional[BoundingContour]:
        """
        Копирует bounding_contour для нового модуля, включая копирование BREP файлов.

        Args:
            original_module_id: UUID оригинального модуля
            new_module_id: UUID нового модуля

        Returns:
            Новый BoundingContour или None если оригинал не найден
        """
        with self.db_session.session() as db:
            original = db.query(BoundingContour).filter_by(module_id=original_module_id).first()
            if not original:
                return None

            brep_files = original.brep_files or {}
            new_brep_files: Dict[str, str] = {}
            base_path = Path(BREP_FILES_PATH)
            for filename, relative_path in brep_files.items():
                if not relative_path:
                    continue
                source_path = base_path / relative_path
                if not source_path.exists():
                    continue
                file_content = source_path.read_bytes()
                new_relative_path = save_brep_file(new_module_id, filename, file_content)
                new_brep_files[filename] = new_relative_path

            new_contour = BoundingContour(
                module_id=new_module_id,
                is_assembly=original.is_assembly,
                is_shell=original.is_shell,
                brep_files=new_brep_files,
                parent_id=None  # Для копии не копируем hierarchy
            )
            db.add(new_contour)
            db.commit()
            return new_contour