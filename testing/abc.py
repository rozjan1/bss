import requests

cookies = {
    'customer-ecom-state': 'NOT_DEFINED',
    'groceryCookieLang': 'cs',
    'deviceSessionId': 'f121eb9d-8bfe-41f0-80c9-f0a8cbd416a0',
    'dtCookie': 'v_4_srv_7_sn_8168B5D7C821749586316C897CD7B115_perc_100000_ol_0_mul_1_app-3Ac32cb5e5575cf68e_1',
    'VersionedCookieConsent': 'v:2,essential:1,analytics:0,social:0,perso_cont_ads:0,ads_external:0',
    'rxVisitor': '1761818680285M9BKBT8F0QPBT0TD6T820JK3I30JAK9C',
    'liquidFeeThreshold': '0',
    'dtSa': 'true%7CKD%7C-1%7CPage%3A%2026343532%7C-%7C1761842859507%7C242767515_824%7Chttps%3A%2F%2Fwww.albert.cz%2Fshop%2FMaso-a-ryby%2FVeprove%2FKrkovice-plec-panenka%2FVeprova-plec-bez-kosti-na-peceni%2Fp%2F26343532%7C%7C%7C%7C',
    '_abck': 'D1FFD147D3F06FC3D89A22F7CA4343B0~-1~YAAQBm7UF8463y+aAQAAYjZJNw5wOW9EXi7fjLpnoMBkGWVRorJa7up0LLELYTYRBaDFraDMkdtK23eQf344anY1+9RiclYubuHRSNLH3OXvLPhSnxha/4U7c9+r6eeJyUc5gT+P6U+mTHcOF1TmBxB1coxP2K7kWrY9unmYLvMKI0SY5BFiF1JuFjU8fhirJKy7o5JEYRkSFypboX7EdF7PSlc/7EfbLJ7QBPyYJrfNiLSrbuUdwJCehxm7DrOUv9ESV9WcSyeRVzCEUvQe5xfBwevdJ12LBeXD92usXet9tAnD7CbXxIzXuM0RJdfB2epvuWmmQdYoFuHlDruQ2h5eZEcEbDeAgwYg9n6Da5bWNw73JnaI9HA/dKk9LTFANf6+ZJkfYBBzthhFsaTiMXKKxzgnCDcfcNSujjWCdIZNmRIWTDihuk2419QkManp585rgET1G9wDgY6pVsF3Lys3TQvU8E1oT2X3X78J1QhKtkN3m6jDbOFx5LrOjw==~-1~-1~-1~-1~-1',
    'ak_bmsc': '1ED8AF83107795E711348686918E6A91~000000000000000000000000000000~YAAQBm7UF8863y+aAQAAYjZJNx1jvi6yD1fpnvw5DuRsTCPw83rnvmhM3lptgEgMKNJGe9VhuhqWYXviD2tfV0rXtC6aBoYxP4DZ03fvAtIib1GSg+9Algipq/wmJZCFIdClKFeNsDeyl1KhbuzF9Qt/Kt5T/zSXfFrXzqfVyAFi7Pxrz3XPQ+XnNvOdBuBhVFZygrw6LYY1KSZKoAsPVePDxUl4p23cyCjuKUb40OhUpSQkNxNBMW79fv41MFNWsga9xp4Iwmc93t4ozqu4hHPTRQWLdG+9LZkXxZv19Q7Yx2Ua8i3tFlYDC9KngQw+0R9d7V/fNFOlNOrlSCt7amassF1psYCV+SVeaPu4OqF3J6jxBEeOlTsVtCSgfVMO',
    'bm_sz': '1B065D41969695FB5247B2227F445DDB~YAAQBm7UF9E63y+aAQAAYjZJNx3k2tUrMEeuLhtjpqtzBSqODCGxIMPuFooAFmd4CkNeRaQRE04j6ZMaQAFIYt0z1E/GRM9AN+KvLR1dzu0UDogVw+bE8qhINnWfVc+Yy+hA+hxZfxej1yldc54g9fH8VrejcqV7vzscDKj4ajncm5014O8rvel9LJo/7/nOo6jgBn/4laZDu3S1vt8FgHUifW86xAYVZ2qG+7t0ZvLvxmwiUhg/o5KTyPQAhiL1Lmgx+ozSX9uLY4dUxXXACa+iwotbURN97KFyiyYL6BWmd9QCs/0F1lPtgj+f6FZjBJXvXcoWfk36MjYdWjRFHHZ8f88XvFHjHl9ZlPgB2IR9yjlzwg==~3290424~4405298',
    'AWSALB': '+bAUhEBTfMoS/PUoD8NpyI7Nk4oWjJMw1NVzVsteJGQd6rUCXuZzxPYsyT+nO06P8j4GWYZWbxdgUtJojTGjyy5asg6ajqlfScRnLvEuKe6Q7wKvttJ9CY7Ycmm+',
    'AWSALBCORS': '+bAUhEBTfMoS/PUoD8NpyI7Nk4oWjJMw1NVzVsteJGQd6rUCXuZzxPYsyT+nO06P8j4GWYZWbxdgUtJojTGjyy5asg6ajqlfScRnLvEuKe6Q7wKvttJ9CY7Ycmm+',
    'dtPC': '7$236107795_445h-vRDIHAMLVMWHNREBJBPVMLFPRDMVQLRII-0e0',
    'rxvt': '1761866512885|1761864712885',
    'bm_sv': 'F17E3C9590548A56E9B97C8776A5DC04~YAAQRG7UF10uKSeaAQAA7YNnNx0AF9uSZNXqFQZPnV8peS2b1ed7vURL2c2PX9gkCXX364RFtXfcNH776Lm71FMJeBKE3qhYgAq7pVuHirpzjS1C7DwQeXl7vFztvTVjGusvow3CzqQvjrqjXlCp5TttpvMhhu5fvx8ZD/LoVMRJTThczVHyCnZlT+W49YFYvmiKr7xOxFjb7axrx3obnMA1oaWv4c2VGTuXopzdjLdbDsfX7enTVoj4rVFko1lI~1',
}

