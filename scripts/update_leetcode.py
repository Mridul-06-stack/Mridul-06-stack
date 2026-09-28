"""Fetch LeetCode stats and inject them into README.md between marker comments."""
import json
import os
import re
import sys
import urllib.request

USERNAME = os.environ.get("LEETCODE_USERNAME", "").strip()
if not USERNAME:
    sys.exit("LEETCODE_USERNAME is not set")

QUERY = """
query userStats($username: String!) {
  matchedUser(username: $username) {
    profile { ranking }
    submitStats: submitStatsGlobal {
      acSubmissionNum { difficulty count }
    }
  }
  userContestRanking(username: $username) {
    rating
    attendedContestsCount
    topPercentage
  }
}
"""

req = urllib.request.Request(
    "https://leetcode.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"username": USERNAME}}).encode(),
    headers={
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/u/{USERNAME}/",
        "User-Agent": "Mozilla/5.0",
    },
)
with urllib.request.urlopen(req, timeout=30) as resp:
    payload = json.load(resp)

user = (payload.get("data") or {}).get("matchedUser")
if not user:
    sys.exit(f"LeetCode user '{USERNAME}' not found")

solved = {d["difficulty"]: d["count"] for d in user["submitStats"]["acSubmissionNum"]}
contest = (payload["data"] or {}).get("userContestRanking")

lines = [
    "| Total Solved | Easy | Medium | Hard | Global Rank |",
    "|:---:|:---:|:---:|:---:|:---:|",
    f"| **{solved.get('All', 0)}** | {solved.get('Easy', 0)} | {solved.get('Medium', 0)} "
    f"| {solved.get('Hard', 0)} | {user['profile']['ranking']:,} |",
]
if contest:
    lines += [
        "",
        f"🏅 Contest rating: **{round(contest['rating'])}** "
        f"· Contests attended: **{contest['attendedContestsCount']}** "
        f"· Top **{contest['topPercentage']:.2f}%**",
    ]
lines += ["", f"_Auto-updated via GitHub Actions · [Profile](https://leetcode.com/u/{USERNAME})_"]
block = "\n".join(lines)

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

pattern = re.compile(r"(<!--LEETCODE_START-->).*?(<!--LEETCODE_END-->)", re.DOTALL)
if not pattern.search(readme):
    sys.exit("LeetCode markers not found in README.md")

readme = pattern.sub(lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}", readme)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("README updated")