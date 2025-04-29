import re
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
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

    for link in html.findall('a'):
        urls.append(link.get('href'))

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

        #Already Visited Website (No need to go back/potential infinite trap)
        if (parsed in visited):
            return False

        parsed = urlparse(url)# Splits into 6 parts: Scheme, netloc, path, params, query, fragment
        #Ex. Scheme="https", Netloc="www.helloworld.com", Path="/path/.../, Params="", query="query=int", Fragment="fragment" (Ignore)

        if parsed.scheme not in set(["http", "https"]):
            return False

        domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]

        #Check to see if domain in netloc(subdomain + domain)
        if not any(domain in parsed.netloc for domain in domains):
            return False

        #Special Link since it has more than netloc to check
        if ("today.uci.edu" in parsed.netloc) and (parsed.path != "/department/information_computer_sciences/"):
            return False

        #Do not want URL with dates since these go to news pages, where it can infinitely loop and get stuck
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
