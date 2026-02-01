import os, requests
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()

github_token = os.getenv("GITHUB_TOKEN", "")

def fetch_github(owner: str, repo: str, endpoint: str) -> Document:
  """
  Currently, whenever this function gets called, it searches
  the github repo for issues. It can extend more if needed
  """
  url = f"https://api.github.com/repos/{owner}/{repo}/{endpoint}"
  headers = {
    "Authorization": f"Bearer {github_token}"
  }
  response = requests.get(url, headers=headers)
  if(response.status_code == 200):
    data = response.json()
  else:
    print(f"Error: {response.status_code} - {response.text}")
    return []
    # raise Exception(f"Failed to fetch data from GitHub API: {response.status_code} - {response.text}")
  print("data:", data)
  return data

def load_issues(issues: list) -> list[Document]:
  docs = []
  for issue in issues:
    metadata = {
      "author": issue["user"]["login"],
      "comments": issue["comments"],
      "body": issue["body"],
      "labels": issue["labels"],
      "created_at": issue["created_at"],
    }
    data = issue["title"]
    if(issue["body"]):
      data += issue["body"]
    doc = Document(page_content=data, metadata=metadata)
    docs.append(doc)
  return docs

def fetch_github_issues(owner: str, repo: str) -> list[Document]:
  data = fetch_github(owner, repo, "issues")
  return load_issues(data)

