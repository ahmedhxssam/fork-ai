"""Create a new persisted scenario without deleting prior decisions or evidence."""
import argparse
import json
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--port", type=int, default=8000)
args = parser.parse_args()
request = urllib.request.Request(f"http://127.0.0.1:{args.port}/api/experiments",
    data=json.dumps({"seed": 26}).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(request, timeout=60) as response:
    experiment = json.load(response)
print(f"New experiment {experiment['id']} · revision {experiment['revision']}")
print(f"Open http://127.0.0.1:{args.port} and choose a fresh mission. Previous records are preserved.")
