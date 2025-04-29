import re
from urllib.parse import urlparse, urlunparse, urldefrag, urljoin
from bs4 import BeautifulSoup
from collections import defaultdict
from stopwords import STOPWORDS

class ReportData:
    # num of unique URLs, discarding the fragment part
    unique_pages = 0

    # tuple containing a URL, and the number of words in the page with the most # of words
    longest_page = (None, -1)

    # a dict containing each found word and the frequency of it (will be sorted and constrained to top 50 at file write time)
    # key = word, value = frequency
    word_frequencies = defaultdict(int)

    # dict of all subdomains in the uci.edu domain, key = URL, value = # of unique pages in subdomain
    subdomains = {}

    # num of subdomains
    total_num_subdomains = 0


def write_data_to_file():
    # sort words in descending order by frequency
    sorted_words = sorted(ReportData.word_frequencies.items(), key=lambda item: item[1], reverse=True)
    # cut down to only 50 words if longer than 50
    if len(sorted_words) >= 50:
        sorted_words = sorted_words[:49]
    
    # sort subdomains in alphabetical order
    sorted_subdomains = sorted(ReportData.subdomains.items())

    with open("data_report.txt", 'w') as file:
        file.write(f"# unique pages: {ReportData.unique_pages}\n")
        file.write(f"Longest page: URL = {ReportData.longest_page[0]}, Length = {ReportData.longest_page[1]}\n")
        for word in sorted_words:
            file.write(f"{word[0]} - {word[1]}\n")
        for subdomain in sorted_subdomains:
            file.write(f"{subdomain[0]} - {subdomain[1]}\n")
        file.write(f"# of uci.edu subdomains: {ReportData.total_num_subdomains}\n")


def update_unique_pages(url) -> bool:
    # remove fragment from URL
    url_minus_fragment = urldefrag(url)[0]

    if url_minus_fragment not in ReportData.unique_pages:
        ReportData.unique_pages += 1
        write_data_to_file()


def update_longest_page(url, words):
    # get word count
    word_count = len(words)

    # if word_count of current URL exceeds curr longest page, update the data
    if word_count > ReportData.longest_page[1]:
        ReportData.longest_page = (url, word_count)
        write_data_to_file()


def update_word_frequencies(words):
    # update word frequencies
    for word in words:
        if word not in STOPWORDS:
            ReportData.word_frequencies[word] += 1
    write_data_to_file()


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
    if resp.status != 200:
        return []

    links = extract_next_links(url, resp)

    update_unique_pages(url)

    html = BeautifulSoup(resp.raw_response.content, 'html.parser')

    # extract text (excluding HTML markup) from HTML
    text = html.get_text(strip=True)
    words = text.split()

    update_longest_page(url, words)
    update_word_frequencies(words)

    # if a URL is a subdomain of uci.edu, count how many unique pages it has
    if is_subdomain(url):
        # increment num of total subdomains
        ReportData.num_subdomains += 1
        seen = set()
        # find each hyperlink in html
        for tag in html.find_all('a', href=True):
            # combine hyperlink with base url to get whole url
            link = combine_url(url, tag["href"])
            if link not in seen:
                seen.add(link)
        ReportData.subdomains[url] = len(seen)
        write_data_to_file()

    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    html = BeautifulSoup(resp.raw_response.content, 'html.parser')
    urls = []

    for tag in html.find_all('a', href=True):
        urls.append(combine_url(url, tag["href"]))

    return urls

visited = set()
def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:

        #Contains fragment
        if ("#" in url):
            parsed = url.split("#")[0] #Split at where it fragments into a list and get first element

        parsed = urlparse(url)# Splits into 6 parts: Scheme, netloc, path, params, query, fragment
        #Ex. Scheme="https", Netloc="www.helloworld.com", Path="/path/.../, Params="", query="query=int", Fragment="fragment" (Ignore)

        #Already Visited Website (No need to go back/potential infinite trap)
        if (parsed in visited):
            return False

        if parsed.scheme not in set(["http", "https"]):
            return False

        domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]

        #Check to see if domain in netloc(subdomain + domain)
        if not any(domain in parsed.netloc for domain in domains):
            return False

        #Special Link since it has more than netloc to check
        if ("today.uci.edu" in parsed.netloc) and (parsed.path != "/department/information_computer_sciences/"):
            return False

        path_size = len(parsed.path.split("/"))
        #Do not want URL with dates since these go to news pages, where it can infinitely loop and get stuck
        if (path_size > 3):
            possible_year = parsed.path.split("/")[1].isdigit()
            possible_month = parsed.path.split("/")[2].isdigit()
            possible_day = parsed.path.split("/")[3].isdigit()

            if (possible_year and possible_month and possible_day):
                return False

        if re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
                + r"|sql|apk|bat)$", parsed.path.lower()):
            return False

        #Restore back to link form (String)
        parsed = urlunparse(parsed)
        visited.add(parsed)

        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
