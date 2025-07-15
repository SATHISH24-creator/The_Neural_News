from bs4 import BeautifulSoup

def clean_html_tags(text):
    """Remove HTML tags and return clean text."""
    soup = BeautifulSoup(text, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_before("\n")
    return soup.get_text(separator=" ", strip=True)