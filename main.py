from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_astradb import AstraDBVectorStore
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents import create_tool_calling_agent
# from langchain_classic.retrievers import create_retriever_tool
from langchain_classic import hub
from github import fetch_github_issues

load_dotenv()

def connect_to_vtstore() -> AstraDBVectorStore:

  try:
    embeddings = OpenAIEmbeddings()
    desired_namespace = os.getenv("ASTRA_DB_KEYSPACE")
    if desired_namespace:
      ASTRA_DB_KEYSPACE = desired_namespace
    else:
      ASTRA_DB_KEYSPACE = None

    vtstore = AstraDBVectorStore(
      embedding = embeddings,
      collection_name="github_issues", # create a new collection if not exists
      api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT", ""),
      token = os.getenv("ASTRA_DB_APPLICATION_TOKEN", ""),
      namespace = ASTRA_DB_KEYSPACE,
    )
  except Exception as e:
    print(f"Error connecting to AstraDB vector store: {e}")
    raise e

  # vtstore = AstraDBVectorStore.from_existing_collection(
  #   embeddings,
  #   astra_db_api_endpoint=astra_db_api_endpoint,
  #   astra_db_application_token=astra_db_application_token,
  #   astra_db_keyspace=astra_db_keyspace,
  #   collection_name="github_issues"
  # )
  return vtstore

vtstore = connect_to_vtstore()
add_to_vectorstore = input("Would you like to update the Github issues? (y/N): ").lower() in ["yes", "y"]

if(add_to_vectorstore):
  owner = "techwithtim"
  repo = "Flask-Web-App-Tutorial"
  issues = fetch_github_issues(owner, repo)

  try:
    vtstore.delete_collection()
    print("Deleted existing collection 'github_issues'.")
  except:
    pass

  vtstore = connect_to_vtstore()
  print(f"Connected to AstraDB vector store.")
  print(f"Fetched {len(issues)} issues from GitHub repository {owner}/{repo}.")
  vtstore.add_documents(issues)
  print("Added issues to AstraDB vector store.")

  results = vtstore.similarity_search("flash messages", k=3)
  for result in results:
    print(f"* {result.page_content} {result.metadata}")