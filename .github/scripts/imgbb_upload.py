import sys
import json


def parse_imgbb_response(data):
    """Parse ImgBB API response dict. Returns the image URL on success, None on failure."""
    if not data.get("success"):
        return None
    return data["data"]["url"]


def main():
    d = json.load(sys.stdin)
    url = parse_imgbb_response(d)
    if url is None:
        print("Upload failed:", d, file=sys.stderr)
        sys.exit(1)
    print(url)


if __name__ == "__main__":
    main()
