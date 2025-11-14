import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

# Bot to scan the website and generate a sitemap 

class SitemapSpider(CrawlSpider):
    name = 'sitemap_spider'
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (compatible; SitemapBot/1.0)',
        'ROBOTSTXT_OBEY': True,  # Respects robots.txt
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.5,
        'DEPTH_LIMIT': 3, 
        'CLOSESPIDER_PAGECOUNT': 100, 
        'LOG_LEVEL': 'INFO', 
    }
    
    rules = (
        Rule(
            LinkExtractor(
                allow_domains=None, # type: ignore
                deny_extensions=[
                    'pdf', 'zip', 'tar', 'gz', 'rar', '7z',
                    'exe', 'bin', 'dmg', 'iso',
                    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'ico',
                    'mp3', 'mp4', 'avi', 'mov', 'wmv', 'flv',
                    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                ]
            ),
            callback='parse_page',
            follow=True
        ),
    )
    
    def __init__(self, start_url, *args, **kwargs):
        super(SitemapSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.sitemap_data = []
        self.crawled_count = 0
    
    def parse_page(self, response):
        self.crawled_count += 1
        
        # Log progress
        self.logger.info(f'Crawled page {self.crawled_count}: {response.url}')
        
        # Collect page data
        page_data = {
            'url': response.url,
            'status': response.status,
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'priority': self.calculate_priority(response.url),
            'title': response.css('title::text').get(),
        }
        
        self.sitemap_data.append(page_data)
        
        return page_data
    
    def calculate_priority(self, url):
        path = urlparse(url).path
        depth = len([p for p in path.split('/') if p])
        
        if depth == 0:
            return '1.0'  # Homepage
        elif depth == 1:
            return '0.8'  # Top-level pages
        elif depth == 2:
            return '0.6'  # Second-level pages
        else:
            return '0.4'  # Deeper pages
    
    def closed(self, reason):
        self.logger.info(f'Spider closed: {reason}')
        self.logger.info(f'Total pages crawled: {len(self.sitemap_data)}')
        self.generate_xml_sitemap()
        self.generate_report()
    
    def generate_xml_sitemap(self, filename='sitemap.xml'):
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        for page in self.sitemap_data:
            if page['status'] == 200:
                url_element = ET.SubElement(urlset, 'url')
                
                loc = ET.SubElement(url_element, 'loc')
                loc.text = page['url']
                
                lastmod = ET.SubElement(url_element, 'lastmod')
                lastmod.text = page['lastmod']
                
                priority = ET.SubElement(url_element, 'priority')
                priority.text = page['priority']
        
        tree = ET.ElementTree(urlset)
        ET.indent(tree, space='  ')
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        self.logger.info(f'XML sitemap saved to {filename}')
    
    def generate_report(self, filename='sitemap_report.txt'):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('=' * 70 + '\n')
            f.write('SITEMAP GENERATION REPORT\n')
            f.write('=' * 70 + '\n\n')
            f.write(f'Start URL: {self.start_urls[0]}\n')
            f.write(f'Total Pages Crawled: {len(self.sitemap_data)}\n')
            f.write(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            
            f.write('-' * 70 + '\n')
            f.write('CRAWLED URLS\n')
            f.write('-' * 70 + '\n\n')
            
            for i, page in enumerate(self.sitemap_data, 1):
                status_mark = '✓' if page['status'] == 200 else '✗'
                f.write(f"{i}. {status_mark} [{page['status']}] {page['url']}\n")
                if page['title']:
                    f.write(f"   Title: {page['title']}\n")
                f.write(f"   Priority: {page['priority']}\n\n")
            
            f.write('=' * 70 + '\n')
        
        self.logger.info(f'Text report saved to {filename}')


def run_sitemap_generator(start_url, max_pages=100, depth_limit=3, delay=0.5):

    print('\nStarting crawl...\n')
    
    # Update spider settings
    SitemapSpider.custom_settings.update({ # type: ignore
        'CLOSESPIDER_PAGECOUNT': max_pages,
        'DEPTH_LIMIT': depth_limit,
        'DOWNLOAD_DELAY': delay,
    })
    
    process = CrawlerProcess()
    
    process.crawl(SitemapSpider, start_url=start_url)
    process.start() 

if __name__ == '__main__':
    # Configuration
    START_URL = 'http://testphp.vulnweb.com/'
    MAX_PAGES = 100  
    DEPTH_LIMIT = 3  # (0 = unlimited)
    DELAY = 0.5 
    
    run_sitemap_generator(
        start_url=START_URL,
        max_pages=MAX_PAGES,
        depth_limit=DEPTH_LIMIT,
        delay=DELAY
    )
    
    print('\n' + '=' * 70)
    print('CRAWL COMPLETE!')
    print('=' * 70)
    print('Generated files:')
    print('  - sitemap.xml (XML sitemap for search engines)')
    print('  - sitemap_report.txt (Detailed crawl report)')
    print('=' * 70)