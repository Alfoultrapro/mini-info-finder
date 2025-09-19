import os, requests, re, csv, time
from bs4 import BeautifulSoup
from fpdf import FPDF
from PIL import Image
from io import BytesIO
import networkx as nx
import matplotlib.pyplot as plt
import socket

TOR_PROXY = 'socks5h://127.0.0.1:9050'
HEADERS = {'User-Agent': 'Mozilla/5.0'}
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

def tor_running(host='127.0.0.1', port=9050):
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        return True
    except:
        return False

def generate_usernames(name):
    parts = name.lower().split()
    usernames = []
    if len(parts) >= 2:
        usernames.append(parts[0]+parts[1])
        usernames.append(parts[0]+'.'+parts[1])
        usernames.append(parts[0][0]+parts[1])
        usernames.append(parts[0]+parts[1][0])
    usernames.append(''.join(parts))
    return list(set(usernames))

def search_bing(name, pages=1):
    results = []
    for page in range(pages):
        start = page*10
        url = f'https://www.bing.com/search?q="{name}"&first={start}'
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, 'lxml')
            for item in soup.select('li.b_algo'):
                title = item.find('h2').text if item.find('h2') else ''
                link = item.find('a')['href'] if item.find('a') else ''
                snippet = item.find('p').text if item.find('p') else ''
                results.append({'source':'Bing','title':title,'url':link,'snippet':snippet})
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
                r = requests.get(url, headers=HEADERS, timeout=5)
                if r.status_code==200:
                    results.append({'source':platform,'title':f'Username: {u}','url':url,'snippet':'Profile found'})
            except:
                continue
    return results

def search_dark_web(name):
    results=[]
    if not tor_running():
        return results
    s = requests.Session()
    s.proxies={'http':TOR_PROXY,'https':TOR_PROXY}
    for onion in ONION_SITES:
        try:
            r = s.get(onion, headers=HEADERS, timeout=10)
            if r.status_code==200 and name.lower() in r.text.lower():
                results.append({'source':onion,'title':'Name Found','url':onion,'snippet':'Mention found'})
            time.sleep(1)
        except:
            continue
    return results

def extract_emails(text):
    return re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)

def save_csv(data, file='report.csv'):
    if not data: return
    keys=data[0].keys()
    with open(file,'w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

def create_pdf(data, file='report.pdf'):
    if not data: return
    pdf=FPDF()
    pdf.add_page()
    pdf.set_font("Arial",'B',16)
    pdf.cell(0,10,"OSINT Report",ln=True,align="C")
    pdf.set_font("Arial",'',12)
    for i,item in enumerate(data,1):
        pdf.multi_cell(0,8,f"{i}. Source: {item['source']}\nTitle: {item['title']}\nURL: {item['url']}\nEmails: {item.get('emails','')}\nSnippet: {item['snippet']}\n")
    pdf.output(file)

def create_graph(data, file='connections.png'):
    G=nx.Graph()
    for item in data:
        node=item['title'] if item['title'] else item['url']
        G.add_node(node)
        for e in item.get('emails','').split(', '):
            if e: G.add_node(e); G.add_edge(node,e)
    plt.figure(figsize=(12,8))
    nx.draw(G, with_labels=True, node_size=2000, node_color='skyblue', font_size=10, font_weight='bold')
    plt.savefig(file)

def main():
    name=input("Enter full name: ")
    usernames=generate_usernames(name)
    data=[]
    data+=search_bing(name)
    data+=search_social(usernames)
    data+=search_dark_web(name)
    for r in data:
        r['emails']=','.join(extract_emails(r['snippet']))
    save_csv(data)
    create_pdf(data)
    create_graph(data)
    print(f"Done! {len(data)} results found.")

if __name__=="__main__":
    main()
