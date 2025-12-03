import re
import requests
from time import sleep
import json


# list of facets/product types
facets = {
  "b;T3ZvY2UlMjBhJTIwemVsZW5pbmE=": "Ovoce a zelenina",
  "b;TWwlQzMlQTklQzQlOERuJUMzJUE5LCUyMHZlamNlJTIwYSUyMG1hcmdhciVDMyVBRG55": "Mléko, vejce a margaríny",
  "b;UGVrJUMzJUExcm5hJTdDVm9sbiVDMyVBOSUyMHBlJUM0JThEaXZv=": "Pekárna",
  "b;TWFzbyUyMGElMjBsYWglQzUlQUZka3k": "Maso a lahudky",
  "b;TXJhJUM1JUJFZW4lQzMlQTk": "Mražené",
  "b;VHJ2YW5saXYlQzMlQTk": "Trvanlivé",
  "b;TiVDMyVBMXBvamU=": "Nápoje",
  "b;U3BlY2klQzMlQTFsbiVDMyVBRCUyMHYlQzMlQkQlQzUlQkVpdmE": "Speciální výživa"
}


def get_tesco_data(facet, session=None, timeout=30):
    """
    Sends a POST request to the Tesco API to fetch category products.
    """
    url = 'https://xapi.tesco.com/'

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'x-apikey': 'TvOSZJHlEk0pjniDGQFAc9Q59WGAR4dA',
        'region': 'CZ',
        'language': 'cs-CZ',
        'Origin': 'https://nakup.itesco.cz',
        'Referer': 'https://nakup.itesco.cz/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15',
    }

    # This is the GraphQL query and variables
    page = 0
    count = 1000

    payload = [
        {
            "operationName": "GetCategoryProducts",
            "variables": {
                "page": page,
                "includeRestrictions": True,
                "includeVariations": True,
                "showDepositReturnCharge": True,
                "includeRangeFilter": False,
                "count": count,
                "facet": facet,
                "configs": [
                    {
                        "featureKey": "dynamic_filter",
                        "params": [{"name": "enable", "value": "true"}]
                    }
                ],
                "filterCriteria": [{"name": "0", "values": ["groceries"]}],
                "appliedFacetArgs": [],
                "sortBy": "relevance"
            },
            "extensions": {"mfeName": "mfe-plp"},
            "query": """query GetCategoryProducts($facet: ID, $page: Int = 1, $count: Int, $sortBy: String, $offset: Int, $favourites: Boolean, $configs: [ConfigArgType], $filterCriteria: [filterCriteria], $includeRestrictions: Boolean = true, $includeVariations: Boolean = true, $mediaExperiments: BrowseSearchConfig, $showDepositReturnCharge: Boolean = false, $appliedFacetArgs: [AppliedFacetArgs], $includeRangeFilter: Boolean = false) {
              category(
                page: $page
                count: $count
                configs: $configs
                sortBy: $sortBy
                offset: $offset
                facet: $facet
                favourites: $favourites
                config: $mediaExperiments
                filterCriteria: $filterCriteria
                appliedFacetArgs: $appliedFacetArgs
              ) {
                pageInformation: info {
                  ...PageInformation
                  __typename
                }
                results {
                  node {
                    ... on MPProduct {
                      ...ProductItem
                      __typename
                    }
                    ... on FNFProduct {
                      ...ProductItem
                      __typename
                    }
                    ... on ProductType {
                      ...ProductItem
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                facetLists: facetGroups {
                  ...FacetLists
                  __typename
                }
                facets {
                  ...facet
                  __typename
                }
                options {
                  sortBy
                  __typename
                }
                __typename
              }
            }
            
            fragment ProductItem on ProductInterface {
              typename: __typename
              ... on ProductType {
                context {
                  type
                  ... on ProductContextOfferType {
                    linkTo
                    offerType
                    __typename
                  }
                  __typename
                }
                __typename
              }
              sellers(type: TOP, limit: 1, offset: 0) {
                ...Sellers
                __typename
              }
              ... on MPProduct {
                context {
                  type
                  ... on ProductContextOfferType {
                    linkTo
                    offerType
                    __typename
                  }
                  __typename
                }
                seller {
                  id
                  name
                  __typename
                }
                variations {
                  ...Variation @include(if: $includeVariations)
                  __typename
                }
                __typename
              }
              ... on FNFProduct {
                context {
                  type
                  ... on ProductContextOfferType {
                    linkTo
                    offerType
                    __typename
                  }
                  __typename
                }
                variations {
                  priceRange {
                    minPrice
                    maxPrice
                    __typename
                  }
                  ...Variation @include(if: $includeVariations)
                  __typename
                }
                media {
                  defaultImage {
                    url
                    aspectRatio
                    __typename
                  }
                  images {
                    url
                    aspectRatio
                    __typename
                  }
                  __typename
                }
                __typename
              }
              id
              tpnb
              tpnc
              gtin
              adId
              baseProductId
              title
              brandName
              shortDescription
              defaultImageUrl
              superDepartmentId
              media {
                defaultImage {
                  url
                  aspectRatio
                  __typename
                }
                __typename
              }
              images {
                display {
                  default {
                    url
                    __typename
                  }
                  __typename
                }
                __typename
              }
              quantityInBasket
              superDepartmentName
              departmentId
              departmentName
              aisleId
              aisleName
              displayType
              productType
              charges @include(if: $showDepositReturnCharge) {
                ... on ProductDepositReturnCharge {
                  __typename
                  amount
                }
                __typename
              }
              averageWeight
              bulkBuyLimit
              maxQuantityAllowed: bulkBuyLimit
              groupBulkBuyLimit
              bulkBuyLimitMessage
              bulkBuyLimitGroupId
              timeRestrictedDelivery
              restrictedDelivery
              isInFavourites
              isNew
              isRestrictedOrderAmendment
              maxWeight
              minWeight
              increment
              details {
                components {
                  ...Competitors
                  ...AdditionalInfo
                  __typename
                }
                __typename
              }
              catchWeightList {
                price
                weight
                default
                __typename
              }
              restrictions @include(if: $includeRestrictions) {
                type
                isViolated
                message
                __typename
              }
              reviews {
                stats {
                  noOfReviews
                  overallRating
                  overallRatingRange
                  __typename
                }
                __typename
              }
              modelMetadata {
                name
                version
                __typename
              }
            }
            
            fragment Competitors on CompetitorsInfo {
              competitors {
                id
                priceMatch {
                  isMatching
                  __typename
                }
                __typename
              }
              __typename
            }
            
            fragment AdditionalInfo on AdditionalInfo {
              isLowEverydayPricing
              __typename
            }
            
            fragment Variation on VariationsType {
              products {
                id
                baseProductId
                variationAttributes {
                  attributeGroup
                  attributeGroupData {
                    name
                    value
                    attributes {
                      name
                      value
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                __typename
              }
              __typename
            }
            
            fragment Sellers on ProductSellers {
              __typename
              results {
                id
                __typename
                isForSale
                status
                seller {
                  id
                  name
                  logo {
                    url
                    __typename
                  }
                  __typename
                }
                price {
                  price: actual
                  unitPrice
                  unitOfMeasure
                  actual
                  __typename
                }
                promotions {
                  id
                  promotionType
                  startDate
                  endDate
                  description
                  unitSellingInfo
                  price {
                    beforeDiscount
                    afterDiscount
                    __typename
                  }
                  attributes
                  __typename
                }
                fulfilment(deliveryOptions: BEST) {
                  __typename
                  ... on ProductDeliveryType {
                    end
                    charges {
                      value
                      __typename
                    }
                    __typename
                  }
                }
              }
            }
            
            fragment FacetLists on ProductListFacetsType {
              __typename
              category
              categoryId
              facets {
                facetId: id
                facetName: name
                binCount: count
                isSelected: selected
                __typename
              }
            }
            
            fragment PageInformation on ListInfoType {
              totalCount: total
              pageNo: page
              pageId
              count
              pageSize
              matchType
              offset
              query {
                searchTerm
                actualTerm
                queryPhase
                __typename
              }
              __typename
            }
            
            fragment facet on FacetInterface {
              __typename
              id
              name
              type
              ...FacetListTypeFields
              ...FacetMultiLevelTypeFields
              ...FacetRangeTypeFields @include(if: $includeRangeFilter)
              ...FacetBooleanTypeFields
            }
            
            fragment FacetListTypeFields on FacetListType {
              id
              name
              listValues: values {
                name
                value
                isSelected
                count
                __typename
              }
              multiplicity
              metadata {
                description
                footerText
                linkText
                linkUrl
                __typename
              }
              __typename
            }
            
            fragment FacetMultiLevelTypeFields on FacetMultiLevelType {
              id
              name
              multiLevelValues: values {
                children {
                  count
                  name
                  value
                  isSelected
                  __typename
                }
                appliedValues {
                  isSelected
                  name
                  value
                  __typename
                }
                __typename
              }
              multiplicity
              metadata {
                description
                footerText
                linkText
                linkUrl
                __typename
              }
              __typename
            }
            
            fragment FacetRangeTypeFields on FacetRangeType {
              rangeValues: values {
                buckets {
                  name
                  value
                  count
                  isSelected
                  __typename
                }
                customInput {
                  min
                  max
                  appliedMin
                  appliedMax
                  step
                  unit
                  delimiter
                  unitPosition
                  __typename
                }
                __typename
              }
              __typename
            }
            
            fragment FacetBooleanTypeFields on FacetBooleanType {
              booleanValues: values {
                count
                isSelected
                value
                name
                __typename
              }
              __typename
            }
            """
        }
    ]

    try:
        # Use provided requests.Session (configured with Tor SOCKS proxy) if available
        if session is not None:
            response = session.post(url, headers=headers, json=payload, timeout=timeout)
        else:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        print("Request successful!")
        print("Status Code:", response.status_code)
        
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        exit()


