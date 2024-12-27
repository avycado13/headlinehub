import datetime
import requests
from bs4 import BeautifulSoup


def find_articles(soup, url):
    if 'text.npr.org' in url:
        return (a_link for section in soup.find_all('div', class_='topic-container') for a_link in section.find_all('a'))
    return (a_link for section in soup.find_all('section') for a_link in section.find_all('a'))


def get_content(urls):
    # Initialize an empty string to hold the HTML content
    html_content = '<!DOCTYPE html>\n<html>\n<body>\n'

    for url in urls:
        # Make a request to the website
        r = requests.get(url, timeout=10)

        # Parse the website using BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        html_content += f'HeadlineHub for {datetime.date.today()}\n'
        # Add the URL to the HTML content
        html_content += f'<h2><a href={url}>{url}</h2><br/>\n'
        html_content += '<ul>\n'

        # Write each link to the HTML content
        for a_href in find_articles(soup, url):
            html_content += f'<li>{a_href}</li><br/>\n'

        html_content += '</ul>\n'

    # Close the HTML tags
    html_content += '</body>\n</html>\n'
    return html_content
