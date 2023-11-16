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



if __name__ == "__main__":
    scrapy()





