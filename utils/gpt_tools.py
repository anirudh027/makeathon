from sqlite_utils import *
from langchain_openai import OpenAIEmbeddings
from langchain.evaluation import load_evaluator
import numpy as np
import os



## SIMILARITY MATCHING ##
embeddings_model = OpenAIEmbeddings(model="text-embedding-ada-002")
hf_evaluator = load_evaluator("embedding_distance", embeddings=embeddings_model)

def get_similarity(email):
    '''
    Get the similarity between the target email and all other emails in the database

    email: str
        The email of the target user

    return: dict
        A dictionary with the email as the key and the similarity as the value
    '''
    target = load_profile(email)[:-1]
    email_lists = [i[0] for i in get_all_emails(email)]
    lookups =  {i:load_profile(i)[:-1] for i in email_lists}
    similarities = {}
    for email,lookup in lookups.items():
        similarity = []
        for t, l in zip(target, lookup):
            if t is not None and l is not None:
                similarity.append(hf_evaluator.evaluate_strings(prediction=t, reference=l)['score'])
        similarities[email] = np.mean(similarity)

    return similarities


## Chatbot ##

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import PyPDFLoader

MESSAGES = [SystemMessage(content="This will assist customers to buy an electric car that will recommend only Mercedes cars")]

### Pre-loading the data
loader = PyPDFLoader("../mercedes-data.pdf")
documents  = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)
embeddings = OpenAIEmbeddings()
db = FAISS.from_documents(texts, embeddings)
retriever = db.as_retriever()
static_rag = create_retriever_tool(
    retriever,
    "mercedes_e_cars_specs",
    "Information about mercedes electric cars and their specifications",
)

tools = [DuckDuckGoSearchRun(), static_rag]

llm = ChatOpenAI(
    model="gpt-4",
    max_tokens=500,
    max_retries=10,
    )

# Creating the retriever
prompt = hub.pull("hwchase17/openai-tools-agent")
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def chat(msg, persona = None):
    MESSAGES.append(HumanMessage(content=msg)) # Add the user message to the chat history
    bot_response = agent_executor.invoke({"input": msg, "chat_history":MESSAGES})['output']
    MESSAGES.append(AIMessage(content=bot_response)) # Add the bot response to the chat history
    
    return bot_response