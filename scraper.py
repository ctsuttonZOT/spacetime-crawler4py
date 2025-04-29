import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from collections import defaultdict
from stopwords import STOPWORDS

class ReportData:
    # set of unique URLs, discarding the fragment part
    unique_pages = set()

    # tuple containing a URL, and the number of words in the page with the most # of words
    longest_page = (None, -1)

    # a dict containing each found word and the frequency of it (will be sorted and constrained to top 50 at file write time)
    # key = word, value = frequency
    word_frequencies = defaultdict(int)

    # dict of all subdomains in the uci.edu domain, key = URL, value = # of unique pages in subdomain
    subdomains = {}


def update_unique_pages(url) -> bool:
    # remove fragment from URL
    url_minus_fragment = urldefrag(url)[0]

    if url_minus_fragment not in ReportData.unique_pages:
        ReportData.unique_pages.add(url_minus_fragment)


def update_longest_page(url, words):
    # get word count
    word_count = len(words)

    # if word_count of current URL exceeds curr longest page, update the data
    if word_count > ReportData.longest_page[1]:
        ReportData.longest_page = (url, word_count)


def update_word_frequencies(words):
    # update word frequencies
    for word in words:
        if word not in STOPWORDS:
            ReportData.word_frequencies[word] += 1


def is_subdomain(url) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname

    if not hostname:
        return False
    
    return hostname == "uci.edu" or hostname.endswith('.' + "uci.edu")


def combine_url(base_url, subdomain):
    # join base url to subdomain url and remove any fragment(s)
    return urldefrag(urljoin(base_url, subdomain))[0]


def scraper(url, resp):
    links = extract_next_links(url, resp)

    update_unique_pages(url)
    
    # extract text (excluding HTML markup) from HTML
    text = BeautifulSoup.get_text(seperator=' ')
    words = text.split()
    words.strip()

    update_longest_page(url, words)
    update_word_frequencies(words)
    
    if is_subdomain(url):
        seen = set()
        html = BeautifulSoup(resp.raw_response.content, 'html')
        # find each hyperlink in html
        for tag in html.find_all('a', href=True):
            # combine hyperlink with base url to get whole url
            link = combine_url(url, tag["href"])
            if link not in seen:
                seen.add(link)
        ReportData.subdomains[url] = len(seen)

    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    html = BeautifulSoup(resp.raw_response.content, 'html')
    urls = []

    for link in html.find_all('a', href=True):
        urls.append(combine_url(url, link))

    return urls

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:

        parsed = urlparse(url)# Splits into 6 parts: Scheme, netloc, path, params, query, fragment
        #Ex. Scheme="https", Netloc="www.helloworld.com", Path="/path/.../, Params="", query="query=int", Fragment="fragment"
        if parsed.scheme not in set(["http", "https"]):
            return False

        domains = ["ics.uci.edu", "ics.uci.edu", "informatics.uci.edu", "stat.uci.edu"]

        #Check to see if domain in netloc(subdomain + domain)
        if not any(domain in parsed.netloc for domain in domains):
            return False

        #Special Link since it has more than netloc to check
        if ("today.uci.edu" in parsed.netloc) and (parsed.path != "/department/information_computer_sciences/"):
            return False


        #As long as it is not any of these extensions, it returns True
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|sql|apk|bat)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
