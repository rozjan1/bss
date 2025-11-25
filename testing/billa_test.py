import requests
import json

cookies = {
    'XSRF-TOKEN': '051252ef-de51-4905-a88c-f01a832363df',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'cs-CZ,cs;q=0.5',
    'cache-control': 'no-cache',
    'credentials': 'include',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://shop.billa.cz/produkty/ovoce-a-zelenina-1165',
    'sec-ch-ua': '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'x-request-id': '590c4ee7-a428-4fb1-8024-95344422e0b9-1762887186651',
    'x-xsrf-token': '051252ef-de51-4905-a88c-f01a832363df',
    # 'cookie': 'XSRF-TOKEN=051252ef-de51-4905-a88c-f01a832363df',
}

params = {
    'page': '0',
    'sortBy': 'relevance',
    'enableStatistics': 'false',
    'enablePersonalization': 'false',
    'pageSize': '500',
}

response = requests.get(
    'https://shop.billa.cz/api/product-discovery/categories/ovoce-a-zelenina-1165/products',
    params=params,
    cookies=cookies,
    headers=headers,
)
 
results = []
print(json.dumps(response.json(), ensure_ascii=False, indent=2))

results.append(response.json().get('results', []))

for i in results:
    print(i.get('name'))