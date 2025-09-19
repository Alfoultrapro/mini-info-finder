import os
import re
import csv
import time
import urllib.request
from urllib.error import URLError, HTTPError
from html import unescape
from datetime import datetime

HEADERS = {'User-Agent': 'Mozilla/5.0'}

SOCIAL_PLATFORMS = [
    "https://github.com/",
    "https://www.reddit.com/user/",
    "https://twitter.com/",
    "https://www.instagram.com/",
    "https://www.facebook.com/",
    "https://www.tiktok.com/@"
]

def generate_usernames(name):
    parts = name.lower().split()
    usernames = set()
    if len(parts) >= 2:
        first, last = parts[0], parts[-1]
        usernames.update([
            first+last,
            first+'.'+last,
            first[0]+last,
            first+last[0],
            last+first,
            last+'.'+first,
            last+first[0],
            first+last+'_',
            first+'_'+last,
            last+'_'+first,
            first[0]+'.'+last
        ])
    else:
        usernames.add(parts[0])
    return list(usernames)

def clean_html(text):
    text = re.sub(r'<.*?>', '', text)
    return unescape(text.strip())

def search_bing(name, pages=1):
    results = []
    for page in range(pages):
        start = page*10
        url = f'https://www.bing.com/search?q="{name}"&first={start}'
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                links = re.findall(r'<a href="(http[s]?://[^"]+)"', html)
                snippets = re.findall(r'<p>(.*?)</p>', html)
                for i in range(min(len(links), len(snippets))):
                    snippet = clean_html(snippets[i])
                    results.append({'source':'Bing','title':links[i],'url':links[i],'snippet':snippet})
            time.sleep(1)
        except:
            continue
    return results

def search_social(usernames):
    results=[]
    for u in usernames:
        for platform in SOCIAL_PLATFORMS:
            url = platform + u
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=5):
                    results.append({'source':platform,'title':f'Username: {u}','url':url,'snippet':'Profile found'})
            except (HTTPError, URLError):
                continue
    return results

def extract_emails(text):
    return re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)

def save_csv(data):
    if not data:
        print("No results found.")
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file = f'report_{timestamp}.csv'
    keys = data[0].keys()
    with open(file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in data:
            row['url'] = f'=HYPERLINK("{row["url"]}", "{row["url"]}")'
            writer.writerow(row)
    print(f"CSV saved to '{file}'.")

def main():
    name = input("Enter full name: ")
    usernames = generate_usernames(name)
    print(f"Generated {len(usernames)} username variations for social media.")
    data = []
    data += search_bing(name)
    data += search_social(usernames)
    for r in data:
        r['emails'] = ','.join(extract_emails(r['snippet']))
    save_csv(data)
    print(f"Done! Found {len(data)} results.")

if __name__ == "__main__":
    main()
