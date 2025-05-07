import json

def process_data(filename: str) -> None:
    with open(filename, 'r') as file:
        data = json.load(file)
    
    unique_urls = data["unique_urls"]
    longest_page = data["longest_page"]
    # only top 50 common words
    sorted_words = sorted(data["word_freqs"].items(), key=lambda item: item[1], reverse=True)
    filtered_words = []

    # filter out 1 letter "words"
    for word in sorted_words:
        if len(word[0]) > 1:
            filtered_words.append(word)

    filtered_words = filtered_words[:49]
    sorted_subdomains = sorted(data["subdomains"].items())
    num_subdomains = data["total_subdomains"]

    with open("report.txt", 'w') as file:
        file.write(f"# unique pages: {unique_urls}\n")
        file.write("--------------------\n")
        file.write(f"Longest page: URL = {longest_page[0]}, Length = {longest_page[1]}\n")
        file.write("--------------------\n")
        for word in filtered_words:
            file.write(f"{word[0]} - {word[1]}\n")
        file.write("--------------------\n")
        for subdomain in sorted_subdomains:
            file.write(f"{subdomain[0]} - {subdomain[1]}\n")
        file.write("--------------------\n")
        file.write(f"# of uci.edu subdomains: {num_subdomains}\n")


def main():
    process_data("data_dumps/data_report_8.txt")
    print("COMPLETE")


if __name__ == "__main__":
    main()