"""
To install all the dependencies:
    pip install -r requirements.txt

To save the current dependencies in the python/conda env:
    pip freeze > requirements.txt


ON Mac M1 chip, do

    brew install --cask chromedriver

to install chromdriver to PATH



source ~/desktop/project/pyscrapeEnv/bin/activate

sudo xcode-select --switch /Applications/Xcode.app
/Applications/Xcode.app

python3 app.py
"""

from bs4 import BeautifulSoup
import requests, lxml, os, json
from parsel import Selector

# requestHandler()
import random

# selenium_stealth
from selenium import webdriver
from selenium_stealth import stealth
import time

# Proxy Rotation
from fp.fp import FreeProxy

# For CSV parsing
import pandas

# For filtering venue names
import re

# For selenium web scrape tutorial
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#import org.openqa.selenium.support.ui.Select;
from selenium.webdriver.support.select import Select
#import org.openqa.selenium.By;

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from pymongo.mongo_client import MongoClient

from selenium.common.exceptions import WebDriverException

from dotenv import load_dotenv
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from concis_ML.spiders.UBCSpider import UBCSpider

import cohere
from cohere.responses.classify import Example

import pinecone

import voyageai 
from voyageai import get_embeddings

# to install cohere
# python -m pip install cohere

load_dotenv()


"""
We only use the code below, code after main is not being used right now 
"""
def scrapy():
    faculty_to_scrape = 'commerce-and-business-administration'  # Replace with the faculty you want to scrape
    custom_settings = {
        'LOG_LEVEL': 'WARNING',  # Set log level to warning to reduce console output
    }

    process = CrawlerProcess(get_project_settings(), custom_settings)
    process.crawl(UBCSpider, faculty=faculty_to_scrape, jobdir='crawls/UBCSpider-1')
    process.start()

def create_pinecone_db():
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

    for x in mycol.find():
        only_route = not '/' in x['url']
        
        try:
            url_no_https = x['url'][8:] # getting rid of 'https://' in the url
        except IndexError:
            print(f"url does not contain 'https://': {x['url']}")
        
        if only_route:
            print(f"no path found for url: {x['url']}")
            print(f"setting to route name (IDK what a route name is)")
            title = url_no_https
            last_dot = title.rfind('.')
            title = title[:last_dot]
            title = title.replace('.', ' ')
            title = title.replace('-', ' ')
            print(f"new title: {title}")
        else:
            first_slash = url_no_https.find('/')
            path = url_no_https[first_slash + 1:] # assumes that if no path, there is no '/' at the end or else will index error
            title = path.replace('/', ' ')
            title = title.replace('-', ' ')
            print(f"title: {title}")
        
        info = f"{title}: \n{x['text']}'"
        
        documents_embeddings = get_embeddings([info], model="voyage-01")
        
        # documents_embeddings = co.embed(
        #     texts=[info],
        #     model='embed-english-v3.0',
        #     input_type='search_document'
        # )
        
        vector = {
            'id': x['url'], 
            'values':documents_embeddings[0], 
            'metadata':{'url': x['url']},
        }
        
        status = index.upsert(vectors=[vector])
        if 'upserted_count' in status:
            print(f"status: {status}, SUCCESSFULLY SENT: {x['url']}")
        else:
            print(f"status: {status}, FAILED TO SEND: {x['url']}")

if __name__ == "__main__":
    create_pinecone_db()