def clean_tesco_data(data, category_name):
    results_list = []
    try:
        # Path: [0] -> "data" -> "category" -> "results"
        results_list = data[0]["data"]["category"]["results"]
    except (IndexError, KeyError) as e:
        print(f"Could not find the 'results' list. Check JSON structure. Error: {e}")

    if data[0]["data"]["category"]["pageInformation"]["totalCount"] > 1000:
        print("\033[93m" + f"Warning: Total count exceeds 1000 for category {category_name}. Data may be incomplete." + "\033[0m")

    all_titles = []

    # Iterate through each item in the results list
    for item in results_list:
        try:
            # Path for each item: "node" -> "title"
            #print("New item:" + item["node"]["title"])

            title = item["node"]["title"]
            image_url = item["node"]["defaultImageUrl"]
            
            regular_price = item["node"]["sellers"]["results"][0]["price"]["price"]
            price_per_unit_default = item["node"]["sellers"]["results"][0]["price"]["unitPrice"]

            sale_price = regular_price
            sale_ppu = price_per_unit_default
            
            product_url = f"https://nakup.itesco.cz/groceries/cs-CZ/products/{item['node']['id']}"

            sale_requirement = None

            promotions = item["node"]["sellers"]["results"][0]["promotions"]

            if promotions != []:
                description = promotions[0]["description"]
                # "19,90 Kč Více než o polovinu nižší cena s Clubcard"
                # "36%, předtím 219.90 Kč"
                # "33,90 Kč s Clubcard"
                promo_attributes = promotions[0]["attributes"]
                if promo_attributes != []:
                  sale_requirement = promo_attributes # can be empty list or a list with one element
                  if promo_attributes[0] == 'CLUBCARD_PRICING':
                    sale_requirement = 'tesco_clubcard'
                  
                  if "s Clubcard" in description:
                    print("Promotion description: " + description)
                    if not re.search(r'\d{1,3}%.*předtím', description):
                      sale_price = extract_price(description)  # regular_price * (1 - float(description.split('%')[0].replace(',', '.')) / 100)
                    sale_ppu = float(promotions[0]['unitSellingInfo'].split(" ")[0].replace(",", "."))

            unit_code = item["node"]["sellers"]["results"][0]["price"]["unitOfMeasure"]

            all_titles.append({
                'source': 'tesco',
                'product_category': category_name,
                'item_name': title,
                'image_url': image_url,
                'original_price': regular_price, #  "286,40 Kč"
                'original_ppu': price_per_unit_default,  # eg "89.9", we need to add the unit from the unit_code
                'sale_price': sale_price, # "143,84 Kč"
                'sale_ppu': sale_ppu,  # eg "89.9", we need to add the unit from the unit_code
                'unit_code': unit_code, # eg kg, g, l etc.
                'product_url': product_url,
                'sale_requirement': sale_requirement  # Indicate that sale price requires Tesco Clubcard
            })
        except KeyError as e:
            # Handle cases where an item might be missing the expected structure
            print(f"Error processing item: {e}")
            print(item)
            print("Warning: Found an item without a 'title' in its 'node'. Skipping.")

    return all_titles


