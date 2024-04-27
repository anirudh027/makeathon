from sqlite_utils import *
from langchain_openai import OpenAIEmbeddings
from langchain.evaluation import load_evaluator
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