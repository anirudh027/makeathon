from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import HumanMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_community.tools import DuckDuckGoSearchRun, GoogleSearchRun, FileSearchTool
from langchain.retrievers.web_research import WebResearchRetriever
from langchain.chains import ConversationalRetrievalChain, RetrievalQAWithSourcesChain, ConversationChain
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import TextLoader
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import OpenAIEmbeddings
from langchain.evaluation import load_evaluator
import sys
from gpt_tools import *
from sqlite_utils import *

import numpy as np

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

## REFRESH FUNCTION ##
def refresh_user_data(USER_ID):
    
    global TOOLS, persona_rag, similar_history_rag, update_persona
    persona_to_text(USER_ID,'user_persona')
    ## Converting to db
    persona = TextLoader("user_persona.txt")
    persona = persona.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    persona_texts = text_splitter.split_documents(persona)
    persona_db = FAISS.from_documents(persona_texts, embeddings)

    persona_retriever = persona_db.as_retriever()
    persona_rag = create_retriever_tool(
        persona_retriever,
        "user_persona",
        "User persona",
    )


    ## Gathering Neighbors
    similar_account = get_similarity(USER_ID)
    top = sorted(list(similar_account.keys()), key=lambda x: similar_account[x], reverse=True)[:2]
    history_to_text(top,'similar_history')

    similar_history = TextLoader("similar_history.txt")
    similar_history = similar_history.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    similar_history_texts = text_splitter.split_documents(similar_history)
    similar_history_db = FAISS.from_documents(similar_history_texts, embeddings)

    similar_history_retriever = similar_history_db.as_retriever()
    similar_history_rag = create_retriever_tool(
        similar_history_retriever,
        "similar_history",
        "History of users with similar preferences",
    )

    TOOLS = [DuckDuckGoSearchRun(), static_rag, persona_rag, similar_history_rag, update_persona, summarize_chat]

class Persona(BaseModel):
    Demographics: str = Field(default=None, description="This encompasses various personal attributes and characteristics that describe an individual or group. It includes information about their gender, age or age group, marital status, and details about their children, such as the number and their ages. It also takes into account their profession, current economic standing, and potential for career growth. The location is also a key factor, covering the type of region they reside in, whether rural or urban, as well as the country they live in. Additionally, it examines their vehicle ownership history, indicating the number and types of vehicles, with a focus on whether they prefer luxury modern executive, compact SUVs or mid-range cars or used cars. It should also include what price of car they prefer. Finally, this description includes the percentage of the overall customer base that this group represents.")
    Customer_Experience: str = Field(default=None, description="This captures the diverse ways customers engage with a brand throughout their journey, highlighting a range of preferences, behaviors, and touchpoints. It assesses whether customers lean toward digital communication or traditional transaction methods. Brand loyalty can play a role in this, leading some customers to request minimal information during their purchases. The preferred mode of communication for service bookings, such as digital channels, phone calls, or direct clicks, is also considered. Additionally, it notes whether customers appreciate pick-up service options, whether are inclined to adopt service contracts when purchasing a car. This approach provides a comprehensive understanding of how customers interact with a brand, ensuring that their unique needs and preferences are met.")
    Psychology: str = Field(default=None, description="This outlines a customer's mindset, focusing on their price sensitivity, passion for cars, and attitude toward spending. It captures whether they follow traditional approaches, are price-sensitive but value quality, and whether they are open to luxury and convenience, showing a willingness to invest in higher-end products. It considers their appetite for financial risk, distinguishing those who prefer reliable, well-known brands from those more adventurous with newer brands. The description also evaluates their buying behavior, noting whether they are impulsive shoppers swayed by societal trends or those who prioritize brand prestige, maintenance, and resale value over simple status symbols. Additionally, it observes whether customers use cars as basic transportation or as a display of status. This information also includes their digital savvy, eco-friendliness, and willingness to pay for sustainable options. It further considers their hobbies and whether they are loyal to established brands or open to exploring newer ones.")
    Marketing_Implications: str = Field(default=None, description="This decribes the positioning strategies of what the customer is attracted to. High-end luxury targets the elite market, while premium with a digital flair appeals to modern, tech-savvy consumers. It might offer a mix of digital and personalised services. The focus on premium emphasizes high quality, and the value strategy attracts budget-conscious customers who want services at a fair price without unnecessary frills.")
    
