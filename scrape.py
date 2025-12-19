# import time
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup

# def expand_shadow(driver, element):
#     """Access shadow DOM"""
#     return driver.execute_script("return arguments[0].shadowRoot", element)

# def scrape_indeed(job, location, max_pages=1):


#     #LOCAL -----------------------------------------------------------------------------
#     #-----------------------------------------------------------------------------------
#     chrome_options = Options()
#     # chrome_options.add_argument("--start-maximized")
#     # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     chrome_options.add_argument("--headless=new")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     chrome_options.add_argument("--disable-features=VizDisplayCompositor")
#     chrome_options.add_argument("--window-size=1920,1080")

#     driver = webdriver.Chrome(options=chrome_options)

#     #DOCKER------------------------------------------------------------------------------
#     #------------------------------------------------------------------------------------
#     # chrome_options = Options()
#     # chrome_options.add_argument("--headless=new")
#     # chrome_options.add_argument("--no-sandbox")
#     # chrome_options.add_argument("--disable-dev-shm-usage")
#     # chrome_options.add_argument("--disable-gpu")
#     # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     # chrome_options.add_argument("--disable-features=VizDisplayCompositor")
#     # chrome_options.add_argument("--window-size=1920,1080")

#     # driver = webdriver.Chrome(options=chrome_options)

#     #------------------------------------------------------------------------------------
#     #------------------------------------------------------------------------------------


#     results = []

#     base_url = f"https://in.indeed.com/jobs?q={job}&l={location}"

#     for page in range(max_pages):
#         start = page * 10
#         url = f"{base_url}&start={start}"
#         print(f"\nScraping page {page+1}: {url}")

#         driver.get(url)
#         time.sleep(4)

#         try:
            
#             root1 = driver.find_element(By.CSS_SELECTOR, "div#mosaic-provider-jobcards")
            
#             shadow_host = root1.find_element(By.CSS_SELECTOR, "mosaic-provider-jobcards")
#             shadow_root = expand_shadow(driver, shadow_host)

#             job_cards = shadow_root.find_elements(By.CSS_SELECTOR, "div.jobCard_mainContent")

#         except Exception:
#             print("WARNING!!! Shadow DOM structure changed — trying fallback selector")
#             job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")

#         if not job_cards:
#             print("WARNING!!! No job cards found. Indeed blocked or layout changed.")
#             continue

#         for job_card in job_cards:
#             soup = BeautifulSoup(job_card.get_attribute("innerHTML"), "html.parser")

#             title = soup.select_one("h2.jobTitle")
#             title = title.text.strip() if title else "N/A"

#             company = soup.select_one("span.companyName")
#             company = company.text.strip() if company else "N/A"

#             loc = soup.select_one("div.companyLocation")
#             loc = loc.text.strip() if loc else "N/A"

#             salary = soup.select_one("div.salary-snippet")
#             salary = salary.text.strip() if salary else "N/A"

#             # Extract job link
#             link_tag = soup.find("a")
#             if link_tag and link_tag.get("href"):
#                 link = "https://in.indeed.com" + link_tag.get("href")
#             else:
#                 link = "N/A"

#             # scraping actual job description from job page
#             description = scrape_description(driver, link)

#             # results.append({
#             #     "title": title,
#             #     "company": company,
#             #     "location": loc,
#             #     "salary": salary,
#             #     "description": description,
#             #     "link": link,
#             # })

#             results.append({
#                 "title": title or "N/A",
#                 "company": company or "N/A",
#                 "location": loc or "N/A",
#                 "salary": salary or "N/A",
#                 "description": description or "N/A",
#                 "link": link or "N/A",
#                 "source": "indeed",

                
#                 "extra": {}
#             })


#     driver.quit()
#     return results


# def scrape_description(driver, link):
#     """Open job page and scrape description inside its shadow DOM"""
#     if link == "N/A":
#         return "N/A"

#     try:
#         driver.execute_script("window.open('');")
#         driver.switch_to.window(driver.window_handles[-1])
#         driver.get(link)
#         time.sleep(3)

#         # Job description is inside <div id="jobDescriptionText">
#         desc = driver.find_elements(By.CSS_SELECTOR, "#jobDescriptionText")

#         if desc:
#             txt = desc[0].text.strip()
#         else:
#             # fallback
#             txt = driver.find_element(By.TAG_NAME, "body").text[:500]

#         driver.close()
#         driver.switch_to.window(driver.window_handles[0])
#         return txt

#     except Exception:
#         driver.close()
#         driver.switch_to.window(driver.window_handles[0])
#         return "Unable to fetch description"



import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup


def scrape_indeed(job, location, max_pages=1):
    """
    Scrape Indeed India job listings.
    Shadow DOM REMOVED.
    Uses stable <a class="tapItem"> job cards.
    """

    # ==============================
    # CHROME OPTIONS (LOCAL SAFE)
    # ==============================
    chrome_options = Options()

    #  DO NOT use headless locally (Indeed blocks it)
    # chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Realistic User-Agent (IMPORTANT)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)

    results = []

    base_url = f"https://in.indeed.com/jobs?q={job}&l={location}"

    for page in range(max_pages):
        start = page * 10
        url = f"{base_url}&start={start}"

        print(f"\nScraping page {page + 1}: {url}")

        driver.get(url)
        time.sleep(3)

        # Scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # ==============================
        # JOB CARDS (NO SHADOW DOM)
        # ==============================
        job_cards = driver.find_elements(By.CSS_SELECTOR, "a.tapItem")

        if not job_cards:
            print("WARNING!!! No job cards found. Indeed likely blocked.")
            continue

        for card in job_cards:
            soup = BeautifulSoup(card.get_attribute("innerHTML"), "html.parser")

            # ------------------------------
            # TITLE
            # ------------------------------
            title_tag = soup.select_one("h2.jobTitle span")
            title = title_tag.text.strip() if title_tag else "N/A"

            # ------------------------------
            # COMPANY
            # ------------------------------
            company_tag = soup.select_one("span.companyName")
            company = company_tag.text.strip() if company_tag else "N/A"

            # ------------------------------
            # LOCATION
            # ------------------------------
            loc_tag = soup.select_one("div.companyLocation")
            loc = loc_tag.text.strip() if loc_tag else "N/A"

            # ------------------------------
            # SALARY
            # ------------------------------
            salary_tag = soup.select_one("div.salary-snippet")
            salary = salary_tag.text.strip() if salary_tag else "N/A"

            # ------------------------------
            # JOB LINK (IMPORTANT FIX)
            # ------------------------------
            link = card.get_attribute("href")
            if link and not link.startswith("http"):
                link = "https://in.indeed.com" + link

            # ------------------------------
            # JOB DESCRIPTION
            # ------------------------------
            description = scrape_description(driver, link)

            results.append({
                "title": title or "N/A",
                "company": company or "N/A",
                "location": loc or "N/A",
                "salary": salary or "N/A",
                "description": description or "N/A",
                "link": link or "N/A",
                "source": "indeed",
                "extra": {}
            })

    driver.quit()
    return results


def scrape_description(driver, link):
    """
    Open job page in a new tab and scrape description.
    """

    if not link or link == "N/A":
        return "N/A"

    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])

        driver.get(link)
        time.sleep(3)

        desc_elem = driver.find_elements(By.CSS_SELECTOR, "#jobDescriptionText")

        if desc_elem:
            text = desc_elem[0].text.strip()
        else:
            # fallback
            text = driver.find_element(By.TAG_NAME, "body").text[:500]

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        return text

    except Exception:
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception:
            pass

        return "Unable to fetch description"
