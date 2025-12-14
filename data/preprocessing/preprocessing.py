import argparse
import re
import os
from pymongo import MongoClient
import pandas as pd

TAG_RE = re.compile(r"<[^>]+>")

def clean_text(text):
    if text is None:
        return ""
    text = TAG_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

client = MongoClient("mongodb://root:my-secret-pw@localhost:27017")

labels_db = client["MiningDesignDecisions"]
jira_db = client["JiraRepos"]

labels = labels_db["IssueLabels"]

# Make sure it has the fields
cursor = labels.find(
    {
        "tags": "has-label",
        "existence": {"$exists": True},
        "property": {"$exists": True},
        "executive": {"$exists": True}
    },
    no_cursor_timeout=True
)

records = []

for label in cursor:
    label_id = label["_id"] # "Apache-13343357"
    if "-" not in label_id:
        continue

    project, issue_id = label_id.split("-", 1)

    issue = jira_db[project].find_one({"id": issue_id})
    if not issue:
        continue

    fields = issue.get("fields", {})
    description = clean_text(fields.get("description", ""))
    summary = clean_text(fields.get("summary", ""))
    if description == "" and summary == "":
        continue

    records.append({
        "project": project,
        "label_id": label_id,
        "description": description,
        "summary": summary,
        "existence": bool(label.get("existence", False)),
        "property": bool(label.get("property", False)),
        "executive": bool(label.get("executive", False)),
    })

# Convert to DataFrame
df = pd.DataFrame(records)
# Output path
os.makedirs("data", exist_ok = True)
output_path = "data/issue_with_labels.csv"
df.to_csv(output_path, index=False, encoding="utf-8")

print(f"CSV exported to {output_path}!")
