from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_astradb import AstraDBVectorStore
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents import create_tool_calling_agent
from langchain_core.tools.retriever import create_retriever_tool
from langchain_classic import hub
from github import fetch_github_issues
from note import note_tool

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

  return vtstore


if __name__ == "__main__":
  if(not os.getenv("ASTRA_DB_APPLICATION_TOKEN")):
    raise RuntimeError("Set ASTRA_DB_APPLICATION_TOKEN")
  if(not os.getenv("OPENAI_API_KEY")):
    raise RuntimeError("Set OPENAI_API_KEY")
  if(not os.getenv("GITHUB_REPO_OWNER")):
    raise RuntimeError("Set GITHUB_REPO_OWNER")
  if(not os.getenv("GITHUB_REPO_NAME")):
    raise RuntimeError("Set GITHUB_REPO_NAME")

  vtstore = connect_to_vtstore()
  add_to_vectorstore = input("Would you like to update the Github issues? (y/N): ").lower() in ["yes", "y"]

  if(add_to_vectorstore):
    issues = fetch_github_issues(owner=os.getenv("GITHUB_REPO_OWNER"), repo=os.getenv("GITHUB_REPO_NAME"))
    try:
      vtstore.delete_collection()
      print("Deleted existing collection 'github_issues'.")
    except:
      pass

    vtstore = connect_to_vtstore()
    print(f"Connected to AstraDB vector store.")
    print(f"Fetched {len(issues)} issues from GitHub repository {os.getenv('GITHUB_REPO_OWNER')}/{os.getenv('GITHUB_REPO_NAME')}.")
    vtstore.add_documents(issues)
    print("Added issues to AstraDB vector store.")


  retriever = vtstore.as_retriever(search_kwargs={"k": 3}) # Search 3 documents
  retriever_tool = create_retriever_tool(
    retriever=retriever,
    name="github_search",
    description="Search for information about github issues. For any questions about github issues, you must use this tool!",
  )

  prompt = hub.pull("hwchase17/openai-functions-agent")
  llm = ChatOpenAI()
  tools = [retriever_tool, note_tool]

  agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
  )
  agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
  )

  while (question := input("Ask a question about github issues (q to quit): ")) != "q":
    result = agent_executor.invoke({
      "input": question
    })
    print(result["output"])