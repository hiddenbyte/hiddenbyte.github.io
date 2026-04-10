import io
import json
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
import imgbb_upload


class TestParseImgbbResponse(unittest.TestCase):
    def test_success_returns_url(self):
        data = {"success": True, "data": {"url": "https://i.ibb.co/abc/photo.jpg"}}
        result = imgbb_upload.parse_imgbb_response(data)
        self.assertEqual(result, "https://i.ibb.co/abc/photo.jpg")

    def test_success_false_returns_none(self):
        data = {"success": False, "data": {"url": "https://i.ibb.co/abc/photo.jpg"}}
        result = imgbb_upload.parse_imgbb_response(data)
        self.assertIsNone(result)

    def test_missing_success_key_returns_none(self):
        data = {"data": {"url": "https://i.ibb.co/abc/photo.jpg"}}
        result = imgbb_upload.parse_imgbb_response(data)
        self.assertIsNone(result)

    def test_success_zero_returns_none(self):
        # API may return 0 instead of False
        data = {"success": 0, "data": {"url": "https://i.ibb.co/abc/photo.jpg"}}
        result = imgbb_upload.parse_imgbb_response(data)
        self.assertIsNone(result)

    def test_success_one_returns_url(self):
        # API may return 1 instead of True
        data = {"success": 1, "data": {"url": "https://i.ibb.co/abc/photo.jpg"}}
        result = imgbb_upload.parse_imgbb_response(data)
        self.assertEqual(result, "https://i.ibb.co/abc/photo.jpg")

    def test_empty_dict_returns_none(self):
        result = imgbb_upload.parse_imgbb_response({})
        self.assertIsNone(result)

    def test_url_is_returned_verbatim(self):
        url = "https://i.ibb.co/xyz/image-with-dashes_and_underscores.png"
        data = {"success": True, "data": {"url": url}}
        result = imgbb_upload.parse_imgbb_response(data)
        self.assertEqual(result, url)


class TestMain(unittest.TestCase):
    def _run_main_with_stdin(self, payload):
        stdin_data = json.dumps(payload)
        with patch("sys.stdin", io.TextIOWrapper(io.BytesIO(stdin_data.encode()))):
            imgbb_upload.main()

    def test_success_prints_url(self):
        data = {"success": True, "data": {"url": "https://i.ibb.co/abc/photo.jpg"}}
        stdin_data = json.dumps(data)
        with patch("sys.stdin", io.TextIOWrapper(io.BytesIO(stdin_data.encode()))), \
             patch("builtins.print") as mock_print:
            imgbb_upload.main()
            mock_print.assert_called_once_with("https://i.ibb.co/abc/photo.jpg")

    def test_failure_exits_1(self):
        data = {"success": False}
        stdin_data = json.dumps(data)
        with patch("sys.stdin", io.TextIOWrapper(io.BytesIO(stdin_data.encode()))):
            with self.assertRaises(SystemExit) as ctx:
                imgbb_upload.main()
            self.assertEqual(ctx.exception.code, 1)

    def test_failure_prints_to_stderr(self):
        data = {"success": False, "error": {"message": "Bad request"}}
        stdin_data = json.dumps(data)
        with patch("sys.stdin", io.TextIOWrapper(io.BytesIO(stdin_data.encode()))), \
             patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                imgbb_upload.main()
            self.assertIn("Upload failed", mock_stderr.getvalue())

    def test_missing_success_key_exits_1(self):
        data = {"data": {"url": "https://i.ibb.co/abc/photo.jpg"}}
        stdin_data = json.dumps(data)
        with patch("sys.stdin", io.TextIOWrapper(io.BytesIO(stdin_data.encode()))):
            with self.assertRaises(SystemExit) as ctx:
                imgbb_upload.main()
            self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
