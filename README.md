# Bulk Edit Picture App

This repository now includes an MVP batch image editing application with documented scope, architecture, and acceptance criteria.

## 1) Scope

- **Target platform:** Desktop/CLI (cross-platform via Python 3.10+).
- **Supported input formats:** `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`.
- **Supported output formats:** `jpeg`, `png`, `webp`, `bmp`, `tiff`.
- **Maximum batch size (default):** `1000` images per run (configurable with CLI flag).

## 2) Core Features

- Bulk resize
- Bulk crop
- Bulk rotate
- Bulk rename using pattern tokens (`{name}`, `{index}`)
- Bulk watermark text overlay
- Format conversion
- JPEG/WebP quality/compression control (where supported)

## 3) Workflow

1. Import source folder (`--input-dir`)
2. Optional preview (`--preview`) to inspect planned outputs before writing files
3. Apply same edit pipeline to all discovered images
4. Export to destination folder (`--output-dir`) using naming rules (`--rename-pattern`)

## 4) Non-Functional Requirements

- **Performance:** Single pass processing per image.
- **Memory limits:** One-image-at-a-time processing; no full-batch in-memory buffering.
- **Offline support:** Fully local execution with no network dependency.
- **Robustness:** Corrupted/unreadable files are skipped and reported, not fatal to full batch.

## 5) Architecture & Stack

- **Language/runtime:** Python 3.10+
- **Imaging library:** Pillow
- **App model:** CLI entry point with pure processing functions for testability

## 6) MVP and Phased Enhancements

### MVP (implemented)
- Folder import and image discovery
- Preview mode
- Resize/crop/rotate/watermark/convert/quality
- Export naming rules
- Corrupted file handling and processing summary

### Next phases
- Saved presets
- Undo/rollback support
- Metadata editing
- Cloud storage integrations

## 7) Acceptance Criteria & Test Scenarios

### Acceptance criteria
- App rejects batches larger than configured max.
- App processes all valid images and skips corrupted images with explicit error messages.
- Resize, crop, rotate, rename, format conversion, and quality options are applied consistently across the batch.
- Preview mode produces an execution plan and does not write output files.
- Export naming pattern is honored for all processed files.

### Test scenarios
- Batch resize and rotate updates dimensions/orientation as expected.
- Format conversion from PNG to JPEG writes `.jpg` outputs.
- Rename pattern produces deterministic output names including index token.
- Corrupted input files do not terminate the run; summary reports them as failures.
- Batch size guard raises an error when input count exceeds max.

## Usage

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run preview:

```bash
python bulk_edit_app.py --input-dir ./in --output-dir ./out --resize 800x600 --preview
```

Run processing:

```bash
python bulk_edit_app.py \
  --input-dir ./in \
  --output-dir ./out \
  --resize 800x600 \
  --rotate 90 \
  --watermark "Sample" \
  --format jpeg \
  --quality 85 \
  --rename-pattern "{name}_edited_{index}"
```

Run tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```