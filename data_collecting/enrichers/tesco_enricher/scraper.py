import platform
import time
import random
from camoufox.sync_api import Camoufox

def get_headless_mode():
    """
    Detects if running in Docker (Linux) to use 'virtual' mode 
    for better stability and stealth.
    """
    if platform.system() == "Linux":
        return "virtual"  # Uses Xvfb (requires the Dockerfile setup provided previously)
    return True  # Standard headless for macOS/Windows

def save_tesco_html(url, output_file="tesco_page.html"):
    mode = get_headless_mode()
    print(f"🚀 Starting Camoufox in '{mode}' mode...")

    # Initialize browser
    # geoip=False saves memory/bandwidth. Enable it if you need location spoofing.
    with Camoufox(headless=mode, geoip=False) as browser:
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Set timeout to 60s to avoid early failures
        page.set_default_timeout(60000)

        print(f"🌍 Navigating to: {url}")
        try:
            # Go to the page and wait for the DOM to be ready
            page.goto(url, wait_until="domcontentloaded")
            
            # CRITICAL: Wait for dynamic content (hydration)
            # Tesco loads price and details via JS after the initial paint.
            print("⏳ Waiting for dynamic content to load...")
            time.sleep(4) 
            
            # Optional: Scroll to bottom to trigger lazy-loading elements
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)

            # Get the full HTML
            full_html = page.content()

            # Save to file
            print(f"💾 Saving to {output_file}...")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(full_html)
            
            print("✅ Done! File saved successfully.")

        except Exception as e:
            print(f"❌ Error: {e}")
            # Save a screenshot for debugging if it fails
            page.screenshot(path="error_screenshot.png")

if __name__ == "__main__":
    target_url = "https://nakup.itesco.cz/groceries/cs-CZ/products/212302210"
    save_tesco_html(target_url, "tesco_product.html")