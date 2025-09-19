import sys
import subprocess
import os
import time

# ===== AUTO-INSTALL DEPENDENCIES =====
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for pkg in ["requests", "beautifulsoup4", "lxml", "fpdf2", "pillow", "selenium", "networkx", "matplotlib"]:
    try:
        __import__(pkg)
    except ImportError:
        print(f"[*] Installing {pkg}...")
        install(pkg)

import requests
from bs4 import BeautifulSoup
import re
import csv
from fpdf import FPDF
from PIL import Image
from io import BytesIO
import networkx as nx
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TOR_PROXY = 'socks5h://127.0.0.1:9050'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
MAX_SEARCH_PAGES = 2
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

SOCIAL_PLATFORMS = [
    "https://github.com/",
    "https://www.reddit.com/user/",
    "https://twitter.com/",
    "https://www.instagram.com/",
    "https://www.facebook.com/",
    "https://www.tiktok.com/@"
]

ONION_SITES = [
    'http://msydqstlz2kzerdg.onion/',
    'http://3g2upl4pq6kufc4m.onion/',
    'http://torlinks2mn2l3.onion/',
    'http://amg5evnwl2icg6jx.onion/',
    'http://zqktlwi4fecvo6ri.onion/'
]

def generate_usernames(name):
    parts = name.lower().split()
    usernames = []
    if len(parts) >= 2:
        usernames.append(parts[0] + parts[1])
        usernames.append(parts[0] + '.' + parts[1])
        usernames.append(parts[0][0] + parts[1])
        usernames.append(parts[0] + parts[1][0])
    usernames.append(''.join(parts))
    return list(set(usernames))

def search_surface_web(query, pages=MAX_SEARCH_PAGES):
    results = []
    for page in range(pages):
        start = page * 10
        url = f'https://www.bing.com/search?q="{query}"&first={start}'
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, 'lxml')
            for item in soup.select('li.b_algo'):
                title = item.find('h2').text if item.find('h2') else ''
                link = item.find('a')['href'] if item.find('a') else ''
                snippet = item.find('p').text if item.find('p') else ''
                results.append({'source': 'Surface Web', 'title': title, 'url': link, 'snippet': snippet})
            time.sleep(1)
        except:
            continue
    return results

def search_social_media(usernames):
    results = []
    for u in usernames:
        for platform in SOCIAL_PLATFORMS:
            url = platform + u
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    results.append({'source': platform, 'title': f'Username: {u}', 'url': url, 'snippet': 'Profile found'})
            except:
                continue
    return results

def search_dark_web(name):
    results = []
    session = requests.Session()
    session.proxies = {'http': TOR_PROXY, 'https': TOR_PROXY}
    for onion in ONION_SITES:
        try:
            r = session.get(onion, headers=HEADERS, timeout=15)
            if r.status_code == 200 and name.lower() in r.text.lower():
                results.append({'source': onion, 'title': 'Name Found', 'url': onion, 'snippet': 'Mention found on page'})
            time.sleep(1)
        except:
            continue
    return results

def extract_emails(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)

def save_to_csv(data, filename='people_report.csv'):
    if not data:
        print("[!] No data to save.")
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"[*] CSV report saved to '{filename}'.")

def take_screenshot(url, name, index):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1200, 800)
        driver.get(url)
        filepath = os.path.join(SCREENSHOT_DIR, f"screenshot_{index}.png")
        driver.save_screenshot(filepath)
        driver.quit()
        return filepath
    except:
        return None

def create_pdf(data, filename='people_report.pdf'):
    if not data:
        print("[!] No data for PDF.")
        return
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "OSINT Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", '', 12)
    
    for i, item in enumerate(data, start=1):
        pdf.multi_cell(0, 8, f"{i}. Source: {item['source']}\nTitle: {item['title']}\nURL: {item['url']}\nEmails: {item.get('emails','')}\nSnippet: {item['snippet']}\n")
        screenshot = take_screenshot(item['url'], item['title'], i)
        if screenshot:
            pdf.image(screenshot, w=100)
        pdf.ln(5)
    pdf.output(filename)
    print(f"[*] PDF report saved to '{filename}'.")

def create_connection_graph(data, filename='connections.png'):
    G = nx.Graph()
    for item in data:
        node_label = item['title'] if item['title'] else item['url']
        G.add_node(node_label)
        # connect emails to node
        for email in item.get('emails','').split(', '):
            if email:
                G.add_node(email)
                G.add_edge(node_label, email)
    plt.figure(figsize=(12,8))
    nx.draw(G, with_labels=True, node_size=2000, node_color="skyblue", font_size=10, font_weight="bold")
    plt.savefig(filename)
    print(f"[*] Connection graph saved to '{filename}'.")

def main():
    name = input("Enter the full name of the person: ")
    usernames = generate_usernames(name)
    
    print("[*] Searching surface web...")
    surface_results = search_surface_web(name)
    
    print("[*] Searching social media usernames...")
    social_results = search_social_media(usernames)
    
    print("[*] Searching dark web...")
    dark_results = search_dark_web(name)
    
    all_results = surface_results + social_results + dark_results
    
    for r in all_results:
        r['emails'] = ', '.join(extract_emails(r['snippet']))
    
    save_to_csv(all_results)
    create_pdf(all_results)
    create_connection_graph(all_results)
    
    print(f"[*] Done! Found {len(all_results)} results.")

if __name__ == "__main__":
    main()
