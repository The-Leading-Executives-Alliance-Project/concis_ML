from dotenv import load_dotenv
import os
import pinecone

import voyageai 
from voyageai import get_embeddings

import cohere

from pymongo.mongo_client import MongoClient

load_dotenv()

def search_pages(query):
        query_embed = get_embeddings([query], model="voyage-01")
        
        results = index.query(
                vector=query_embed[0],
                top_k=2,
                include_values=True
        )

        return results

def ask(question, collection, num_generations=1):
    results = search_pages(question)
    
    matches = results['matches']
    documents = []
    urls = []
    for match in matches:
        url = match['id']
        urls.append(url)
        documents.append(collection.find_one({'url': url})['text'])
    
    prompt = f"""
    Extract the answer of the following question from the text provided.

    Question: {question}

    Provided with the following information: \n
    """

    for document in documents:
        prompt += f"{document}\n\n"

    prediction = co.generate(
            prompt=prompt,
            max_tokens=200,
            model="command-nightly",
            temperature=0.5,
            num_generations=num_generations
    )

    return prediction.generations, urls

if __name__ == "__main__":
    # SETUP
    pc_api_key = os.getenv("PINECONE_API_KEY")
    co_api_key = os.getenv("COHERE_API_KEY")
    env = os.getenv("PINECONE_ENVIRONMENT")
    mongo_url = os.getenv("MONGO_URL")
    voyageai.api_key = os.getenv("VOYAGEAI_API_KEY")
    
    pinecone.init(api_key=pc_api_key, environment=env)
    
    id_name = "website-info"
    index = pinecone.Index(id_name)
    
    co = cohere.Client(co_api_key)
    
    myclient = MongoClient(mongo_url)
    db_name = "UBC"
    col_name = "commerce-and-business-administration"
    mydb = myclient[db_name]
    mycol = mydb[col_name]
    # done setting up
    
    # THE ACTUAL PROGRAM
    question = "What do I need to be promoted to second year?"
    
    answer, urls = ask(question, mycol)

    print(f"questions: {question}")
    print(f"answer: {answer}")
    print(f"You can find more information from the following websites:")
    for url in urls:
        print(url)