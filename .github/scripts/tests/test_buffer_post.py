import io
import json
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
import buffer_post


class TestBuildCaption(unittest.TestCase):
    def test_combines_title_and_url(self):
        result = buffer_post.build_caption("My Post", "https://example.com/my-post")
        self.assertEqual(result, "My Post\n\nhttps://example.com/my-post")

    def test_empty_strings(self):
        result = buffer_post.build_caption("", "")
        self.assertEqual(result, "\n\n")

    def test_preserves_special_characters(self):
        result = buffer_post.build_caption("Post: 10 años", "https://example.com/post")
        self.assertEqual(result, "Post: 10 años\n\nhttps://example.com/post")


class TestBuildMutation(unittest.TestCase):
    def test_feed_uses_create_feed_post(self):
        mutation = buffer_post.build_mutation("feed")
        self.assertIn("CreateFeedPost", mutation)
        self.assertNotIn("CreateStoryPost", mutation)

    def test_story_uses_create_story_post(self):
        mutation = buffer_post.build_mutation("story")
        self.assertIn("CreateStoryPost", mutation)
        self.assertNotIn("CreateFeedPost", mutation)

    def test_mutation_contains_required_fields(self):
        for post_type in ("feed", "story"):
            with self.subTest(post_type=post_type):
                mutation = buffer_post.build_mutation(post_type)
                self.assertIn("createPost", mutation)
                self.assertIn("CreatePostInput", mutation)
                self.assertIn("PostActionSuccess", mutation)
                self.assertIn("MutationError", mutation)
                self.assertIn("id", mutation)
                self.assertIn("dueAt", mutation)


class TestBuildVariables(unittest.TestCase):
    def setUp(self):
        self.channel_id = "chan_123"
        self.caption = "Hello\n\nhttps://example.com"
        self.img_url = "https://img.example.com/photo.jpg"

    def test_feed_type_in_metadata(self):
        variables = buffer_post.build_variables("feed", self.channel_id, self.caption, self.img_url)
        self.assertEqual(variables["input"]["metadata"]["instagram"]["type"], "feed")

    def test_story_type_in_metadata(self):
        variables = buffer_post.build_variables("story", self.channel_id, self.caption, self.img_url)
        self.assertEqual(variables["input"]["metadata"]["instagram"]["type"], "story")

    def test_channel_id_set(self):
        variables = buffer_post.build_variables("feed", self.channel_id, self.caption, self.img_url)
        self.assertEqual(variables["input"]["channelId"], self.channel_id)

    def test_caption_set_as_text(self):
        variables = buffer_post.build_variables("feed", self.channel_id, self.caption, self.img_url)
        self.assertEqual(variables["input"]["text"], self.caption)

    def test_image_url_in_assets(self):
        variables = buffer_post.build_variables("feed", self.channel_id, self.caption, self.img_url)
        self.assertIn(self.img_url, variables["input"]["assets"]["images"])

    def test_scheduling_type_is_automatic(self):
        variables = buffer_post.build_variables("feed", self.channel_id, self.caption, self.img_url)
        self.assertEqual(variables["input"]["schedulingType"], "automatic")

    def test_mode_is_add_to_queue(self):
        variables = buffer_post.build_variables("feed", self.channel_id, self.caption, self.img_url)
        self.assertEqual(variables["input"]["mode"], "addToQueue")


class TestHandleResponse(unittest.TestCase):
    def test_success_returns_true(self):
        data = {"data": {"createPost": {"post": {"id": "post_abc", "dueAt": "2024-01-01"}}}}
        result = buffer_post.handle_response(data, "feed")
        self.assertTrue(result)

    def test_success_prints_post_id(self):
        data = {"data": {"createPost": {"post": {"id": "post_abc", "dueAt": "2024-01-01"}}}}
        with patch("builtins.print") as mock_print:
            buffer_post.handle_response(data, "feed")
            mock_print.assert_called_once_with("Feed post created: post_abc")

    def test_success_capitalizes_post_type(self):
        data = {"data": {"createPost": {"post": {"id": "post_xyz", "dueAt": "2024-01-01"}}}}
        with patch("builtins.print") as mock_print:
            buffer_post.handle_response(data, "story")
            mock_print.assert_called_once_with("Story post created: post_xyz")

    def test_error_returns_false(self):
        data = {"data": {"createPost": {"message": "Unauthorized", "extensions": {"code": "UNAUTHORIZED"}}}}
        result = buffer_post.handle_response(data, "feed")
        self.assertFalse(result)

    def test_error_prints_to_stderr(self):
        data = {"data": {"createPost": {"message": "Error"}}}
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            buffer_post.handle_response(data, "feed")
            self.assertIn("Error creating feed post", mock_stderr.getvalue())

    def test_missing_data_key_returns_false(self):
        result = buffer_post.handle_response({}, "feed")
        self.assertFalse(result)

    def test_empty_create_post_returns_false(self):
        result = buffer_post.handle_response({"data": {"createPost": {}}}, "story")
        self.assertFalse(result)


