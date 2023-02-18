# Scrapetools
A collection of tools to aid in web scraping.<br>
Install using:
<pre>pip install scrapetools</pre>
Scrapetools contains three functions (scrape_emails, scrape_phone_numbers, scrape_inputs)
and one class (LinkScraper).
<br>
## Basic usage
<pre>
import scrapetools
import requests

url = 'https://somewebsite.com'
source = requests.get(url).text

emails = scrapetools.scrape_emails(source)

phoneNumbers = scrapetools.scrape_phone_numbers(source)

scraper = scrapetools.LinkScraper(source, url)
scraper.scrape_page()
# links can be accessed and filtered via the get_links() function
same_site_links = scraper.get_links(same_site_only=True)
same_site_image_links = scraper.get_links(link_type='img', same_site_only=True)
external_image_links = scraper.get_links(link_type='img', excluded_links=same_site_image_links)

# scrape_inputs() returns a tuple of BeautifulSoup Tag elements for various user input elements
forms, inputs, buttons, selects, text_areas = scrapetools.scrape_inputs(source)
</pre>
