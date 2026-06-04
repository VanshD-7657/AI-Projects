import os
import requests 
from tavily import TavilyClient
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")
client = TavilyClient(api_key=api_key)

def search_hotels(query):
    response = client.search(query=query, max_results=5)
    results = []
    
    for i,r in enumerate(response['results'],1):
        title = r.get('title', 'Unknown')
        url = r.get('url', '')
        snippet = r.get('content', '').strip()

        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(' ', 1)[0] + '...'

        results.append(f"{i}. {title}\nURL: {url}\nSnippet: {snippet}\n")
    
    return "\n\n".join(results)


