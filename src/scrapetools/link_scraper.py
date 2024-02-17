from typing import Any
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup


class LinkScraper:
    def __init__(self, html_src: str, page_url: str):
        self.soup = BeautifulSoup(html_src, features="html.parser")
        self.parsed_url = urlparse(page_url)
        self.page_links = []
        self.img_links = []
        self.script_links = []

    def format_relative_links(self, links: list[str]) -> list[str]:
        """Parses list of links and constructs a full url
        according to self.parsed_url for the ones that don't have a
        'netloc' property returned by urlparse.

        Full urls are returned unedited other than stripping any
        leading or trailing forward slashes."""
        formatted_links: list[str] = []
        for link in links:
            link = (
                link.strip(" \n\t\r")
                .replace('"', "")
                .replace("\\", "")
                .replace("'", "")
            )
            parsed_url = urlparse(link)
            if all(ch not in link for ch in "@ "):
                parsed_url = list(parsed_url)
                if parsed_url[0] == "":
                    parsed_url[0] = self.parsed_url.scheme
                if parsed_url[1] == "":
                    parsed_url[1] = self.parsed_url.netloc
                formatted_links.append(urlunparse(parsed_url).strip("/"))
        return formatted_links

    def remove_duplicates(self, obj: list[Any]) -> list[Any]:
        """Removes duplicate members."""
        return list(set(obj))

    def process_links(self, links: list[str]) -> list[str]:
        """Formats relative links, removes duplicates, and sorts in alphabetical order."""
        return sorted(self.remove_duplicates(self.format_relative_links(links)))

    def find_all(self, tag_name: str, attribute_name: str) -> list[str]:
        """Finds all results according to tag_name and attribute_name.\n
        Filters out fragments."""
        return [
            tag.get(attribute_name)
            for tag in self.soup(tag_name, recursive=True)
            if tag.get(attribute_name) is not None
            and "#" not in tag.get(attribute_name)
        ]

    def filter_same_site(self, links: list[str]) -> list[str]:
        """Filters out links that don't match self.parsed_url.netloc"""
        return [
            link
            for link in links
            if urlparse(link).netloc.strip("www.")
            == self.parsed_url.netloc.strip("www.")
        ]

    def scrape_page_links(self):
        """Scrape links according to tags and attributes."""
        links: list[str] = []
        for tag, attribute in [
            ("a", "href"),
            ("link", "href"),
            ("source", "src"),
            ("div", "src"),
            ("div", "data-src"),
            ("div", "data-url"),
            ("div", "href"),
        ]:
            links.extend(self.find_all(tag, attribute))
        self.page_links = self.process_links(links)

    def scrape_img_links(self):
        """Scrape links from src attribute of <img> tags."""
        self.img_links = self.process_links(
            self.find_all("img", "src") + self.find_all("img", "data-src")
        )

    def scrape_script_links(self):
        """Scrape script links from src attribute of <script> tags."""
        self.script_links = self.process_links(self.find_all("script", "src"))

    def scrape_page(self):
        """Scrape all link types."""
        for scrape in [
            self.scrape_page_links,
            self.scrape_img_links,
            self.scrape_script_links,
        ]:
            scrape()
        self.merge_image_links_from_non_img_tags()

    def merge_image_links_from_non_img_tags(self):
        """Finds links in self.script_links and self.page_links
        that have one of these image file extensions and adds them
        to self.img_links"""
        formats = [
            ".jpg",
            ".jpeg",
            ".png",
            ".svg",
            ".bmp",
            ".tiff",
            ".pdf",
            ".eps",
            ".gif",
            ".jfif",
            ".webp",
            ".heif",
            ".avif",
            ".bat",
            ".bpg",
        ]
        for link in self.script_links + self.page_links:
            if any(ext in link for ext in formats):
                self.img_links.append(link)
        self.img_links = sorted(self.remove_duplicates(self.img_links))

    def get_links(
        self,
        link_type: str = "all",
        same_site_only: bool = False,
        excluded_links: list[str] | None = None,
    ) -> list[str]:
        """Returns a list of urls found on the page.

        :param link_type: Can be 'all', 'page', 'img', or 'script'.

        :param same_site_only: Excludes external urls if True.

        :param excluded_links: A list of urls to filter out of the results.
        Useful for excluding duplicates when recursively scraping a website.
        Can also be used with link_type='all' to get two link types in one call:

        e.g. links = scraper.get_links(link_type = 'all', excluded_links = scraper.script_links)
        will return page links and img links."""
        match link_type:
            case "all":
                links = self.remove_duplicates(
                    self.page_links + self.img_links + self.script_links
                )
            case "page":
                links = self.page_links
            case "img":
                links = self.img_links
            case "script":
                links = self.script_links
            case _:
                links = []
        if same_site_only:
            links = self.filter_same_site(links)
        if excluded_links:
            links = [link for link in links if link not in excluded_links]
        return sorted(links)
