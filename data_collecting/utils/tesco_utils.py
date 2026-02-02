import time
import threading
import undetected_chromedriver as uc
from loguru import logger

class CookieManager:
    _cookies = None
    _user_agent = None  # Add this to sync headers
    _lock = threading.Lock()

    @classmethod
    def get_session_data(cls, product_id, force_refresh=False):
        with cls._lock:
            if cls._cookies is None or force_refresh:
                cls._cookies, cls._user_agent = cls._fetch_from_browser(product_id)
            return cls._cookies, cls._user_agent

    @staticmethod
    def _fetch_from_browser(product_id):
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        driver = None
        try:
            driver = uc.Chrome(options=options, use_subprocess=True)
            
            # 1. Get the real User-Agent this specific driver instance is using
            user_agent = driver.execute_script("return navigator.userAgent")
            
            url = f'https://nakup.itesco.cz/groceries/cs-CZ/products/{product_id}'
            driver.get(url)
            
            # 2. Simulate human presence to validate Akamai (_abck cookie)
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(3)
            
            cookies = driver.get_cookies()
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            return cookie_string, user_agent
        finally:
            if driver:
                driver.quit()