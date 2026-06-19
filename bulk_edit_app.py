from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, UnidentifiedImageError

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
OUTPUT_FORMATS = {
    "jpeg": ("JPEG", ".jpg"),
    "png": ("PNG", ".png"),
    "webp": ("WEBP", ".webp"),
    "bmp": ("BMP", ".bmp"),
    "tiff": ("TIFF", ".tiff"),
}
DEFAULT_MAX_BATCH_SIZE = 1000
WATERMARK_PADDING = 10
WATERMARK_ESTIMATED_CHAR_WIDTH = 8
WATERMARK_TEXT_HEIGHT = 20


@dataclass
class EditOptions:
    resize: Optional[Tuple[int, int]] = None
    crop: Optional[Tuple[int, int, int, int]] = None
    rotate: int = 0
    watermark: Optional[str] = None
    output_format: Optional[str] = None
    quality: Optional[int] = None
    rename_pattern: str = "{name}_{index}"


def discover_images(input_dir: Path) -> List[Path]:
    files = [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files)


def parse_resize(value: str) -> Tuple[int, int]:
    try:
        width, height = value.lower().split("x", 1)
        return int(width), int(height)
    except (ValueError, AttributeError) as exc:
        raise argparse.ArgumentTypeError("Resize must be formatted as WIDTHxHEIGHT, e.g. 800x600.") from exc


def parse_crop(value: str) -> Tuple[int, int, int, int]:
    try:
        left, top, right, bottom = [int(part.strip()) for part in value.split(",")]
        return left, top, right, bottom
    except (ValueError, AttributeError) as exc:
        raise argparse.ArgumentTypeError("Crop must be formatted as left,top,right,bottom.") from exc


def apply_edits(image: Image.Image, options: EditOptions) -> Image.Image:
    edited = image.copy()
    if options.resize:
        edited = edited.resize(options.resize)
    if options.crop:
        edited = edited.crop(options.crop)
    if options.rotate:
        edited = edited.rotate(options.rotate, expand=True)
    if options.watermark:
        draw = ImageDraw.Draw(edited)
        width, height = edited.size
        x = max(WATERMARK_PADDING, width - (len(options.watermark) * WATERMARK_ESTIMATED_CHAR_WIDTH) - WATERMARK_PADDING)
        y = max(WATERMARK_PADDING, height - WATERMARK_TEXT_HEIGHT)
        draw.text((x, y), options.watermark, fill=(255, 255, 255))
    return edited


def build_output_name(source: Path, index: int, pattern: str, extension: str) -> str:
    name = pattern.format(name=source.stem, index=index)
    return f"{name}{extension}"


def process_batch(
    input_dir: Path,
    output_dir: Path,
    options: EditOptions,
    preview: bool = False,
    max_batch_size: int = DEFAULT_MAX_BATCH_SIZE,
):
    images = discover_images(input_dir)
    if len(images) > max_batch_size:
        raise ValueError(f"Batch size {len(images)} exceeds configured max of {max_batch_size}.")

    if options.output_format:
        output_key = options.output_format.lower()
        output_format, output_ext = OUTPUT_FORMATS[output_key]
    else:
        output_format = None
        output_ext = None

    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {"processed": 0, "failed": 0, "errors": [], "planned_outputs": []}

    for index, image_path in enumerate(images, start=1):
        try:
            with Image.open(image_path) as image:
                source_format = image.format or "PNG"
                current_ext = image_path.suffix.lower()
                if output_format is None:
                    save_format = source_format
                    final_ext = current_ext if current_ext in SUPPORTED_EXTENSIONS else ".png"
                else:
                    save_format = output_format
                    final_ext = output_ext

                output_name = build_output_name(image_path, index, options.rename_pattern, final_ext)
                destination = output_dir / output_name
                summary["planned_outputs"].append(str(destination))

                if preview:
                    summary["processed"] += 1
                    continue

                edited = apply_edits(image, options)
                save_kwargs = {}
                if options.quality is not None and save_format in {"JPEG", "WEBP"}:
                    save_kwargs["quality"] = options.quality
                edited.save(destination, format=save_format, **save_kwargs)
                summary["processed"] += 1
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            summary["failed"] += 1
            summary["errors"].append(f"{image_path.name}: {exc}")

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bulk edit pictures in a folder.")
    parser.add_argument("--input-dir", required=True, type=Path, help="Input folder with images.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Output folder for edited images.")
    parser.add_argument("--preview", action="store_true", help="Show planned outputs without writing files.")
    parser.add_argument("--resize", type=parse_resize, help="Resize as WIDTHxHEIGHT (example: 800x600).")
    parser.add_argument("--crop", type=parse_crop, help="Crop as left,top,right,bottom.")
    parser.add_argument("--rotate", type=int, default=0, help="Rotate degrees clockwise.")
    parser.add_argument("--watermark", type=str, help="Watermark text.")
    parser.add_argument("--format", choices=sorted(OUTPUT_FORMATS.keys()), help="Output format override.")
    parser.add_argument("--quality", type=int, help="Quality value (recommended 1-95 for JPEG/WEBP).")
    parser.add_argument("--rename-pattern", type=str, default="{name}_{index}", help="Rename pattern tokens: {name} {index}.")
    parser.add_argument("--max-batch-size", type=int, default=DEFAULT_MAX_BATCH_SIZE, help="Maximum images per run.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.input_dir.exists() or not args.input_dir.is_dir():
        parser.error("--input-dir must point to an existing directory.")
    if args.quality is not None and not (1 <= args.quality <= 100):
        parser.error("--quality must be between 1 and 100.")

    options = EditOptions(
        resize=args.resize,
        crop=args.crop,
        rotate=args.rotate,
        watermark=args.watermark,
        output_format=args.format,
        quality=args.quality,
        rename_pattern=args.rename_pattern,
    )

    summary = process_batch(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        options=options,
        preview=args.preview,
        max_batch_size=args.max_batch_size,
    )

    mode = "PREVIEW" if args.preview else "PROCESS"
    print(f"[{mode}] processed={summary['processed']} failed={summary['failed']}")
    if summary["planned_outputs"]:
        for item in summary["planned_outputs"]:
            print(f"- {item}")
    if summary["errors"]:
        print("Errors:")
        for err in summary["errors"]:
            print(f"- {err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
