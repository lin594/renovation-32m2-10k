#!/usr/bin/env python3
"""Import optimized renovation photos and generate the public room gallery."""

from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import html
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "photos.csv"
MEDIA_ROOT = ROOT / "media" / "photos"
GALLERY = MEDIA_ROOT / "README.md"
COLUMNS = (
    "id",
    "date",
    "stage",
    "room",
    "view",
    "caption",
    "file",
    "privacy_note",
    "source_sha256",
)
STAGES = {"before": "装修前", "progress": "施工中", "after": "完工"}
ROOMS = {
    "bedroom": ("卧室", "bedroom"),
    "kitchen": ("厨房", "kitchen"),
    "living": ("客厅", "living"),
    "hall_a": ("走廊A（玄关）", "hall-a"),
    "hall_b": ("走廊B", "hall-b"),
    "balcony": ("转角阳台", "balcony"),
    "bath": ("卫生间", "bath"),
}
PHOTO_ID = re.compile(r"^PHOTO-(\d{4})$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BLUR_GEOMETRY = re.compile(r"^(\d+)x(\d+)\+(\d+)\+(\d+)$")
MAX_EDGE = 1800
MAX_BYTES = 900 * 1024


class PhotoError(ValueError):
    """A user-fixable catalog or import error."""


def sha256_file(source: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_catalog(catalog: Path | None = None) -> list[dict[str, str]]:
    catalog = catalog or CATALOG
    with catalog.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise PhotoError("data/photos.csv 表头不符合约定")
        return list(reader)


def validate_catalog(rows: list[dict[str, str]]) -> None:
    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    seen_hashes: set[str] = set()
    for index, row in enumerate(rows, start=2):
        photo_id = row.get("id", "").strip()
        if not PHOTO_ID.fullmatch(photo_id):
            raise PhotoError(f"photos.csv 第 {index} 行 id 格式错误")
        if photo_id in seen_ids:
            raise PhotoError(f"photos.csv 第 {index} 行 id 重复：{photo_id}")
        seen_ids.add(photo_id)
        try:
            date.fromisoformat(row.get("date", ""))
        except ValueError as exc:
            raise PhotoError(f"photos.csv 第 {index} 行日期无效") from exc
        if row.get("stage") not in STAGES:
            raise PhotoError(f"photos.csv 第 {index} 行 stage 无效")
        if row.get("room") not in ROOMS:
            raise PhotoError(f"photos.csv 第 {index} 行 room 无效")
        if not SLUG.fullmatch(row.get("view", "")):
            raise PhotoError(f"photos.csv 第 {index} 行 view 必须是英文短横线 slug")
        if not row.get("caption", "").strip():
            raise PhotoError(f"photos.csv 第 {index} 行 caption 不能为空")
        relative_file = row.get("file", "")
        expected_prefix = f"media/photos/{ROOMS[row['room']][1]}/"
        if not relative_file.startswith(expected_prefix) or not relative_file.endswith(".jpg"):
            raise PhotoError(f"photos.csv 第 {index} 行 file 与房间或格式不匹配")
        if relative_file in seen_files:
            raise PhotoError(f"photos.csv 第 {index} 行 file 重复：{relative_file}")
        seen_files.add(relative_file)
        source_hash = row.get("source_sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", source_hash):
            raise PhotoError(f"photos.csv 第 {index} 行 source_sha256 无效")
        if source_hash in seen_hashes:
            raise PhotoError(f"photos.csv 第 {index} 行原图哈希重复")
        seen_hashes.add(source_hash)


def next_id(rows: list[dict[str, str]]) -> str:
    numbers = [int(match.group(1)) for row in rows if (match := PHOTO_ID.fullmatch(row["id"]))]
    return f"PHOTO-{max(numbers, default=0) + 1:04d}"


def next_output_path(
    rows: list[dict[str, str]], photo_date: str, stage: str, room: str, view: str
) -> Path:
    folder = ROOMS[room][1]
    prefix = f"{photo_date}-{stage}-{view}-"
    existing = {
        Path(row["file"]).name
        for row in rows
        if row["file"].startswith(f"media/photos/{folder}/")
    }
    sequence = 1
    while f"{prefix}{sequence:02d}.jpg" in existing:
        sequence += 1
    return Path("media") / "photos" / folder / f"{prefix}{sequence:02d}.jpg"


def jpeg_dimensions(source: Path) -> tuple[int, int]:
    data = source.read_bytes()
    if not data.startswith(b"\xff\xd8"):
        raise PhotoError(f"不是有效JPEG：{source}")
    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            break
        length = int.from_bytes(data[offset : offset + 2], "big")
        if length < 2 or offset + length > len(data):
            break
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            return width, height
        offset += length
    raise PhotoError(f"无法读取JPEG尺寸：{source}")


def jpeg_has_app1(source: Path) -> bool:
    """Return whether a JPEG contains any APP1 segment (EXIF/XMP metadata)."""
    data = source.read_bytes()
    if not data.startswith(b"\xff\xd8"):
        raise PhotoError(f"不是有效JPEG：{source}")
    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker == 0xDA:  # Start of scan: following bytes are compressed image data.
            return False
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            return False
        length = int.from_bytes(data[offset : offset + 2], "big")
        if marker == 0xE1:
            return True
        if length < 2 or offset + length > len(data):
            return False
        offset += length
    return False


def validate_public_jpeg(source: Path) -> None:
    if source.stat().st_size > MAX_BYTES:
        raise PhotoError(f"照片超过900KB：{source}")
    width, height = jpeg_dimensions(source)
    if max(width, height) > MAX_EDGE:
        raise PhotoError(f"照片最长边超过1800px：{source}")
    if jpeg_has_app1(source):
        raise PhotoError(f"照片仍包含APP1元数据：{source}")


def write_catalog(rows: list[dict[str, str]], catalog: Path | None = None) -> None:
    catalog = catalog or CATALOG
    catalog.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=catalog.parent, delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    os.replace(temporary, catalog)


def gallery_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "<!-- 本文件由 scripts/photo.py gallery 自动生成，请修改 data/photos.csv 或使用导入命令。 -->",
        "# 现场照片档案",
        "",
        "照片按房间组织，并在房间内依次展示装修前、施工中和完工阶段。尚未拍摄的阶段会明确留空，不用效果图冒充实景。",
        "",
        "公开照片均已压缩并移除元数据；原始 HEIC 只保存在本地 `.local/photos-original/`。新增照片请参考[人类编辑指南](../../docs/editing-guide.md)。",
        "",
    ]
    for room_id, (room_name, folder) in ROOMS.items():
        room_rows = [row for row in rows if row["room"] == room_id]
        if not room_rows:
            continue
        lines.extend([f"## {room_name}", ""])
        for stage, stage_name in STAGES.items():
            stage_rows = sorted(
                (row for row in room_rows if row["stage"] == stage),
                key=lambda row: (row["date"], row["id"]),
            )
            lines.extend([f"### {stage_name}", ""])
            if not stage_rows:
                lines.extend(["_尚未拍摄。_", ""])
                continue
            for row in stage_rows:
                image_name = Path(row["file"]).name
                alt = html.escape(f"{room_name}｜{stage_name}｜{row['caption']}", quote=True)
                lines.extend(
                    [
                        f'<img src="{folder}/{image_name}" alt="{alt}" width="520">',
                        "",
                        f"{row['date']} · `{row['id']}` · {row['caption']}",
                        "",
                    ]
                )
                if row.get("privacy_note", "").strip():
                    lines.extend([f"> 隐私处理：{row['privacy_note']}", ""])
    lines.extend(
        [
            "## 后续拍摄约定",
            "",
            "尽量站在同一门口、使用相近焦段和方向拍摄；先记录全景，再补充墙面、管线、柜体和收口细节，以便形成可信的前后对比。",
            "",
        ]
    )
    return "\n".join(lines)


def generate_gallery(
    catalog: Path | None = None, gallery: Path | None = None
) -> str:
    catalog = catalog or CATALOG
    gallery = gallery or GALLERY
    rows = read_catalog(catalog)
    validate_catalog(rows)
    content = gallery_markdown(rows)
    gallery.parent.mkdir(parents=True, exist_ok=True)
    gallery.write_text(content, encoding="utf-8")
    return content


def magick_command(source: Path, destination: Path, blurs: list[str]) -> list[str]:
    executable = shutil.which("magick")
    if not executable:
        raise PhotoError("未找到ImageMagick命令 magick；请先安装后再导入照片")
    command = [
        executable,
        str(source),
        "-auto-orient",
        "-resize",
        "1800x1800>",
        "-colorspace",
        "sRGB",
    ]
    for geometry in blurs:
        match = BLUR_GEOMETRY.fullmatch(geometry)
        if not match:
            raise PhotoError(f"模糊区域格式错误：{geometry}")
        _width, _height, x, y = match.groups()
        command.extend(
            [
                "(",
                "+clone",
                "-crop",
                geometry,
                "-blur",
                "0x24",
                ")",
                "-geometry",
                f"+{x}+{y}",
                "-composite",
            ]
        )
    command.extend(
        [
            "-strip",
            "-sampling-factor",
            "4:2:0",
            "-interlace",
            "Plane",
            "-quality",
            "82",
            str(destination),
        ]
    )
    return command


def import_photo(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        raise PhotoError(f"找不到原图：{source}")
    try:
        date.fromisoformat(args.date)
    except ValueError as exc:
        raise PhotoError("日期必须使用 YYYY-MM-DD") from exc
    if args.stage not in STAGES:
        raise PhotoError("stage 必须是 before、progress 或 after")
    if args.room not in ROOMS:
        raise PhotoError(f"room 必须是：{', '.join(ROOMS)}")
    if not SLUG.fullmatch(args.view):
        raise PhotoError("view 必须是小写英文、数字和短横线")
    if not args.caption.strip():
        raise PhotoError("caption 不能为空")
    for geometry in args.blur:
        if not BLUR_GEOMETRY.fullmatch(geometry):
            raise PhotoError(f"模糊区域格式错误：{geometry}")

    rows = read_catalog()
    validate_catalog(rows)
    source_hash = sha256_file(source)
    if any(row["source_sha256"] == source_hash for row in rows):
        raise PhotoError("该原图已经导入，source_sha256 重复")
    relative_output = next_output_path(rows, args.date, args.stage, args.room, args.view)
    destination = ROOT / relative_output
    if destination.exists():
        raise PhotoError(f"目标文件已存在：{relative_output}")
    row = {
        "id": next_id(rows),
        "date": args.date,
        "stage": args.stage,
        "room": args.room,
        "view": args.view,
        "caption": args.caption.strip(),
        "file": relative_output.as_posix(),
        "privacy_note": args.privacy_note.strip(),
        "source_sha256": source_hash,
    }
    print("将导入：", row)
    if args.dry_run:
        return 0

    catalog_before = CATALOG.read_bytes()
    gallery_before = GALLERY.read_bytes() if GALLERY.exists() else None
    destination_created = False
    try:
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_output = Path(temporary_dir) / "photo.jpg"
            subprocess.run(magick_command(source, temporary_output, args.blur), check=True)
            validate_public_jpeg(temporary_output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temporary_output, destination)
            destination_created = True
        rows.append(row)
        validate_catalog(rows)
        write_catalog(rows)
        generate_gallery()
        subprocess.run(["make", "check"], cwd=ROOT, check=True)
    except Exception:
        CATALOG.write_bytes(catalog_before)
        if gallery_before is None:
            GALLERY.unlink(missing_ok=True)
        else:
            GALLERY.write_bytes(gallery_before)
        if destination_created:
            destination.unlink(missing_ok=True)
        raise
    print(f"已生成：{relative_output}")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    importer = subparsers.add_parser("import", help="导入一张照片并刷新图库")
    importer.add_argument("source")
    importer.add_argument("--date", required=True)
    importer.add_argument("--stage", required=True, choices=tuple(STAGES))
    importer.add_argument("--room", required=True, choices=tuple(ROOMS))
    importer.add_argument("--view", required=True)
    importer.add_argument("--caption", required=True)
    importer.add_argument("--privacy-note", default="")
    importer.add_argument("--blur", action="append", default=[])
    importer.add_argument("--dry-run", action="store_true")
    subparsers.add_parser("gallery", help="从data/photos.csv重建图库")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "gallery":
            generate_gallery()
            print(f"Generated {GALLERY.relative_to(ROOT)}")
            return 0
        return import_photo(args)
    except (PhotoError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