def extract_price(text):
    match = re.search(r'(\d{1,3}(?:[.,]\d{1,2})?)\s*Kč', text)
    if match:
        # replace comma with dot for consistency
        return float(match.group(1).replace(',', '.'))
    return None



def extract_nutrition(data):
    try:
        nutrition_array = data[0]['data']['product']['details']['nutritionInfo']
    except (IndexError, KeyError) as e:
        print(f"Error: Could not find 'nutritionInfo'. Structure may have changed. Error: {e}")
        return {}

    # Initialize a dictionary to store the extracted information
    nutrition_details = {}

    # The first item usually contains the serving size ('na 100 ml'), which is good context.
    serving_size_item = nutrition_array[0]
    nutrition_details['Serving Size'] = serving_size_item.get('perComp', 'N/A')
    
    # Iterate through the rest of the list, skipping items with no actual nutrient value
    for item in nutrition_array[1:]:
        name = item.get('name')
        value = item.get('perComp')
        
        # We only want entries that have a name and an actual value (not just '-')
        if name and value and value != '-':
            nutrition_details[name] = value

    return nutrition_details


if __name__ == "__main__":
    all_titles = []

    for code, category_name in facets.items():
        print(f"Fetching data for facet: {code} ({category_name})")
        tesco_data = get_tesco_data(code)

        all_titles.extend(clean_tesco_data(tesco_data, category_name))
        sleep(1)  # Be polite and avoid hitting the server too quickly

    with open('tesco_products.json', 'w', encoding='utf-8') as f:
        json.dump(all_titles, f, ensure_ascii=False, indent=4)

    #for title in all_titles:
        #print(title)