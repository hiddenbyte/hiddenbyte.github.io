"""
Post to Instagram via Buffer GraphQL API.

Usage: python3 buffer_post.py <post_type>
  post_type: 'feed' or 'story'

Required environment variables:
  BUFFER_API_KEY      Buffer API bearer token
  BUFFER_CHANNEL_ID   Buffer channel ID for the Instagram account
  IMG_URL             Public URL of the image to post
  POST_TITLE          Blog post title (used in caption)
  POST_URL            Blog post URL (used in caption)
"""

import json
import os
import sys
import urllib.request


def build_caption(post_title, post_url):
    return f"{post_title}\n\n{post_url}"


def build_mutation(post_type):
    mutation_name = "CreateFeedPost" if post_type == "feed" else "CreateStoryPost"
    return f"""
mutation {mutation_name}($input: CreatePostInput!) {{
  createPost(input: $input) {{
    ... on PostActionSuccess {{
      post {{
        id
        dueAt
      }}
    }}
    ... on MutationError {{
      message
      extensions {{
        code
      }}
    }}
  }}
}}
"""


def build_variables(post_type, channel_id, caption, img_url):
    return {
        "input": {
            "channelId": channel_id,
            "text": caption,
            "assets": {
                "images": [img_url]
            },
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "metadata": {
                "instagram": {
                    "type": post_type
                }
            }
        }
    }


def handle_response(data, post_type):
    """Return True on success, False on error."""
    result = data.get("data", {}).get("createPost", {})
    if "post" in result:
        print(f"{post_type.capitalize()} post created: {result['post']['id']}")
        return True
    print(f"Error creating {post_type} post:", data, file=sys.stderr)
    return False


def post_to_buffer(post_type, api_key, channel_id, img_url, post_title, post_url):
    caption = build_caption(post_title, post_url)
    mutation = build_mutation(post_type)
    variables = build_variables(post_type, channel_id, caption, img_url)

    payload = json.dumps({"query": mutation, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.buffer.com",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    print("Response:", json.dumps(data, indent=2))
    return handle_response(data, post_type)


def main():
    if len(sys.argv) < 2:
        print("Usage: buffer_post.py <post_type>", file=sys.stderr)
        sys.exit(1)

    post_type = sys.argv[1]
    if post_type not in ("feed", "story"):
        print(f"Invalid post type: {post_type!r}. Must be 'feed' or 'story'.", file=sys.stderr)
        sys.exit(1)

    success = post_to_buffer(
        post_type=post_type,
        api_key=os.environ["BUFFER_API_KEY"],
        channel_id=os.environ["BUFFER_CHANNEL_ID"],
        img_url=os.environ["IMG_URL"],
        post_title=os.environ["POST_TITLE"],
        post_url=os.environ["POST_URL"],
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
