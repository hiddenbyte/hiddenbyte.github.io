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
import urllib.error
import urllib.request

post_type = sys.argv[1]
if post_type not in ("feed", "story"):
    print(f"Invalid post type: {post_type!r}. Must be 'feed' or 'story'.", file=sys.stderr)
    sys.exit(1)

caption = f"{os.environ['POST_TITLE']}\n\n{os.environ['POST_URL']}"

mutation_name = "CreateFeedPost" if post_type == "feed" else "CreateStoryPost"
mutation = f"""
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

# Buffer's instagram type for feed posts is "post", not "feed"
instagram_type = "post" if post_type == "feed" else "story"

variables = {
    "input": {
        "channelId": os.environ["BUFFER_CHANNEL_ID"],
        "text": caption,
        "assets": {
            "images": [os.environ["IMG_URL"]]
        },
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "metadata": {
            "instagram": {
                "type": instagram_type
            }
        }
    }
}

payload = json.dumps({"query": mutation, "variables": variables}).encode()
req = urllib.request.Request(
    "https://api.buffer.com",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['BUFFER_API_KEY']}"
    }
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP {e.code} {e.reason}", file=sys.stderr)
    print("Response body:", body, file=sys.stderr)
    sys.exit(1)

print("Response:", json.dumps(data, indent=2))
result = data.get("data", {}).get("createPost", {})
if "post" in result:
    print(f"{post_type.capitalize()} post created: {result['post']['id']}")
else:
    print(f"Error creating {post_type} post:", data, file=sys.stderr)
    sys.exit(1)
