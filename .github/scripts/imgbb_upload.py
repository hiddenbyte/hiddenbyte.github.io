import sys
import json

d = json.load(sys.stdin)
if not d.get("success"):
    print("Upload failed:", d, file=sys.stderr)
    sys.exit(1)
print(d["data"]["url"])
