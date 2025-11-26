import requests
import json
from urllib.parse import urlparse, parse_qs


# Lightweight fetcher for Albert.cz product details
class AlbertProductInfoFetcher:
    """Fetch and normalize product info from an Albert.cz product URL or product code.

    Usage:
        fetcher = AlbertProductInfoFetcher()
        info = fetcher.fetch('https://www.albert.cz/shop/.../p/26863092')
        # info -> {'nutrients': {...}, 'allergies': {...}}

    The fetch method accepts either a full product URL (product code will be extracted)
    or a product code string directly.
    """

    def __init__(self):
        # default cookies/headers carried over from the original script; they
        # help emulate a browser request but are not guaranteed to be stable.
        self.cookies = {
            'dtCookie': 'v_4_srv_5_sn_279E84FAA92DD96FB0E36105C59A5A6B_perc_100000_ol_0_mul_1_app-3Ac32cb5e5575cf68e_0',
            '_abck': 'F18A332EB85F28227920426960DEE61C~-1~YAAQF5JkX22tzaWaAQAA6h8+vw4qAJlk5wg1JsLD5LMG5hkaYZY3WZNKS1v+ioMDqFrPzK5zqzqUimpHeA6ImKObsyBZGr8T0lcBEWa+O0BH7hxbF5iKCUil8xIfc6zhV3p3GckYrsEdLdgYIso139v31F5aKkUZczgydxDRdMqGkwXFmr5A+Hy1aBeMmbvPMARG3xYAOoUWm0GHow5dOZfX3KGCIEFba1cMa7dJlks3Z8ZNhMPBmDS0wcc8gNinRks9iu21JkWhuKV7Jweo/V6vOfYHnpS3UYWavOhbV2gPj6fU9y4joaJIh9NK8fOHVfFRzvesU38BBIzZPuKf3U34BXSLjvJwpPYycsQoR1ifjFGBsBb0olKekwFzwoN8yq+DBWn2aLXbMbxAzheS497OWRfMme+kxTHTX1NOEaV0Uk5Ih5xAeiFOfSdIgo6zcGxMsAZWPsVfr/sfXaj2zcGxXjjiR07OSnJVRif7OKg=~-1~-1~-1~-1~-1',
            'deviceSessionId': 'ce6f3250-ba84-4dbd-921b-b4b76b0a0648',
            'customer-ecom-state': 'NOT_DEFINED',
            'groceryCookieLang': 'cs',
            'liquidFeeThreshold': '0',
            'ak_bmsc': 'C05888960E0FBB5E24D2130CBD1A014B~000000000000000000000000000000~YAAQF5JkX7WtzaWaAQAAeCM+vx2MGcHrp1FCwSLN9YZN8+oG4BHYGhpWSR5EMHV6oMXIxTmn65sV+qJ3+qnCIv+p0yz3Rf3toaQ8knNKMOzCpzrG4azEM3hbrs5HbDoihj0VwynL542XF4SbpvmCgDf7MKHpvFr9a3BbVuP6OEWDoP8/PjS8O1a5cQE3rAHD4wQs5TO8a8sqoSn5ll3AWdo7GznhnHX7hpzY/UO1WyyY4ucA0uVdAp2EmaMtgRXZ84B9wsx+m9C9aYmhIvkUnGyK8Q9EnEwUFXl/5zTGhCMJHANvC3QnzxfwRLr/azCW0i0p5yoXo7Yed2mVion+9YQe8uP8YURm2R1AruW8txZIXIZYmLHmkZxw3t1OBPdswUssSkfstPoRgz/rufPjgA+Imc86PlTzfaFM+Vg6BVG/BhuHamBFS0sdzzW6wMQoQqK0lSM=',
            'VersionedCookieConsent': 'v%3A2%2Cessential%3A1%2Canalytics%3A0%2Csocial%3A0%2Cperso_cont_ads%3A0%2Cads_external%3A0',
            'AMCV_2A6E210654E74B040A4C98A7%40AdobeOrg': '179643557%7CMCMID%7C47732117756320159160629093944694941328%7CMCAID%7CNONE%7CvVersion%7C5.5.0',
            'bm_sz': '0A7AB60A2F0E1B4CF9813E8CEEB168F4~YAAQFpJkX1GuuaWaAQAAjE4/vx2qfLhnjUGa6A0j6OG+34Moht00+aGKN2+jtPswRnI6ZcYjo4M2ZwCckbRt7K8jGKKE+U9ZmMEaaw+wiF3oVJCXPTutufmYa3uozuBoaVT1Wk7xIgVN5koUHJgLK0VR+pgicMJORPXTiyWt9oWUY5W7ibkEVVfvsMOqdStCDKQZ63Uk3VFchTjR6YQ0YITZUx6qxQStaqvZ+B1/Jka4dkpjeSBWhuZ2HnejaHf/Kbkak44Y7tvL2hDcot0N0fxeDZE3hIhSMj81rT1hV1HY88C2LuDQcTzq5OKlmd7PhrbshQA1ubUADwoNAiBisKbB5ohxrbMMqkv+/+Q7F9PlY4t2ZvAzOJKCbUBoXRRwSf5Ai1O+BIXKk21DWqQfYNLRjw4zDQ==~4535106~4407604',
            'AWSALB': 'Key1K2ZzabP9ahdWBmFZ1x+xiLbUAT19IL1B6Nfsbxfu080lGt79NSrne1XL3/0046HLo3GGmvM4e2PLhzAieG3Yw0+AqDLBLs+z50/q0k6zUWl98Kg6oFFZJHSD',
            'AWSALBCORS': 'Key1K2ZzabP9ahdWBmFZ1x+xiLbUAT19IL1B6Nfsbxfu080lGt79NSrne1XL3/0046HLo3GGmvM4e2PLhzAieG3Yw0+AqDLBLs+z50/q0k6zUWl98Kg6oFFZJHSD',
            'bm_sv': 'B9FFDFB85A90F0D3A269073A58CED7BE~YAAQF5JkX10dzqWaAQAAPeFCvx2pGXLPaSsPQYnSslvNKmklrFHh6NSjjgTw5X+8dtFIaet4N87PUrpDAmma4WMtrn4MQV58a9d+ioYJloLhdLsGI3Pb/CScvZSn0I8iij9LNN45lGqaEUqHEOcqbD+Gw2hHrOqlF7+2X2Zqk3POVtjjr6gt+cTquNpAgRjdU1Q+VkxP+68dQZLF3FWbd4kLPoNDwjMrgjOdUAL2u0P30tMD4Eyw9bOoRmOa4w+Y~1',
        }

        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'apollographql-client-name': 'cz-alb-web-stores',
            'apollographql-client-version': '88bb9dfcd6dbf6d12a9df4fb8cf74bc3dd94ef86',
            'content-type': 'application/json',
            'priority': 'u=1, i',
            'referer': 'https://www.albert.cz/shop/Uzeniny-a-lahudky/Sunky-a-slaniny/Veprove-a-hovezi/Ceska-chut-Sunka-nejvyssi-jakosti/p/26863092',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'x-apollo-operation-id': '5763c6885714a83eadfd57082f25426c4a6cdc73a151be53248a90f360231b1a',
            'x-apollo-operation-name': 'ProductDetails',
            'x-default-gql-refresh-token-disabled': 'true',
        }

        # the persisted query hash used by the site's GraphQL endpoint
        self._extensions = {
            'extensions': json.dumps({
                'persistedQuery': {
                    'version': 1,
                    'sha256Hash': '56c710d5a8fbfd875435defa32acce0497637a2987eeb9be0d4a117ea33bdb2a'
                }
            })
        }

    def _extract_product_code(self, url_or_code: str) -> str:
        """Extract product code from a product URL or return the string if it's already a code."""
        # crude check: if contains '/' assume URL
        if '/' in url_or_code:
            parsed = urlparse(url_or_code)
            # check query params for 'p' or 'productCode'
            qs = parse_qs(parsed.query)
            if 'p' in qs:
                return qs['p'][0]
            # fallback: last path segment that looks numeric
            parts = [p for p in parsed.path.split('/') if p]
            for part in reversed(parts):
                if part.isdigit():
                    return part
            # final fallback: join digits from path
            digits = ''.join(ch for ch in parsed.path if ch.isdigit())
            if digits:
                return digits
            raise ValueError('Could not extract product code from URL')
        return url_or_code

    def fetch(self, url_or_code: str) -> dict:
        """Fetch product info for the given product URL or product code.

        Returns a dict: {'nutrients': {...}, 'allergies': {...}}
        Raises requests.HTTPError for HTTP errors and ValueError for parsing issues.
        """
        product_code = self._extract_product_code(url_or_code)

        params = {
            'operationName': 'ProductDetails',
            'variables': json.dumps({'productCode': product_code, 'lang': 'cs'}),
        }
        # merge the extensions param
        params.update(self._extensions)

        response = requests.get('https://www.albert.cz/api/v1/', params=params, cookies=self.cookies, headers=self.headers)
        response.raise_for_status()
        product_info = response.json()

        wsNutriFactData = (
            product_info.get('data', {})
                .get('productDetails', {})
                .get('wsNutriFactData')
        )

        if not wsNutriFactData:
            # return empty structure if nutrition data isn't present
            return {'nutrients': {}, 'allergies': {}}

        # --- Clean nutrients into a flat dict ---
        nutrients = {}
        try:
            nutrients = {
                n['id']: (n.get('valueList') or [{}])[0].get('value')
                for n in wsNutriFactData.get('nutrients', [])[0].get('nutrients', [])
            }
        except Exception:
            # fall back to empty
            nutrients = {}

        # --- Format allergy info cleanly ---
        allergies = {}
        try:
            allergies = {
                a['title']: a.get('values') or None
                for a in wsNutriFactData.get('allegery', [])
            }
        except Exception:
            allergies = {}

        normalized = {
            'nutrients': nutrients,
            'allergies': allergies
        }

        return normalized


if __name__ == '__main__':
    # simple CLI demo: accept a URL or code from argv or use sample code
    import sys

    demo_code = '26863092'
    arg = sys.argv[1] if len(sys.argv) > 1 else demo_code
    fetcher = AlbertProductInfoFetcher()
    try:
        info = fetcher.fetch(arg)
        print(json.dumps(info, ensure_ascii=False, indent=2))
    except Exception as e:
        print('Error fetching product info:', e)
