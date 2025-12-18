from base_scraper import BaseScraper
from typing import List, Dict, Any, Tuple
from time import sleep
from loguru import logger
import re
import sys
from pathlib import Path

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Product


class TescoScraper(BaseScraper):
    def __init__(self):
        super().__init__("tesco")
        self.page_size = 1000  # Tesco returns up to 1000 items per call
        self.facets = {
            "b;T3ZvY2UlMjBhJTIwemVsZW5pbmE=": "Ovoce a zelenina",
            "b;TWwlQzMlQTklQzQlOERuJUMzJUE5LCUyMHZlamNlJTIwYSUyMG1hcmdhciVDMyVBRG55": "Mléko, vejce a margaríny",
            "b;UGVrJUMzJUExcm5hJTdDVm9sbiVDMyVBOSUyMHBlJUM0JThEaXZv=": "Pekárna",
            "b;TWFzbyUyMGElMjBsYWglQzUlQUZka3k=": "Maso a lahudky",
            "b;TXJhJUM1JUJFZW4lQzMlQTk=": "Mražené",
            "b;VHJ2YW5saXYlQzMlQTk=": "Trvanlivé",
            "b;TiVDMyVBMXBvamU=": "Nápoje",
            "b;U3BlY2klQzMlQTFsbiVDMyVBRCUyMHYlQzMlQkQlQzUlQkVpdmE=": "Speciální výživa"
        }   
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-apikey': 'TvOSZJHlEk0pjniDGQFAc9Q59WGAR4dA',
            'region': 'CZ',
            'language': 'cs-CZ',
            'Origin': 'https://nakup.itesco.cz',
            'Referer': 'https://nakup.itesco.cz/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15',
        })

    def fetch_category(self, category_code: str, page: int = 0) -> Dict[str, Any]:
        """Fetch products from Tesco GraphQL API for a given category."""
        payload = [{
            "operationName": "GetCategoryProducts",
            "variables": {
          "page": page,
                "includeRestrictions": True,
                "includeVariations": True,
                "showDepositReturnCharge": True,
                "includeRangeFilter": False,
          "count": self.page_size,
                "facet": category_code,
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
        }]
        
        try:
            response = self.session.post(
                'https://xapi.tesco.com/',
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request failed for category {category_code}: {e}")
            return {}

    def _extract_price(self, text: str) -> float:
        """Extract price from text with regex."""
        match = re.search(r'(\d{1,3}(?:[.,]\d{1,2})?)\s*Kč', text)
        if match:
            return float(match.group(1).replace(',', '.'))
        return None

    def parse_response(self, response_data: Dict[str, Any], category_name: str) -> Tuple[List[Product], bool]:
        """Transform Tesco JSON data into Product objects and signal if more pages exist."""
        products: List[Product] = []
        
        try:
            results_list = response_data[0]["data"]["category"]["results"]
            page_info = response_data[0]["data"]["category"]["pageInformation"]
            total_count = page_info.get("totalCount", 0)
            current_page = page_info.get("page", 0)
            count_per_page = page_info.get("count", len(results_list)) or self.page_size
        except (IndexError, KeyError) as e:
            logger.warning(f"Could not find 'results' list for category {category_name}: {e}")
            return products, False
        
        logger.info(f"Processing {len(results_list)} products from category {category_name}, page {current_page}")
        
        for item in results_list:
            try:
                node = item["node"]
                
                # Basic info
                title = node["title"]
                image_url = node["defaultImageUrl"]
                
                # Pricing
                seller_info = node["sellers"]["results"][0]
                regular_price_raw = seller_info["price"].get("price")
                price_per_unit_default = seller_info["price"].get("unitPrice")
                
                # Skip items without a numeric price
                if regular_price_raw is None:
                  continue
                
                try:
                  regular_price = float(regular_price_raw)
                except (TypeError, ValueError):
                  continue
                
                sale_price = regular_price
                sale_ppu = float(price_per_unit_default) if price_per_unit_default is not None else None
                sale_requirement = None
                
                # Check for promotions
                promotions = seller_info["promotions"]
                
                if promotions:
                    promotion = promotions[0]
                    description = promotion["description"]
                    promo_attributes = promotion.get("attributes", [])
                    
                    if promo_attributes:
                        if promo_attributes[0] == 'CLUBCARD_PRICING':
                            sale_requirement = 'tesco_clubcard'
                    
                    if "s Clubcard" in description:
                        if not re.search(r'\d{1,3}%.*předtím', description):
                            extracted_price = self._extract_price(description)
                            if extracted_price is not None:
                              sale_price = extracted_price
                        
                        # Extract unit price from promotion
                        unit_selling_info = promotion.get('unitSellingInfo', '')
                        if unit_selling_info:
                            try:
                                sale_ppu = float(unit_selling_info.split(" ")[0].replace(",", "."))
                            except (ValueError, IndexError):
                                pass
                
                unit_code = seller_info["price"]["unitOfMeasure"]
                product_url = f"https://nakup.itesco.cz/groceries/cs-CZ/products/{node['id']}"
                
                # Create Product object
                product_obj = Product(
                    source="tesco",
                    product_category=category_name,
                    item_name=title,
                    image_url=image_url,
                    original_price=regular_price,
                    original_ppu=float(price_per_unit_default) if price_per_unit_default is not None else None,
                    sale_price=sale_price,
                    sale_ppu=sale_ppu,
                    unit_code=unit_code,
                    product_url=product_url,
                    sale_requirement=sale_requirement
                )
                
                products.append(product_obj)
                
            except (KeyError, IndexError) as e:
                logger.warning(f"Error processing item: {e}")
                continue
        
        # Determine if there are likely more pages: total_count bigger than items seen so far
        items_seen = (current_page + 1) * count_per_page
        has_more = total_count > items_seen and len(results_list) > 0
        return products, has_more

    def run(self):
        """Main scraping loop for all Tesco categories."""
        logger.info(f"Starting {self.source_name} scraper")
        
        for code, category_name in self.facets.items():
          logger.info(f"Scraping category: {code} ({category_name})")
            
          page = 0
          while True:
            response_data = self.fetch_category(code, page)
                
            if not response_data:
              break
                
            products, has_more = self.parse_response(response_data, category_name)
            if not products:
              break
                
            self.all_products.extend(products)
                
            if not has_more:
              break
                
            page += 1
            sleep(0.5)  # Be polite to the server
        
        logger.info(f"Scraped {len(self.all_products)} products from {self.source_name}")


if __name__ == "__main__":
    scraper = TescoScraper()
    scraper.run()
    scraper.save_to_json('output/tesco_products.json')