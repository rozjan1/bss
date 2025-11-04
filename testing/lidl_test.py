import requests

cookies = {
    'CookieConsent': '{necessary:true%2Cpreferences:false%2Cstatistics:false%2Cmarketing:false}',
    'LidlID': '30460f41-f210-4023-a6b5-48000c42f830',
    'i18n_redirected': 'cs_CZ',
}

headers = {
    'accept': 'application/mindshift.search+json;version=2',
    'accept-language': 'cs-CZ,cs;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.lidl.cz/c/potraviny-a-napoje/s10068374',
    'sec-ch-ua': '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'CookieConsent={necessary:true%2Cpreferences:false%2Cstatistics:false%2Cmarketing:false}; LidlID=30460f41-f210-4023-a6b5-48000c42f830; i18n_redirected=cs_CZ',
}

offset = 0
fetchsize = 1000

params = {
    'offset': str(offset),
    'fetchsize': str(fetchsize),
    'locale': 'cs_CZ',
    'assortment': 'CZ',
    'version': '2.1.0',
    'category.id': '10068374',
}

response = requests.get('https://www.lidl.cz/q/api/search', params=params, cookies=cookies, headers=headers)
print(response.json())