@tool("update_persona", args_schema=Persona, return_direct=False)
def update_persona(Demographics: str  = None, Customer_Experience: str = None, Psychology: str = None, Marketing_Implications: str  = None) -> None:
    """
    Get information of a user and make a persona by dividing the information into Demographics, Customer Experience, Psychology and Marketing Implications according to the way each of them are described. Used to update the current database and should be called whenever you get info about any parameters. All parameters need not be passed to call this.
    """
    if Demographics is not None:
        append_to_profile_column(USER_ID, 'demographics', Demographics)

    if Customer_Experience is not None:
        append_to_profile_column(USER_ID, 'experience', Customer_Experience)

    if Psychology is not None:
        append_to_profile_column(USER_ID, 'psychology', Psychology)

    if Marketing_Implications is not None:  
        append_to_profile_column(USER_ID, 'marketing', Marketing_Implications)

    ## update the user persona
    refresh_user_data(USER_ID)

    print("Tools updated")

class SummarizeChat(BaseModel):
    chat_highlights: str = Field(description="This will describe the different cars and prices suggested to the customer by the bot and whether they reacted positively or negatively towards that particluar suggestion. It will record each of the suggestionas and the corresponding reactions in bullet form. Just record the answers like positive or negative beside the suggestion provided and also the reason behind why they liked or disliked a particulr model. It can be something like,  EQB SUV suggested: Disliked because the customer did not like the charging. The next suggestion and the corresponding reaction can be in the next line in another bullet point.")

@tool("summarize_chat", args_schema=SummarizeChat, return_direct=False)
def summarize_chat(chat_highlights: str) -> None:
    """
    Summarizes the entire conversation that the customer had with the bot.
    """
    append_to_profile_column(USER_ID, 'history', chat_highlights)

    ## update the user persona
    refresh_user_data(USER_ID)

    print("Tools updated")



### DEFINING GLOBAL VARIABLES ###
USER_ID = None
embeddings = OpenAIEmbeddings()
db = FAISS.load_local("mercedes_db/", embeddings, allow_dangerous_deserialization=True)
retriever = db.as_retriever()
static_rag = create_retriever_tool(
    retriever,
    "mercedes_e_cars_specs",
    "Information about mercedes electric cars and their specifications",
)
persona_rag= None
similar_history_rag = None
TOOLS = [DuckDuckGoSearchRun(), static_rag, persona_rag, similar_history_rag, update_persona, summarize_chat]
MESSAGES = [SystemMessage(content="This will assist customers to buy an electric car that will recommend only Mercedes cars. Your focus is giving concise answers and making a sale. You need to use the file 'user_persona' to identify their needs. These needs need to be updated frequently with the 'update_persona' tool.\
                          The 'update_persona' function will be called whenever you get any new updates. Anytime a personal information or preference comes, check if it needs to be updated. Then look up the answer in the 'mercedes_e_cars_specs' document. For better recommendations, you should refer 'similar_history' file to see what similar people prefer.\
                          The 'summarize_chat' function will be called at the end of the chat to summarize all the information regarding the entire conversation. There will be the suggestions provided by the bot and corresponding to each of them there has to be a reaction recorded as in whether the customer had a positive or negative reaction. Give negative responses to the cars that the customer does not talk about when suggested. Each of the suggestions and the reactions should be in separate lines, preferably in bullet points.\
                          Do not ask many questions. Do not tell the user that the function has been called. Do not mention the source pdf from where it is getting the information.")]


def update_user_id(email):
    '''
    Update the global USER_ID variable with the email of the user
    '''
    global USER_ID
    USER_ID = email

def chat(msg):

    global MESSAGES, TOOLS

    print(TOOLS)

    llm = ChatOpenAI(
        model="gpt-4",
        max_tokens=500,
        max_retries=10,
        )
    # Creating the retriever
    prompt = hub.pull("hwchase17/openai-tools-agent")
    agent = create_openai_tools_agent(llm, TOOLS, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=TOOLS, verbose=True)

    MESSAGES.append(HumanMessage(content=msg))
    bot_response = agent_executor.invoke({"input": msg, "chat_history":MESSAGES})['output']
    MESSAGES.append(AIMessage(content=bot_response))
    
    return bot_response