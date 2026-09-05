import urllib.request, json
GITHUB_TOKEN = "REMOVED_TOKEN"
req = urllib.request.Request("https://api.github.com/repos/tsxau26-ux/fillo-outreach/actions/runs/32117372603/jobs")
req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
req.add_header("Accept", "application/vnd.github.v3+json")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
for job in data.get("jobs", []):
    print(f"Job: {job['name']} | status: {job['status']} | conclusion: {job['conclusion']}")
