import requests

try:
    res = requests.post('http://localhost:8004/ai/search', json={'query': 'test', 'limit': 5})
    print("Search status:", res.status_code)
    print("Search response:", res.text)
except Exception as e:
    print(e)
