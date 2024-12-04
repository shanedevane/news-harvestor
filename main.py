import csv
import os
import time
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from colorama import Fore, init
from googlesearch import search
from weasyprint import HTML

init(autoreset=True)


def get_external_links(url, domain):
    """Extract external links from a webpage."""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        external_links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            parsed_href = urlparse(href)

            # Make absolute URL if relative
            if not parsed_href.netloc:
                if href.startswith('/'):
                    href = f"https://{domain}{href}"
                else:
                    continue

            # Check if it's an external link (not from the original domain)
            if domain not in href:
                external_links.add(href)

        return external_links
    except Exception as e:
        print(f"{Fore.RED}Error fetching links from {url}: {str(e)}")
        return set()


def main():
    print(f"{Fore.CYAN}Starting news harvesting process...")

    # Create data directory
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    domains = ["esgdive.com/news/", "sustainability-news.net/tag/news/", "esgtoday.com", "integratedreporting.ifrs.org/news/", "future.portfolio-adviser.com/news-home/"]
    pdf_directory = os.path.join(data_dir, "downloaded_pdfs")
    csv_file = os.path.join(data_dir, "tracked_urls.csv")

    os.makedirs(pdf_directory, exist_ok=True)

    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            csv.writer(file).writerow(['Timestamp', 'Source URL', 'External URL', 'PDF Path', 'Status'])

    tracked_urls = set()
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as file:
            tracked_urls = {row[2] for row in csv.reader(file) if len(row) > 2}

    for domain in domains:
        print(f"\n{Fore.CYAN}Processing domain: {domain}")
        # Modified search query to specifically target Google News
        search_query = f"site:{domain}"

        try:
            # Updated search parameters to target Google News
            for source_url in search(search_query, tld="com", num=10, stop=100, pause=2, extra_params={'tbm': 'nws'}):
                print(f"\n{Fore.CYAN}Checking source URL: {source_url}")

                # Get external links from the page
                external_links = get_external_links(source_url, domain)

                for ext_url in external_links:
                    if ext_url not in tracked_urls:
                        print(f"{Fore.YELLOW}Processing external URL: {ext_url}")

                        parsed_url = urlparse(ext_url)
                        filename = f"{parsed_url.netloc}-{parsed_url.path.replace('/', '-')}.pdf".rstrip('-')
                        pdf_path = os.path.join(pdf_directory, filename)

                        try:
                            HTML(url=ext_url).write_pdf(pdf_path)
                            status = "Success"
                            print(f"{Fore.GREEN}Successfully created PDF: {pdf_path}")
                        except Exception as e:
                            status = f"Error: {str(e)}"
                            print(f"{Fore.RED}PDF conversion failed: {str(e)}")

                        with open(csv_file, 'a', newline='', encoding='utf-8') as file:
                            csv.writer(file).writerow([datetime.now(), source_url, ext_url, pdf_path, status])

                        tracked_urls.add(ext_url)
                        time.sleep(2)
                    else:
                        print(f"{Fore.BLUE}Skipping already processed URL: {ext_url}")

                time.sleep(2)
        except Exception as e:
            print(f"{Fore.RED}Error processing domain {domain}: {str(e)}")

    print(f"\n{Fore.GREEN}News harvesting process completed!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Process interrupted by user")
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {str(e)}")