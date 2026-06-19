import tempfile
import unittest
from pathlib import Path

from PIL import Image

from bulk_edit_app import EditOptions, process_batch


class BulkEditAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.input_dir = self.base / "input"
        self.output_dir = self.base / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_image(self, path: Path, size=(100, 80), color=(10, 100, 200), fmt="PNG"):
        img = Image.new("RGB", size=size, color=color)
        img.save(path, format=fmt)

    def test_preview_mode_does_not_write_outputs(self):
        self._create_image(self.input_dir / "a.png")
        self._create_image(self.input_dir / "b.png")
        options = EditOptions(rename_pattern="{name}_edited_{index}", resize=(50, 50))

        result = process_batch(self.input_dir, self.output_dir, options, preview=True, max_batch_size=10)

        self.assertEqual(result["processed"], 2)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(len(result["planned_outputs"]), 2)
        self.assertEqual(len(list(self.output_dir.iterdir())), 0)

    def test_resize_rotate_and_format_conversion(self):
        self._create_image(self.input_dir / "source.png", size=(120, 60))
        options = EditOptions(resize=(60, 40), rotate=90, output_format="jpeg", quality=85, rename_pattern="{name}_{index}")

        result = process_batch(self.input_dir, self.output_dir, options, preview=False, max_batch_size=10)

        self.assertEqual(result["processed"], 1)
        output_file = next(self.output_dir.iterdir())
        self.assertEqual(output_file.suffix, ".jpg")
        with Image.open(output_file) as out:
            self.assertEqual(out.size, (40, 60))

    def test_corrupted_file_is_skipped(self):
        self._create_image(self.input_dir / "valid.png")
        (self.input_dir / "broken.png").write_text("not an image", encoding="utf-8")
        options = EditOptions(rename_pattern="{name}_{index}")

        result = process_batch(self.input_dir, self.output_dir, options, preview=False, max_batch_size=10)

        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(len(result["errors"]), 1)

    def test_max_batch_size_guard(self):
        self._create_image(self.input_dir / "1.png")
        self._create_image(self.input_dir / "2.png")
        options = EditOptions()
        with self.assertRaises(ValueError):
            process_batch(self.input_dir, self.output_dir, options, preview=False, max_batch_size=1)


if __name__ == "__main__":
    unittest.main()