headers = {
    'accept': '*/*',
    'accept-language': 'cs-CZ,cs;q=0.9',
    'apollographql-client-name': 'cz-alb-web-stores',
    'apollographql-client-version': '9f7f73067ae74ca1179954e9a94f3a23f1822b6b',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.albert.cz/c/zeL001?intcmp=web_all_megamenu_trvanlive_still_hp_cz',
    'sec-ch-ua': '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'x-apollo-operation-id': 'e2e886640745ecc178a7063af2924a312585e81bbf6a7f7c70a38e8389bd9e31',
    'x-apollo-operation-name': 'GetCategoryProductSearch',
    'x-default-gql-refresh-token-disabled': 'true',
    # 'cookie': 'customer-ecom-state=NOT_DEFINED; groceryCookieLang=cs; deviceSessionId=f121eb9d-8bfe-41f0-80c9-f0a8cbd416a0; dtCookie=v_4_srv_7_sn_8168B5D7C821749586316C897CD7B115_perc_100000_ol_0_mul_1_app-3Ac32cb5e5575cf68e_1; VersionedCookieConsent=v:2,essential:1,analytics:0,social:0,perso_cont_ads:0,ads_external:0; rxVisitor=1761818680285M9BKBT8F0QPBT0TD6T820JK3I30JAK9C; liquidFeeThreshold=0; dtSa=true%7CKD%7C-1%7CPage%3A%2026343532%7C-%7C1761842859507%7C242767515_824%7Chttps%3A%2F%2Fwww.albert.cz%2Fshop%2FMaso-a-ryby%2FVeprove%2FKrkovice-plec-panenka%2FVeprova-plec-bez-kosti-na-peceni%2Fp%2F26343532%7C%7C%7C%7C; _abck=D1FFD147D3F06FC3D89A22F7CA4343B0~-1~YAAQBm7UF8463y+aAQAAYjZJNw5wOW9EXi7fjLpnoMBkGWVRorJa7up0LLELYTYRBaDFraDMkdtK23eQf344anY1+9RiclYubuHRSNLH3OXvLPhSnxha/4U7c9+r6eeJyUc5gT+P6U+mTHcOF1TmBxB1coxP2K7kWrY9unmYLvMKI0SY5BFiF1JuFjU8fhirJKy7o5JEYRkSFypboX7EdF7PSlc/7EfbLJ7QBPyYJrfNiLSrbuUdwJCehxm7DrOUv9ESV9WcSyeRVzCEUvQe5xfBwevdJ12LBeXD92usXet9tAnD7CbXxIzXuM0RJdfB2epvuWmmQdYoFuHlDruQ2h5eZEcEbDeAgwYg9n6Da5bWNw73JnaI9HA/dKk9LTFANf6+ZJkfYBBzthhFsaTiMXKKxzgnCDcfcNSujjWCdIZNmRIWTDihuk2419QkManp585rgET1G9wDgY6pVsF3Lys3TQvU8E1oT2X3X78J1QhKtkN3m6jDbOFx5LrOjw==~-1~-1~-1~-1~-1; ak_bmsc=1ED8AF83107795E711348686918E6A91~000000000000000000000000000000~YAAQBm7UF8863y+aAQAAYjZJNx1jvi6yD1fpnvw5DuRsTCPw83rnvmhM3lptgEgMKNJGe9VhuhqWYXviD2tfV0rXtC6aBoYxP4DZ03fvAtIib1GSg+9Algipq/wmJZCFIdClKFeNsDeyl1KhbuzF9Qt/Kt5T/zSXfFrXzqfVyAFi7Pxrz3XPQ+XnNvOdBuBhVFZygrw6LYY1KSZKoAsPVePDxUl4p23cyCjuKUb40OhUpSQkNxNBMW79fv41MFNWsga9xp4Iwmc93t4ozqu4hHPTRQWLdG+9LZkXxZv19Q7Yx2Ua8i3tFlYDC9KngQw+0R9d7V/fNFOlNOrlSCt7amassF1psYCV+SVeaPu4OqF3J6jxBEeOlTsVtCSgfVMO; bm_sz=1B065D41969695FB5247B2227F445DDB~YAAQBm7UF9E63y+aAQAAYjZJNx3k2tUrMEeuLhtjpqtzBSqODCGxIMPuFooAFmd4CkNeRaQRE04j6ZMaQAFIYt0z1E/GRM9AN+KvLR1dzu0UDogVw+bE8qhINnWfVc+Yy+hA+hxZfxej1yldc54g9fH8VrejcqV7vzscDKj4ajncm5014O8rvel9LJo/7/nOo6jgBn/4laZDu3S1vt8FgHUifW86xAYVZ2qG+7t0ZvLvxmwiUhg/o5KTyPQAhiL1Lmgx+ozSX9uLY4dUxXXACa+iwotbURN97KFyiyYL6BWmd9QCs/0F1lPtgj+f6FZjBJXvXcoWfk36MjYdWjRFHHZ8f88XvFHjHl9ZlPgB2IR9yjlzwg==~3290424~4405298; AWSALB=+bAUhEBTfMoS/PUoD8NpyI7Nk4oWjJMw1NVzVsteJGQd6rUCXuZzxPYsyT+nO06P8j4GWYZWbxdgUtJojTGjyy5asg6ajqlfScRnLvEuKe6Q7wKvttJ9CY7Ycmm+; AWSALBCORS=+bAUhEBTfMoS/PUoD8NpyI7Nk4oWjJMw1NVzVsteJGQd6rUCXuZzxPYsyT+nO06P8j4GWYZWbxdgUtJojTGjyy5asg6ajqlfScRnLvEuKe6Q7wKvttJ9CY7Ycmm+; dtPC=7$236107795_445h-vRDIHAMLVMWHNREBJBPVMLFPRDMVQLRII-0e0; rxvt=1761866512885|1761864712885; bm_sv=F17E3C9590548A56E9B97C8776A5DC04~YAAQRG7UF10uKSeaAQAA7YNnNx0AF9uSZNXqFQZPnV8peS2b1ed7vURL2c2PX9gkCXX364RFtXfcNH776Lm71FMJeBKE3qhYgAq7pVuHirpzjS1C7DwQeXl7vFztvTVjGusvow3CzqQvjrqjXlCp5TttpvMhhu5fvx8ZD/LoVMRJTThczVHyCnZlT+W49YFYvmiKr7xOxFjb7axrx3obnMA1oaWv4c2VGTuXopzdjLdbDsfX7enTVoj4rVFko1lI~1',
}

