# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo
from difflib import unified_diff
import os
from datetime import datetime

from dotenv import load_dotenv
import os


class MongoPipeline(object):
    """
    Pipeline for storing scraped items in MongoDB

        So db shows the university
        collection shows the faculty
        and docs in collection shows a single webpage in that faculty
    """  
    def open_spider(self, spider):
        # Database name is the name of the spider
        self.db_name = spider.name
        # Collection name is set to the faculty attribute of the spider
        self.collection_name = getattr(spider, 'faculty', 'default_collection')

        load_dotenv()
        # Retrieve the MongoDB URI from settings
        db_uri = os.getenv('MONGO_URL')  # Use os.getenv to get the environment variable


        # Establish a connection to the MongoDB server
        self.db_client = pymongo.MongoClient(db_uri)
        # Connect to the specified database
        self.db = self.db_client[self.db_name]

        # Create a new directory for logs if it doesn't exist
        logs_dir = 'web_scraper/content_change_logs'
        os.makedirs(logs_dir, exist_ok=True)

        # Create a filename with the current date, including hour and minute
        date_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        self.change_log_filename = os.path.join(logs_dir, f'changes_{spider.name}_{spider.faculty}_{date_time_str}.txt')

        # Open the file for logging changes
        self.file = open(self.change_log_filename, 'w')



    def process_item(self, item, spider):
        meta_data = item.get('meta_data', {})

        # Example usage of start_url from meta_data
        start_url = meta_data.get('start_url')
        if start_url is not None:
            # No need to log the start URL for now, because its confirmed it was working
            #print(f"Processing item from start URL: {start_url}")
            pass
            
        # Function tag
        #func_tag = "[process_item]"
        func_tag = ""

        # Convert item to dict
        item_dict = ItemAdapter(item).asdict()
        item_dict.pop('meta_data', None)
        
        # Check if the URL of the item already exists in the collection
        existing = self.db[self.collection_name].find_one({'url': item['url']})

        if existing:
            # Calculate differences
            old_content = existing['text']
            new_content = item_dict['text']

            # diff = unified_diff(old_content, new_content, lineterm='', fromfile='old', tofile='new', n=0)
            diff = list(unified_diff(old_content.splitlines(), new_content.splitlines(), lineterm=''))

            # Log changes to a file with URL as a title
            if diff:
                self.file.write(f"Changes for URL: {item['url']}\n")
                self.file.write('\n'.join(diff) + '\n\n')

                # Update the document in MongoDB with the new content
                self.db[self.collection_name].replace_one({'url': item['url']}, item_dict)
                spider.logger.info(f"Updated item with changes: {item['url']}")
            else:
                spider.logger.info(f"No change detected: {item['url']}")
        else:
            # If the item does not exist, insert it
            self.db[self.collection_name].insert_one(item_dict)
            spider.logger.info(f"Inserted new item: {item['url']}")

        return item

    def close_spider(self, spider):
        # Close the connection to the MongoDB server
        self.db_client.close()
        # Close the changes file
        self.file.close()

