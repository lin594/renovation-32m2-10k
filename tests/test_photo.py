from __future__ import annotations

import csv
from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from scripts import photo


class PhotoCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.catalog = self.root / "photos.csv"
        self.gallery = self.root / "README.md"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_rows(self, rows: list[dict[str, str]]) -> None:
        with self.catalog.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=photo.COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def row(self, **changes: str) -> dict[str, str]:
        result = {
            "id": "PHOTO-0001",
            "date": "2026-08-24",
            "stage": "before",
            "room": "living",
            "view": "overview",
            "caption": "装修前客厅全景",
            "file": "media/photos/living/2026-08-24-before-overview-01.jpg",
            "privacy_note": "人物照片已模糊",
            "source_sha256": "a" * 64,
        }
        result.update(changes)
        return result

    def test_catalog_validation_and_next_id(self) -> None:
        rows = [self.row()]
        photo.validate_catalog(rows)
        self.assertEqual(photo.next_id(rows), "PHOTO-0002")

    def test_duplicate_source_hash_is_rejected(self) -> None:
        rows = [
            self.row(),
            self.row(
                id="PHOTO-0002",
                file="media/photos/living/2026-08-24-before-detail-01.jpg",
                view="detail",
            ),
        ]
        with self.assertRaisesRegex(photo.PhotoError, "原图哈希重复"):
            photo.validate_catalog(rows)

    def test_invalid_room_stage_date_and_view_are_rejected(self) -> None:
        for changes in (
            {"room": "garage"},
            {"stage": "planned"},
            {"date": "2026-02-30"},
            {"view": "中文视角"},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(photo.PhotoError):
                    photo.validate_catalog([self.row(**changes)])

    def test_gallery_is_grouped_by_room_and_shows_missing_stages(self) -> None:
        self.write_rows([self.row()])
        first = photo.generate_gallery(self.catalog, self.gallery)
        second = photo.generate_gallery(self.catalog, self.gallery)
        self.assertEqual(first, second)
        self.assertIn("## 客厅", first)
        self.assertIn("### 装修前", first)
        self.assertIn("### 施工中\n\n_尚未拍摄。_", first)
        self.assertIn("living/2026-08-24-before-overview-01.jpg", first)
        self.assertIn("人物照片已模糊", first)

    def test_magick_command_requires_executable_and_valid_blur(self) -> None:
        with mock.patch("scripts.photo.shutil.which", return_value=None):
            with self.assertRaisesRegex(photo.PhotoError, "未找到ImageMagick"):
                photo.magick_command(Path("source.heic"), Path("out.jpg"), [])
        with mock.patch("scripts.photo.shutil.which", return_value="/usr/bin/magick"):
            with self.assertRaisesRegex(photo.PhotoError, "模糊区域格式错误"):
                photo.magick_command(Path("source.heic"), Path("out.jpg"), ["bad"])

    def test_dry_run_does_not_require_magick_or_write(self) -> None:
        self.write_rows([])
        source = self.root / "source.heic"
        source.write_bytes(b"original")
        arguments = mock.Mock(
            source=str(source),
            date="2026-08-27",
            stage="progress",
            room="bath",
            view="toilet-removal",
            caption="拆除蹲坑",
            privacy_note="",
            blur=[],
            dry_run=True,
        )
        with (
            mock.patch.object(photo, "ROOT", self.root),
            mock.patch.object(photo, "CATALOG", self.catalog),
        ):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(photo.import_photo(arguments), 0)
        self.assertEqual(photo.read_catalog(self.catalog), [])

    def test_public_jpeg_rejects_any_app1_metadata(self) -> None:
        image = self.root / "metadata.jpg"
        image.write_bytes(
            b"\xff\xd8"
            b"\xff\xe1\x00\x08XMP123"
            b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
            b"\xff\xd9"
        )
        with self.assertRaisesRegex(photo.PhotoError, "APP1"):
            photo.validate_public_jpeg(image)

    def test_import_failure_rolls_back_catalog_gallery_and_image(self) -> None:
        self.write_rows([])
        self.gallery.write_text("old gallery\n", encoding="utf-8")
        source = self.root / "source.heic"
        source.write_bytes(b"original")
        arguments = mock.Mock(
            source=str(source),
            date="2026-08-27",
            stage="progress",
            room="bath",
            view="detail",
            caption="施工细节",
            privacy_note="",
            blur=[],
            dry_run=False,
        )
        output = self.root / "media/photos/bath/2026-08-27-progress-detail-01.jpg"

        def fake_run(command: list[str], **_kwargs: object) -> None:
            if command[0] == "fake-magick":
                Path(command[-1]).write_bytes(
                    b"\xff\xd8"
                    b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
                    b"\xff\xd9"
                )
                return
            raise subprocess.CalledProcessError(1, command)

        with (
            mock.patch.object(photo, "ROOT", self.root),
            mock.patch.object(photo, "CATALOG", self.catalog),
            mock.patch.object(photo, "GALLERY", self.gallery),
            mock.patch.object(photo, "magick_command", side_effect=lambda _s, d, _b: ["fake-magick", str(d)]),
            mock.patch("scripts.photo.subprocess.run", side_effect=fake_run),
        ):
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(subprocess.CalledProcessError):
                    photo.import_photo(arguments)

        self.assertEqual(photo.read_catalog(self.catalog), [])
        self.assertEqual(self.gallery.read_text(encoding="utf-8"), "old gallery\n")
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
