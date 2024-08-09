import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

def get_product_links(base_url, num_pages):
    product_hrefs = []

    for page_num in range(1, num_pages + 1):
        # Construct the URL for the current page
        url = f"{base_url}{page_num}"

        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all `a` tags with `data-track="web:store:product-tile"`
            product_links = soup.find_all('a', {'data-track': 'web:store:product-tile'})

            # Iterate over each product link and add the href attribute to the list
            for link in product_links:
                href = link.get('href')
                product_hrefs.append(href)
        else:
            print(f"Failed to retrieve page {page_num}. Status code: {response.status_code}")

    return product_hrefs

def construct_full_product_urls(product_hrefs, base_product_url="https://store.playstation.com/"):
    full_urls = [f"{base_product_url}{href}" for href in product_hrefs]
    return full_urls


def search_ebgames(title, platform='PlayStation 4'):
    formatted_title = title.lower()
    search_url = f"https://www.ebgames.com.au/search/query?q={formatted_title}"

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Path to your ChromeDriver
    chrome_driver_path = "chromedriver-mac-arm64/chromedriver"  # Update this with your ChromeDriver path

    # Initialize WebDriver
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Navigate to the search URL
        driver.get(search_url)

        # Wait for the product cards to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.search-result__product')))

        # Extract JSON data from the page source
        script_tag = driver.find_element(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        json_data = script_tag.get_attribute('innerHTML')

        # Parse JSON data
        data = json.loads(json_data)

        prices = []
        for product in data.get('results', []):
            if product.get('platformName') == platform:
                price = product.get('price')
                title = product.get('title')
                preowned = product.get('isPreowned')
                prices.append((title, price, preowned))

        if not prices:
            return "No products found for the specified platform."

        for title, price, preowned in prices:
            condition = "Pre-owned" if preowned else "New"
            print(f"Product: {title} | Price: {price} | Condition: {condition}")

        return prices
    except Exception as e:
        print(f"Error occurred: {e}")
        return f"Error occurred: {e}"
    finally:
        driver.quit()


def search_bigw(title):
    # Replace spaces with '+' and handle '&' for URL formatting
    formatted_title = title.replace(' ', '+').replace('&', '%26')
    search_url = f"https://www.bigw.com.au/search?text={formatted_title}&filter%5Bformat%5D=PlayStation+5&filter%5Bformat%5D=PlayStation+4"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()  # Raises an exception for HTTP errors
        print(response.text)
        return response.text
    except requests.RequestException as e:
        print(f"Error occurred: {e}")
        return f"Error occurred: {e}"


def search_jbhifi(title):
    def format_title(title):
        # Replace spaces with hyphens, but avoid trailing hyphens
        title = re.sub(r'\s+', '-', title.strip())
        title = re.sub(r'-+', '-', title)
        return title.strip('-').lower()

    formatted_title = format_title(title)
    product_url = f"https://www.jbhifi.com.au/products/playstation-4-{formatted_title}"
    try:
        # Send the HTTP request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(product_url, headers=headers)

        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the price from the meta tag
            price_meta = soup.find('meta', {'property': 'og:price:amount'})

            if price_meta:
                price = price_meta['content']
                print(f"Price: {price}")
                return price
            return "Price not found"
        else:
            return f"Error: received status code {response.status_code}"
    except Exception as e:
        print(f"Error occurred: {e}")
        return f"Error occurred: {e}"


def visit_product_pages(full_product_urls):
    for url in full_product_urls:
        response = requests.get(url)
        if response.status_code == 200:
            # Process the page if needed, here we just print the URL
            soup = BeautifulSoup(response.text, 'html.parser')
            game_title = soup.find('h1', {'data-qa': 'mfe-game-title#name'})
            game_title = soup.find('h1', {'data-qa': 'mfe-game-title#name'})
            title = game_title.text.strip() if game_title else "Title not found"
            if title != "Title not found":
                replacements = ["PS4", "PS5", "®", "&", "PS4 & PS5",'- Game of the Year Edition','-','Game of the Year Edition']
                for rep in replacements:
                    title = title.replace(rep, "")


            game_image_span = soup.find('span', {'data-qa': 'gameBackgroundImage#heroImage'})
            game_image_tag = game_image_span.find('img', {'data-qa': 'gameBackgroundImage#heroImage#image-no-js'})
            game_image = game_image_tag['src'].replace('&', '&amp;') if game_image_tag else "Game image not found"

            game_publisher = soup.find('div', {'data-qa': 'mfe-game-title#publisher'})
            if game_publisher:
                publisher = game_publisher.text.strip()
            else:
                publisher = "Publisher not found"

            player_rating = soup.find('div', {'data-qa': 'mfe-game-title#average-rating'})
            rating = player_rating.text.strip() if player_rating else "Rating not found"



            # Find the text descriptors
            text_descriptors = soup.find('span', {'data-qa': 'mfe-content-rating#textDescriptors'})
            age_restriction = text_descriptors.text.strip() if text_descriptors else "Descriptors not found"


            # Find the restriction icon
            restriction_icon_span = soup.find('span', {'data-qa': 'mfe-content-rating#ratingImage'})
            restriction_icon_img = restriction_icon_span.find('img') if restriction_icon_span else None
            restriction_icon = restriction_icon_img['src'].replace('&', '&amp;') if restriction_icon_img else "Restriction icon not found"

            final_price_span = soup.find('span', {'data-qa': 'mfeCtaMain#offer0#finalPrice'})
            final_price = final_price_span.text.strip() if final_price_span else None

            original_price_span = soup.find('span', {'data-qa': 'mfeCtaMain#offer0#originalPrice'})
            original_price = original_price_span.text.strip() if original_price_span else None

            key_features_dict = {}
            key_features_items = soup.find_all('li', {
                'data-qa': lambda x: x and x.startswith('mfe-compatibility-notices#notices#listItem')})
            for item in key_features_items:
                key_feature_span = item.find('span', {'data-qa': lambda x: x and x.endswith('#compatText')})
                key_feature_svg = item.find('span', {'data-qa': lambda x: x and x.endswith('#compatIcon')})
                if key_feature_span and key_feature_svg:
                    key_features_dict[str(key_feature_svg)] = key_feature_span.text.strip()



            release_date = soup.find('dd', {
                'data-qa': 'gameInfo#releaseInformation#releaseDate-value'}).text.strip() if soup.find('dd', {
                'data-qa': 'gameInfo#releaseInformation#releaseDate-value'}) else "Release date not found"
            genre = soup.find('dd', {'data-qa': 'gameInfo#releaseInformation#genre-value'}).text.strip() if soup.find(
                'dd', {'data-qa': 'gameInfo#releaseInformation#genre-value'}) else "Genre not found"
            ps4_voice_language = soup.find('dd', {
                'data-qa': 'gameInfo#releaseInformation#ps4Voice-value'}).text.strip() if soup.find('dd', {
                'data-qa': 'gameInfo#releaseInformation#ps4Voice-value'}) else None
            ps4_screen_languages = soup.find('dd', {
                'data-qa': 'gameInfo#releaseInformation#ps4Subtitles-value'}).text.strip() if soup.find('dd', {
                'data-qa': 'gameInfo#releaseInformation#ps4Subtitles-value'}) else None

            # Fallback to generic voice and screen languages if PS5-specific ones are not found
            voice_language = ps4_voice_language if ps4_voice_language else (
                soup.find('dd', {'data-qa': 'gameInfo#releaseInformation#voice-value'}).text.strip() if soup.find('dd',
                                                                                                                  {
                                                                                                                      'data-qa': 'gameInfo#releaseInformation#voice-value'}) else "Voice language not found")
            screen_languages = ps4_screen_languages if ps4_screen_languages else (
                soup.find('dd', {'data-qa': 'gameInfo#releaseInformation#subtitles-value'}).text.strip() if soup.find(
                    'dd', {'data-qa': 'gameInfo#releaseInformation#subtitles-value'}) else "Screen languages not found")
            platform = soup.find('dd',
                                 {'data-qa': 'gameInfo#releaseInformation#platform-value'}).text.strip() if soup.find(
                'dd', {'data-qa': 'gameInfo#releaseInformation#platform-value'}) else "Platform not found"
            if final_price and original_price:
                discount_price = final_price
                regular_price = original_price
            elif final_price:
                discount_price = final_price
                regular_price = final_price
            else:
                discount_price = "Price not found"
                regular_price = "Price not found"

            game_description_p = soup.find('p', {'data-qa': 'mfe-game-overview#description'})
            game_description = str(game_description_p) if game_description_p else "Description not found"
            additional_description_div = soup.find('div', {'data-qa': 'mfe-legal-text#text'})
            additional_description = str(additional_description_div) if additional_description_div else "Additional description not found"

            dlc_list = []
            dlc_items = soup.find_all('div', {'data-qa': lambda x: x and x.startswith('add-ons-grid#')})
            for dlc in dlc_items:
                dlc_name_span = dlc.find('span', {'data-qa': lambda x: x and x.endswith('#product-name')})
                dlc_name = dlc_name_span.text.strip() if dlc_name_span else "DLC name not found"
                dlc_name_span = dlc.find('span', {'data-qa': lambda x: x and x.endswith('#product-name')})
                dlc_name = dlc_name_span.text.strip() if dlc_name_span else None

                if dlc_name:
                    dlc_price_span = dlc.find('span', {'data-qa': lambda x: x and x.endswith('#price#display-price')})
                    dlc_price = dlc_price_span.text.strip() if dlc_price_span else "Price not found"

                    dlc_img_tag = dlc.find('img', {'class': 'psw-top-left psw-l-fit-cover'})
                    dlc_img = dlc_img_tag['src'] if dlc_img_tag else "Image not found"

                    dlc_list.append({'name': dlc_name, 'price': dlc_price, 'img_url': dlc_img})
            edition_list = []

            # Extract edition details
            edition_items = soup.find_all('article',
                                          {'data-qa': lambda x: x and x.startswith('mfeUpsell#productEdition')})
            for item in edition_items:
                edition_name = item.find('h3', {
                    'data-qa': lambda x: x and x.endswith('#editionName')}).text.strip() if item.find('h3', {
                    'data-qa': lambda x: x and x.endswith('#editionName')}) else "Edition name not found"
                edition_price = item.find('span', {
                    'data-qa': lambda x: x and x.endswith('#finalPrice')}).text.strip() if item.find('span', {
                    'data-qa': lambda x: x and x.endswith('#finalPrice')}) else "Price not found"
                edition_img_tag = item.find('img', {'class': 'psw-center psw-l-fit-contain'})
                edition_img_url = edition_img_tag['src'] if edition_img_tag else "Image not found"
                edition_content_items = item.find_all('li', {
                    'data-qa': lambda x: x and x.startswith('mfeUpsell#productEdition')})
                edition_content = [li.text.strip() for li in edition_content_items] if edition_content_items else [
                    "Content not found"]

                edition_list.append({
                    'name': edition_name,
                    'price': edition_price,
                    'img_url': edition_img_url,
                    'content': edition_content
                })
            print(title)
            jbhifi_price=search_jbhifi(title)
            ebgame_price= search_ebgames(title,platform='PlayStation 4')
            print(ebgame_price)
        else:
            print(f"Failed to visit: {url}. Status code: {response.status_code}")








# Base URL of the PlayStation 5 games page
base_url = "https://store.playstation.com/en-au/category/30e3fe35-8f2d-4496-95bc-844f56952e3c/"

# Number of pages to scrape
num_pages = 1  # Replace this number with the actual number of pages
# Retrieve product links
product_hrefs = get_product_links(base_url, num_pages)

# Construct full product URLs
full_product_urls = construct_full_product_urls(product_hrefs)

# Print the full product URLs
visit_product_pages(full_product_urls)
