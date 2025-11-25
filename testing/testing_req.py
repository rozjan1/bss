import requests
import json

# list of facets/product thingy types
# list of facets/product thingy types
facets = [
    "b;UGVrJUMzJUExcm5hJTdDVm9sbiVDMyVBOSUyMHBlJUM0JThEaXZv=", # Pekarna
    "b;T3ZvY2UlMjBhJTIwemVsZW5pbmE=", # Ovoce a zelenina
    "b;TWFzbyUyMGElMjBsYWglQzUlQUZka3k", # Maso a lahudky
]


def get_tesco_data():
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
    payload = [
        {
            "operationName": "GetCategoryProducts",
            "variables": {
                "page": 1,
                "includeRestrictions": True,
                "includeVariations": True,
                "showDepositReturnCharge": True,
                "includeRangeFilter": False,
                "count": 1000,
                "facet": "b;TWFzbyUyMGElMjBsYWglQzUlQUZka3k=",
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
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        print("Request successful!")
        print("Status Code:", response.status_code)
        
        # Pretty print the JSON response
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        exit()

def clean_tesco_data(data):
    results_list = []
    try:
        # Path: [0] -> "data" -> "category" -> "results"
        results_list = data[0]["data"]["category"]["results"]
    except (IndexError, KeyError) as e:
        print(f"Could not find the 'results' list. Check JSON structure. Error: {e}")

    all_titles = []

    # Iterate through each item in the results list
    for item in results_list:
        try:
            # Path for each item: "node" -> "title"
            title = item["node"]["title"]
            all_titles.append(title)
        except KeyError:
            # Handle cases where an item might be missing the expected structure
            print("Warning: Found an item without a 'title' in its 'node'. Skipping.")

    # Output the extracted titles
    for title in all_titles:
        print(title)

if __name__ == "__main__":
    tesco_data = get_tesco_data()
    clean_tesco_data(tesco_data)