class TestPostToBuffer(unittest.TestCase):
    def _make_mock_response(self, payload):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_success_returns_true(self):
        payload = {"data": {"createPost": {"post": {"id": "post_1", "dueAt": "2024-01-01"}}}}
        with patch("urllib.request.urlopen", return_value=self._make_mock_response(payload)):
            result = buffer_post.post_to_buffer(
                post_type="feed",
                api_key="key123",
                channel_id="chan_456",
                img_url="https://img.example.com/img.jpg",
                post_title="Hello World",
                post_url="https://example.com/hello",
            )
        self.assertTrue(result)

    def test_api_error_returns_false(self):
        payload = {"data": {"createPost": {"message": "Unauthorized"}}}
        with patch("urllib.request.urlopen", return_value=self._make_mock_response(payload)):
            result = buffer_post.post_to_buffer(
                post_type="story",
                api_key="bad_key",
                channel_id="chan_456",
                img_url="https://img.example.com/img.jpg",
                post_title="Hello World",
                post_url="https://example.com/hello",
            )
        self.assertFalse(result)

    def test_sends_bearer_token(self):
        payload = {"data": {"createPost": {"post": {"id": "p1", "dueAt": "2024-01-01"}}}}
        with patch("urllib.request.urlopen", return_value=self._make_mock_response(payload)), \
             patch("urllib.request.Request") as MockRequest:
            buffer_post.post_to_buffer(
                post_type="feed",
                api_key="mytoken",
                channel_id="chan_1",
                img_url="https://img.example.com/img.jpg",
                post_title="Title",
                post_url="https://example.com",
            )
            _, kwargs = MockRequest.call_args
            headers = kwargs.get("headers", MockRequest.call_args[0][2] if len(MockRequest.call_args[0]) > 2 else {})
            # Check via the actual call args since Request is positional
            call_args = MockRequest.call_args
            # headers are passed as keyword arg
            passed_headers = call_args.kwargs.get("headers", {})
            self.assertEqual(passed_headers.get("Authorization"), "Bearer mytoken")

    def test_sends_json_content_type(self):
        payload = {"data": {"createPost": {"post": {"id": "p1", "dueAt": "2024-01-01"}}}}
        with patch("urllib.request.urlopen", return_value=self._make_mock_response(payload)), \
             patch("urllib.request.Request") as MockRequest:
            buffer_post.post_to_buffer(
                post_type="feed",
                api_key="mytoken",
                channel_id="chan_1",
                img_url="https://img.example.com/img.jpg",
                post_title="Title",
                post_url="https://example.com",
            )
            passed_headers = MockRequest.call_args.kwargs.get("headers", {})
            self.assertEqual(passed_headers.get("Content-Type"), "application/json")


class TestMain(unittest.TestCase):
    def test_missing_argument_exits_1(self):
        with patch("sys.argv", ["buffer_post.py"]):
            with self.assertRaises(SystemExit) as ctx:
                buffer_post.main()
            self.assertEqual(ctx.exception.code, 1)

    def test_invalid_post_type_exits_1(self):
        with patch("sys.argv", ["buffer_post.py", "reel"]):
            with self.assertRaises(SystemExit) as ctx:
                buffer_post.main()
            self.assertEqual(ctx.exception.code, 1)

    def test_invalid_post_type_prints_to_stderr(self):
        with patch("sys.argv", ["buffer_post.py", "reel"]), \
             patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                buffer_post.main()
            self.assertIn("reel", mock_stderr.getvalue())

    def test_success_exits_0(self):
        payload = {"data": {"createPost": {"post": {"id": "p1", "dueAt": "2024-01-01"}}}}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        env = {
            "BUFFER_API_KEY": "key",
            "BUFFER_CHANNEL_ID": "chan",
            "IMG_URL": "https://img.example.com/img.jpg",
            "POST_TITLE": "Title",
            "POST_URL": "https://example.com",
        }
        with patch("sys.argv", ["buffer_post.py", "feed"]), \
             patch.dict("os.environ", env), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            # Should not raise SystemExit
            buffer_post.main()

    def test_api_failure_exits_1(self):
        payload = {"data": {"createPost": {"message": "Error"}}}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        env = {
            "BUFFER_API_KEY": "key",
            "BUFFER_CHANNEL_ID": "chan",
            "IMG_URL": "https://img.example.com/img.jpg",
            "POST_TITLE": "Title",
            "POST_URL": "https://example.com",
        }
        with patch("sys.argv", ["buffer_post.py", "story"]), \
             patch.dict("os.environ", env), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            with self.assertRaises(SystemExit) as ctx:
                buffer_post.main()
            self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
