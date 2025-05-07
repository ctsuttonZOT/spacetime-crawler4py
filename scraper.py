import re
import json
import os
from nltk.corpus import words as english
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, urldefrag, urljoin
from bs4 import BeautifulSoup
from collections import defaultdict
from stopwords import STOPWORDS

# entire English dictionary
ENGLISH_WORDS = set(english.words())


class SeenURL:
    seen = {}

def remove_non_english_and_stopwords(words):
    # return a list of valid English non-stopwords
    return [word.lower() for word in words if word.lower() not in STOPWORDS and word in ENGLISH_WORDS]


def init_data():
    data = {
    "seen_urls": {},
    "unique_urls": 0,
    "longest_page": ["NULL", -1],
    "word_freqs": {},
    "subdomains": {},
    "total_subdomains": 0
    }

    with open("data_report.txt", 'w') as file:
        json.dump(data, file)


def update_data(url, words):
    # structure of data
    #####################
    # {
    # "seen_urls": dict{str: True},
    # "unique_urls": int,
    # "longest_page": tuple(str, int),
    # "word_freqs": dict{str: int},
    # "subdomains": dict{str: int},
    # "total_subdomains": int
    # }
    #####################

    # if the file is empty, initialize it with default data
    if os.stat("data_report.txt").st_size == 0:
        init_data()

    with open("data_report.txt", "r+") as file:
        data = json.load(file)

        # update unique URLs
        # remove fragment from URL
        url_minus_fragment = urldefrag(url)[0]

        if url_minus_fragment not in data["seen_urls"]:
            data["unique_urls"] += 1
            data["seen_urls"][url_minus_fragment] = True
        SeenURL.seen = data["seen_urls"]

        # update longest page
        # get word count
        word_count = len(words)

        # if word_count of current URL exceeds curr longest page, update the data
        if word_count > data["longest_page"][1]:
            data["longest_page"] = (url, word_count)

        # update word frequencies
        for word in words:
            if word in data["word_freqs"]:
                data["word_freqs"][word] += 1
            else:
                data["word_freqs"][word] = 1

        # update subdomains
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return

        elif hostname == "uci.edu" or hostname.endswith('.' + "uci.edu"):
            # increment total subdomains if subdomain is new 
            if hostname not in data["subdomains"]:
                data["total_subdomains"] += 1
            
            # increment subdomain in subdomain dict
            if hostname in data["subdomains"]:
                data["subdomains"][hostname] += 1
            else:
                data["subdomains"][hostname] = 1
        
        file.seek(0)
        json.dump(data, file)
        file.truncate()


def combine_url(base_url, subdomain):
    # join base url to subdomain url and remove any fragment(s)
    return urldefrag(urljoin(base_url, subdomain))[0]


def scraper(url, resp):
    if resp.status != 200 or not resp.raw_response:
        return []

    links = extract_next_links(url, resp)

    html = BeautifulSoup(resp.raw_response.content, 'html.parser')

    # extract text (excluding HTML markup) from HTML
    text = html.get_text(strip=True)
    words = text.split()

    # remove all non-English words and all stopwords from list of words
    words = remove_non_english_and_stopwords(words)

    res = [link for link in links if is_valid(link)]

    # update report data and write it to file (also grab list of seen URLs)
    update_data(url, words)

    return res


def extract_next_links(url, resp):
    html = BeautifulSoup(resp.raw_response.content, 'html.parser')
    urls = []

    for tag in html.find_all('a', href=True):
        urls.append(combine_url(url, tag["href"]))

    return urls


# function not used currently, may be used later
# def normalizeUrl(url):
#     parsed = urlparse(url)
#     query = parse_qs(parsed.query)

#     allowedParams = ['id', 'category', 'search', 'query', 'tags']
#     #lockedParams = ['do', 'rev', 'token', 'action', 'sid', 'user', 'access_token', 'diff', 'update', 'restore', 'sort', 'order']

#     filteredQuery = {k: v for k, v in query.items() if k in allowedParams}
#     #filteredQuery = {k: v for k, v in query.items() if k not in blockedParams}

#     newQuery = urlencode(filteredQuery, doseq=True)
#     return urlunparse(parsed._replace(query=newQuery))


def is_path_date(split_path: list) -> bool:
    #Checks if keywords for date are in the path.
    pattern = r'\d{4}[-/.]?\d{2}[-/.]?\d{2}'
    keywords = {"day", "month", "year", "date", "time"}
    for part in split_path:
        if (part.lower() in keywords): #Does Keywords check on the part of the path
            return True
        if (re.fullmatch(pattern, part)): #Does Number Pattern check on the part of the path
            return True
    return False


def is_query_date(query: dict) -> bool:
    #Checks if keywords for date are in the query.
    pattern = r'\d{4}[-/.]?\d{2}[-/.]?\d{2}'
    keywords = {"day", "month", "year", "date", "time"}
    for pair in query.items():
        if (pair[0].lower() in keywords):
            return True
        # pair[1] is a list of every query for the given keyword, will likely only be one item
        for item in pair[1]:
            if (re.fullmatch(pattern, item)):
                return True
    return False


def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        #Contains fragment
        if ("#" in url):
            url = url.split("#")[0] #Split at where it fragments into a list and get first element

        # moved fragment remover to normalizeUrl
        parsed = urlparse(url)# Splits into 6 parts: Scheme, netloc, path, params, query, fragment

        #Ex. Scheme="https", Netloc="www.helloworld.com", Path="/path/.../, Params="", query="query=int", Fragment="fragment" (Ignore)

        #Already Visited Website (No need to go back/potential infinite trap)
        if (urlunparse(parsed) in SeenURL.seen): #kyle changed
            return False

        if parsed.scheme not in set(["http", "https"]):
            return False

        domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]

        # gitlab is evil
        if parsed.hostname == "gitlab.ics.uci.edu":
            return False

        #Check to see if domain in netloc(subdomain + domain)
        if not any(domain in parsed.netloc for domain in domains):
            return False

        #Special Link since it has more than netloc to check
        if ("today.uci.edu" in parsed.netloc) and (parsed.path != "/department/information_computer_sciences/"):
            return False
        
        split_path = parsed.path.split("/")
        query_dict = parse_qs(parsed.query)

        if (is_path_date(split_path) or is_query_date(query_dict)):
            return False

        if re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|img"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
                + r"|sql|apk|bat)$", parsed.path.lower()):
            return False

        #Restore back to link form (String)
        parsed = urlunparse(parsed)

        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
