# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import HtmlResponse


import json
from concis_ML.items import Webpage  # Make sure 'Webpage' is defined in your items.py
import hashlib
import logging



class UBCSpider(CrawlSpider):
    name = 'UBC'

    def __init__(self, faculty=None, *args, **kwargs):
        super(UBCSpider, self).__init__(*args, **kwargs)
        self.faculty = faculty

        # Set the logging level to INFO to reduce the verbosity of the logs
        logging.getLogger('scrapy').setLevel(logging.INFO)

        # Load faculty metadata from a JSON file
        with open('./concis_ML/faculty_metadata.json', 'r') as file:
            faculty_metadata = json.load(file)

        if faculty in faculty_metadata:
            faculty_data = faculty_metadata[faculty]
            self.start_urls = faculty_data['start_urls']
            self.allowed_domains = list(faculty_data['allowed_domains'].keys())
            self.allowed_paths = faculty_data['allowed_domains']

            self.rules = (
                Rule(LinkExtractor(allow=()), callback='parse_item', follow=True, process_links='filter_links'),
            )
            self._compile_rules()
        else:
            raise ValueError(f"Faculty '{faculty}' not supported")

    def filter_links(self, links):
        filtered_links = []
        for link in links:
            domain = link.url.split('/')[2]
            if domain in self.allowed_paths:
                if any(link.url.find(path) != -1 for path in self.allowed_paths[domain]):
                    filtered_links.append(link)
        return filtered_links

    # Rename 'parse' to 'parse_item' because CrawlSpider uses the 'parse' method itself
    def parse_item(self, response):
        #self.logger.info(f'Parsing URL: {response.url}')
        item = Webpage()

        item['university_name'] = self.name
        item['faculty'] = self.faculty
        item['url'] = response.url

        # Extract text and create a single string with newline characters removed
        texts = response.xpath('//body//text()').getall()
        item['text'] = ' '.join([text.strip() for text in texts if text.strip()])

        item['links'] = response.css('a::attr(href)').getall()

        content = response.xpath('//body//text()').getall()
        item['content_hash'] = self.hash_content(content)

        yield item

    def _requests_to_follow(self, response):
        if not isinstance(response, HtmlResponse):
            return
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                    if lnk not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            for link in links:
                seen.add(link)
                r = self._build_request(n, link)
                # Call the process_request method of the rule and get the processed request
                processed_request = rule.process_request(r, response)
                if processed_request:
                    yield processed_request


    def _build_request(self, rule, link):
        # Override method to use dont_filter
        r = scrapy.Request(url=link.url, callback=self.parse_item)
        r.meta.update(rule=rule, link_text=link.text)
        return r.replace(dont_filter=True)
    

    """
    Custom content hashing mechanism to update the webpage if changes has been made.

    The change is found, then it records the change in the ./../logs/changes_{spider.name}_{spider.faculty}_{date_str}.txt folder and the date which the change has been found
    """
    def hash_content(self, content):
        # Concatenate all lines of content and encode to a byte string
        content_string = ''.join(content).encode('utf-8')
        # Calculate the hash
        return hashlib.sha256(content_string).hexdigest()

if __name__ == "__main__":
    faculty_to_scrape = 'commerce-and-business-administration'  # Replace with the faculty you want to scrape
    process = CrawlerProcess(get_project_settings())
    process.crawl(UBCSpider, faculty=faculty_to_scrape, jobdir='crawls/UBCSpider-1')
    process.start()
