# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


# middlewares.py

import random
import scrapy
from fp.fp import FreeProxy
from scrapy.exceptions import IgnoreRequest
import requests


class ScrapeOpsProxyMiddleware:
    def __init__(self, scrapeops_api_key, proxy_url):
        self.api_key = scrapeops_api_key
        self.proxy_url = proxy_url

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            scrapeops_api_key=crawler.settings.get('SCRAPEOPS_API_KEY'),
            proxy_url='https://proxy.scrapeops.io/v1/'
        )

    def fetch_proxy(self, target_url):
        # print("api key is :", self.api_key)

        # Fetch a proxy from ScrapeOps
        response = requests.get(self.proxy_url, params={
            'api_key': self.api_key,
            'url': target_url, 
            })
        if response.status_code == 200:
            print("fetch proxy response value is :", response.json().get('proxy'))
            data = response.json()
            if data.get('status') == 'success':
                return data.get('proxy')
            else:
                raise IgnoreRequest("Failed to fetch proxy from ScrapeOps, response data: {}".format(data))
        else:
            raise IgnoreRequest("Failed to fetch proxy from ScrapeOps, HTTP status: {}".format(response.status_code))

    
    def process_request(self, request, spider):
        proxy = self.fetch_proxy(request.url)
        if proxy:
            request.meta['proxy'] = proxy
        else:
            raise IgnoreRequest("No proxy available for {}".format(request.url))

    def process_response(self, request, response, spider):
        if response.status in [403, 429, 503]:
            new_request = request.copy()
            new_request.dont_filter = True
            new_request.meta['proxy'] = self.fetch_proxy(request.url)
            return new_request
        return response

    def process_exception(self, request, exception, spider):
        return request.replace(meta={'proxy': self.fetch_proxy(request.url)})



class ConcisMlSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ConcisMlDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


# class BlockedURLMiddleware:
#     def __init__(self):
#         self.processed_urls = set()

#     def process_response(self, request, response, spider):
#         if response.status == 429 and request.url not in self.processed_urls:
#             # This is the first time encountering a blocked response for this URL
#             self.processed_urls.add(request.url)
#             spider.logger.warning(f"Blocked URL: {request.url}")

#         return response
    

class FreeProxyMiddleware:
    def __init__(self):
        self.retried_urls = set()

    def process_request(self, request, spider):
        if request.url in self.retried_urls:
            # Prevent further processing of URLs that have been retried and blocked
            print(f"Blocking further attempts for URL: {request.url}")
            raise IgnoreRequest(f"URL blocked on previous attempts: {request.url}")
        
        # Use FreeProxy to get a new proxy
        proxy = FreeProxy(timeout=1, rand=True).get()
        print("proxy received :", proxy)
        request.meta['proxy'] = proxy

    def process_response(self, request, response, spider):

        # If response status indicates a block, retry with a new proxy
        if response.status in [403, 429, 503] and request.url not in self.processed_urls:
            # This is the first time encountering a blocked response for this URL
            self.processed_urls.add(request.url)

            # Retry the webpage
            new_request = request.copy()
            new_request.dont_filter = True
            return new_request
        elif response.status in [403, 429, 503] and request.url in self.retried_urls:
            print(f"Blocked on second try for URL: {request.url}")
            
        return response

