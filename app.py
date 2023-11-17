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
from pymongo.server_api import ServerApi

from selenium.common.exceptions import WebDriverException

from dotenv import load_dotenv
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from concis_ML.spiders.UBCSpider import UBCSpider

from urllib.parse import urlparse
import random

import json
from typing import List

# Group data by categories
from collections import defaultdict 

"""
We only use the code below, code after main is not being used right now 
"""

def scrapy(school='UBC',faculty_to_scrape='commerce-and-business-administration'):
    custom_settings = {
        'LOG_LEVEL': 'WARNING',  # Set log level to warning to reduce console output
    }

    process = CrawlerProcess(get_project_settings())
    process.crawl(UBCSpider, faculty=faculty_to_scrape, jobdir='crawls/UBCSpider-1')
    process.start()


def top_longest_common_substrings(text1, text2, top_n=3):
    dp = [[0] * (len(text2) + 1) for _ in range(len(text1) + 1)]
    common_substrings = []

    for i in range(1, len(text1) + 1):
        for j in range(1, len(text2) + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > 0:
                    common_substrings.append((i, dp[i][j]))
            else:
                dp[i][j] = 0

    # Sort common substrings by length and end position
    common_substrings.sort(key=lambda x: (-x[1], x[0]))

    result = []
    last_end_pos = -1

    for end_pos, length in common_substrings:
        start_pos = end_pos - length

        # Check if the current substring overlaps with previously added substrings
        if start_pos > last_end_pos:
            result.append(text1[start_pos: end_pos])
            last_end_pos = end_pos

            if len(result) == top_n:
                break

    # Continue searching if we haven't found enough non-overlapping substrings
    while len(result) < top_n:
        for end_pos, length in common_substrings:
            start_pos = end_pos - length
            if start_pos > last_end_pos:
                result.append(text1[start_pos: end_pos])
                last_end_pos = end_pos

                if len(result) == top_n:
                    break

        if len(result) < top_n:
            break  # Exit loop if no more non-overlapping substrings can be found

    return result


def remove_substrings(text, substrings):
    for substring in substrings:
        text = text.replace(substring, "")
    return text


def update__and_save_common_strings(filename: str, domain: str, new_common_substrings) -> str:
    """ Manage common strings for a specific domain. """

    def load_common_strings():
        """ Load common strings for the domain from a JSON file. """
        try:
            with open(filename, 'r') as file:
                data = json.load(file)
                return data.get(domain, [])
        except FileNotFoundError:
            return []  # Return an empty list if the file does not exist

    def save_common_strings(common_strings: List[str]):
        """ Save common strings for the domain to a JSON file. """
        try:
            with open(filename, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        data[domain] = common_strings
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

    def update_common_strings(existing_strings: List[str], new_strings: List[str]) -> List[str]:
        """ Update the list of common strings with new non-duplicate strings. """
        updated_strings = existing_strings.copy()
        for string in new_strings:
            if string not in existing_strings:
                updated_strings.append(string)
        return updated_strings

    # Load existing common strings for the domain
    existing_strings = load_common_strings()

    # Update the list with new common substrings
    updated_strings = update_common_strings(existing_strings, new_common_substrings)

    # Save the updated list back to the JSON file for the domain
    save_common_strings(updated_strings)

    return updated_strings



def clean_data(school='UBC',faculty='commerce-and-business-administration'):

    func_tag = "[clean_data()]"
    # Establish a connection to the MongoDB server
    db_uri = os.getenv('MONGO_URL')  # Use os.getenv to get the environment variable
    db_client = MongoClient(db_uri)   
    
    # Connect to the MongoDB server 
    db = db_client[school]
    # Get the collection
    collection = db[faculty]
    # Get all the documents
    shuffle_docs = list(collection.find({}))
    random.shuffle(shuffle_docs)

    # For common substring extraction
    filename = 'common_substrings.json'

    grouped_data = defaultdict(list)
    for doc in shuffle_docs:
        # Extract domain from the first document's URL
        url = doc.get('url', '')
        domain = urlparse(url).netloc
        
        grouped_data[domain].append(doc)

    # Now, process each category
    for domain, docs in grouped_data.items():
        print(f"{func_tag} | Processing category: {domain}")

        # for item in items:
        #     # Perform some operation with each item
        #     print(f" - Processing item: {item['name']}")


        # Iterate over the documents
        for i in range(len(docs)):
            print(f"{func_tag} | Processing doc with url : {docs[i]['url']}")
            if i == 0:
                prev_text = docs[i]['text']
                continue


            this_text = docs[i]['text']
            # This returns most up-to-date common substring that is loaded from file, and calculated from two texts
            updated_common_substring = update__and_save_common_strings(filename, domain, top_longest_common_substrings(this_text, prev_text))
            
            # Need to update the doc at index 0 with the udpated common substring found in iteration 1
            if i == 1:
                cleaned_prev_text = remove_substrings(prev_text, updated_common_substring)
                # Update the first document in mongoDB so that it has cleaned_text
                collection.update_one({'_id': docs[i-1]['_id']}, {'$set': {'cleaned_text': cleaned_prev_text}})

            # This is the regular text cleaning for all i in [1,n-1]
            cleaned_this_text = remove_substrings(this_text, updated_common_substring)
            collection.update_one({'_id': docs[i]['_id']}, {'$set': {'cleaned_text': cleaned_this_text}})
            prev_text = this_text

def substring():
    with open('page_text_example.json', 'r') as file:
        text_example = json.load(file)
    longest_common_substrings = top_longest_common_substrings(text_example['text1'], text_example['text2'])

    #Print each substring on a new line
    for substring in longest_common_substrings:
        print("\n", substring)

if __name__ == "__main__":
    load_dotenv()

    # This is test function for common substring extraction
    #substring()

    #scrapy()
    clean_data('UBC','commerce-and-business-administration')