params = {
    'operationName': 'GetCategoryProductSearch',
    'variables': '{"lang":"cs","searchQuery":"","category":"zeM001","pageNumber":PAGE_NUMBER,"pageSize":50,"filterFlag":true,"fields":"PRODUCT_TILE","plainChildCategories":true}',
    'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"afce78bc1a2f0fe85f8592403dd44fae5dd8dce455b6eeeb1fd6857cc61b00a2"}}',
}

def is_empty_product_response(response: dict) -> bool:
    """
    Checks if the JSON response is the one without any products.
    """
    try:
        products_list = response['data']['categoryProductSearch']['products']

        if not products_list:
            return True
        else:
            return False

    except KeyError:
        print("Warning: JSON structure is missing expected keys.")
        return False # Or True, depending on how you want to handle errors


total_count = 0
for i in range(0, 500): # arbitrarily large number, since we stop when no products are returned
    # copy the params so we don't mutate the original
    this_params = params.copy()
    this_params['variables'] = this_params['variables'].replace('PAGE_NUMBER', str(i))

    response = requests.get('https://www.albert.cz/api/v1/', params=this_params, cookies=cookies, headers=headers)

    try:
        parsed = response.json()
    except Exception as e:
        print(f"Failed to parse JSON on page {i}: {e}")
        break

    # Use helper to detect empty product response and stop pagination
    if is_empty_product_response(parsed):
        print(f"Page {i} returned no products — stopping pagination.")
        break

    products = parsed.get('data', {}).get('categoryProductSearch', {}).get('products', [])
    total_count += int(len(products))
    print(parsed['data']['categoryProductSearch']['products'][0].get('name'))

print(f"Total products found: {total_count}")