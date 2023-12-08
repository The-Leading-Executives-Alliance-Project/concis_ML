# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


import json
from web_scraper.items import Webpage  # Make sure 'Webpage' is defined in your items.py
import hashlib
import random
import os


class UBCSpider(CrawlSpider):
    name = 'UBC'

    def __init__(self, faculty=None, *args, **kwargs):
        super(UBCSpider, self).__init__(*args, **kwargs)
        self.last_start_url = None
        self.faculty = faculty

        # Load faculty metadata from a JSON file
        with open('./web_scraper/faculty_metadata.json', 'r') as file:
            faculty_metadata = json.load(file)

        if faculty in faculty_metadata:
            faculty_data = faculty_metadata[faculty]
            self.start_urls = faculty_data['start_urls']
            self.allowed_domains = list(faculty_data['allowed_domains'].keys())
            self.allowed_paths = faculty_data['allowed_domains']

            # Creating dynamic rules based on the allowed paths for each domain
            self.rules = []
            for domain in self.allowed_domains:
                for path in self.allowed_paths[domain]:
                    # If path is '/', scrape the entire domain
                    if path == '/':
                        regex_pattern = r'.*'
                    else:
                        # Otherwise, scrape the specific route and sub-routes
                        regex_pattern = rf'{domain}{path}.*'
                    
                    self.rules.append(
                        Rule(
                            LinkExtractor(allow_domains=[domain], allow=[regex_pattern]),
                            callback='parse_item', 
                            follow=True,
                            process_request=self.add_start_url_meta,
                        )
                    )

            self._compile_rules()

            # Need to allow proxy domain for the crawler 
            self.allowed_domains.append('proxy.scrapeops.io')
        else:
            raise ValueError(f"Faculty '{faculty}' not supported")
    
    # # Activate this when you want to specify region for proxy or use advanced scrapeops features
    # # https://scrapeops.io/docs/proxy-aggregator/integration-examples/python-scrapy-example/
    # def start_requests(self):
    #     for url in self.start_urls:
    #         yield scrapy.Request(url=url, callback=self.parse_item, meta={'optimize_request' : True, 'max_request_cost' : 40})


    def add_start_url_meta(self, request, response):
        return request.replace(meta={'start_url': response.url})

        
    # def parse_start_url(self, response):
    #     start_url = response.url
    #     for link in self.link_extractor.extract_links(response):
    #         yield scrapy.Request(link.url, callback=self.parse_item, meta={'start_url': start_url})


    # def filter_links(self, links):
    #     print("printing links in filter_links() :", links[20])
    #     filtered_links = []
    #     for link in links:
    #         domain = link.url.split('/')[2]
    #         # print("domain :", domain)
    #         if domain in self.allowed_domains:
    #             # Special handling for root path '/'
    #             if '/' in self.allowed_paths[domain]:
    #                 filtered_links.append(link)
    #             else:
    #                 # Check for other specified paths
    #                 if any(link.url.find(path) != -1 for path in self.allowed_paths[domain]):
    #                     # print("the link passed the allowed route :", link.url)
    #                     filtered_links.append(link)
    #                 else:
    #                     # Print the ones that was skipped due to the allowed path for the domain
    #                     print(f'the link did not pass the allowed route : {link.url} in domain {domain} , and route {self.allowed_paths[domain]}')

    #     return filtered_links


    # Rename 'parse' to 'parse_item' because CrawlSpider uses the 'parse' method itself
    def parse_item(self, response):
        #self.logger.info(f'Parsing URL: {response.url}')
        item = Webpage()

        # This will print the change in start_url
        current_start_url = response.meta.get('start_url', None)

        # Check if the start_url has changed
        if current_start_url != self.last_start_url:
            print("\n\n" + "=" * 50)
            print(f"Links below originated from : {current_start_url}")
            print("=" * 50 + "\n\n")
            self.last_start_url = current_start_url  # Update last_start_url

        # This code is redundant, but its passing meta data for the process_item in the pipeline.py
        item['meta_data'] = {
            'start_url': response.meta.get('start_url', response.url),
            # Add other meta data as needed
            # 'other_data': 'value',
            }

        item['university_name'] = self.name
        item['faculty'] = self.faculty
        item['url'] = response.url

        random_number = random.randint(1, 600)

        for url in response.url :
            if url == "https://mybcom.sauder.ubc.ca/courses-money-enrolment/options":
                print("options link scraped : ", url)

        # Extract text and create a single string with newline characters removed
        texts = response.xpath('//body//text() | //body//a/text()').getall()
        item['text'] = '\n\n'.join([text.strip() for text in texts if text.strip()])

        # Randomly sample some responses and save them to a file
        if random_number == 1:
            self.save_HTTP_response(response.body, response.url)

        # Many relative links were found, so we need to convert them to absolute links
        absolute_links = [response.urljoin(href) for href in response.css('a::attr(href)').getall()]
        item['links'] = absolute_links

        for link in absolute_links :
            if link == "https://mybcom.sauder.ubc.ca/courses-money-enrolment/options":
                print("the options is found in the links of the current webpage : ", response.url)

        content = response.xpath('//body//text()').getall()
        item['content_hash'] = self.hash_content(content)

        yield item

    

    # Just a helper function to save the sample web response
    def save_HTTP_response(self, body, url):
        directory = 'web_scraper/response_samples/'

        # Check if the directory exists, and create it if it doesn't
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Generate a filename based on the URL or some unique identifier
        filename = directory + 'response_' + url.split('/')[-1] + '.txt'
        if not filename.strip():
            filename = directory + 'filename_None.txt'

        # Decode the body from bytes to a string
        decoded_body = body.decode('utf-8')

        # Write the decoded response body to the file
        with open(filename, 'w', encoding='utf-8') as file:  # 'w' for writing text
            file.write(decoded_body)
            self.log(f'Saved file {filename}')


    def _requests_to_follow(self, response):
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                    if lnk not in seen]
            if links and rule.process_links:
                
                for link in links:
                    print("link.url is :", link.url)
                    if link.url == "https://mybcom.sauder.ubc.ca/courses-money-enrolment/options" :
                        print("_requests_to_follow found the options webpage in pre-process_links : ", response.url)

                links = rule.process_links(links)

                for link in links:
                    if link.url == "https://mybcom.sauder.ubc.ca/courses-money-enrolment/options" :
                        print("_requests_to_follow found the options webpage in post-process_links : ", response.url)
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
