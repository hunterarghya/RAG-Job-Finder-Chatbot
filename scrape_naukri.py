import time
import logging
from urllib.parse import urljoin, quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def make_driver(headless=False):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
    # uncomment if need a deterministic viewport in headless
    # opts.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=opts)

def scrape_naukri(job, location="", max_pages=1, headless=False):
    """
    Scrape Naukri search results (robust to multiple layouts).
    Returns a list of dicts with fields:
      title, company, location, salary, experience, tags, post_date, description, link
    """
    driver = make_driver(headless=headless)
    results = []

    # format that tends to return server-rendered pages
    q = quote_plus(job.replace(" ", "-"))
    if location:
        loc = quote_plus(location.replace(" ", "-"))
        start_url = f"https://www.naukri.com/{q}-jobs-in-{loc}"
    else:
        start_url = f"https://www.naukri.com/{q}-jobs"

    logging.info("Start URL: %s", start_url)

    try:
        for page in range(max_pages):
            page_num = page + 1
            url = f"{start_url}?p={page_num}"
            logging.info("Scraping page %d: %s", page_num, url)

            driver.get(url)
            time.sleep(2.5)  # let initial HTML/JS settle

            # attempt to force-load lazy content
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1.0)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.0)
            except Exception:
                pass

            # Try several card selectors (layout + common fallbacks)
            card_selectors = [
                "div.cust-job-tuple",    
                "article.jobTuple",  
                "div.listingTuple",
                "div.jobTuple",          
                "a.title"
            ]

            job_cards = []
            for sel in card_selectors:
                try:
                    found = driver.find_elements(By.CSS_SELECTOR, sel)
                    if found and len(found) > 0:
                        job_cards = found
                        logging.info("Found %d job cards using selector: %s", len(found), sel)
                        break
                except Exception:
                    continue

            if not job_cards:
                logging.warning("No job cards found on page %d — page HTML may be different or blocked.", page_num)
                continue

            for jcard in job_cards:
                try:
                    inner_html = jcard.get_attribute("innerHTML")
                    soup = BeautifulSoup(inner_html, "html.parser")
                except Exception:
                    logging.exception("Failed to parse job card; skipping")
                    continue

                # Title & link (preferred selector: a.title)
                title_tag = soup.select_one("a.title") or soup.select_one("h2 a") or soup.select_one("a")
                title = title_tag.get_text(strip=True) if title_tag else None
                link = title_tag.get("href") if title_tag and title_tag.has_attr("href") else None
                if link:
                    link = urljoin("https://www.naukri.com", link)

                # Company
                comp_tag = soup.select_one("a.comp-name") or soup.select_one("a.subTitle") or soup.select_one(".comp-dtls-wrap a")
                company = comp_tag.get_text(strip=True) if comp_tag else None

                # Experience
                exp_tag = soup.select_one(".exp-wrap .expwdth") or soup.select_one(".exp-wrap")
                experience = exp_tag.get_text(strip=True) if exp_tag else None

                # Salary (search for title attribute inside salary wrapper)
                salary_tag = soup.select_one(".sal-wrap span[title]") or soup.select_one(".sal-wrap") or soup.select_one(".sal-wrap span")
                salary = None
                if salary_tag:
                    # salary spans that use title attribute with full text
                    salary = salary_tag.get("title") or salary_tag.get_text(strip=True)

                # Location
                loc_tag = soup.select_one(".loc-wrap span[title]") or soup.select_one(".loc-wrap .locWdth") or soup.select_one(".loc-wrap")
                location_text = None
                if loc_tag:
                    location_text = loc_tag.get("title") or loc_tag.get_text(strip=True)

                # Short description available on the card (if present)
                card_desc = soup.select_one(".job-desc") or soup.select_one(".short-desc") or soup.select_one(".description")
                card_description = card_desc.get_text(strip=True) if card_desc else None

                # Tags (list)
                tag_nodes = soup.select("ul.tags-gt li.tag-li")
                tags = [t.get_text(strip=True) for t in tag_nodes] if tag_nodes else []

                # Post date
                post_date_tag = soup.select_one(".job-post-day") or soup.select_one(".post-date")
                post_date = post_date_tag.get_text(strip=True) if post_date_tag else None

                # Fetch full description from job page (open new tab)
                full_description = None
                if link:
                    full_description = scrape_naukri_description(driver, link)

                # results.append({
                #     "title": title,
                #     "company": company,
                #     "experience": experience,
                #     "salary": salary,
                #     "location": location_text,
                #     "card_description": card_description,
                #     "description": full_description,
                #     "tags": tags,
                #     "post_date": post_date,
                #     "link": link
                # })
                results.append({
                    "title": title or "N/A",
                    "company": company or "N/A",
                    "location": location_text or "N/A",
                    "salary": salary or "N/A",

                    # Prefer full description, fallback to card description
                    "description": full_description or card_description or "N/A",

                    "link": link or "N/A",
                    "source": "naukri",

                    
                    "extra": {
                        "experience": experience,
                        "tags": tags,
                        "post_date": post_date,
                        "card_description": card_description
                    }
                })


            # pause between pages
            time.sleep(1.2)

    except WebDriverException:
        logging.exception("WebDriver failed unexpectedly.")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    return results

def scrape_naukri_description(driver, link):
    """
    Open job page in a new tab and extract the job description. Defensive fallbacks included.
    Returns a trimmed string (or None on failure).
    """
    if not link:
        return None

    try:
        # open new tab
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(link)
        time.sleep(2.0)  # let page load

        # attempt to scroll a bit to trigger lazy description load
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(0.8)
        except Exception:
            pass

        # try multiple selectors for the JD block
        desc_selectors = [
            "div.jd-container",
            "div.job-desc",
            "section.job-desc",
            "#jobDescriptionText",
            "div.description",
            "div#jobDescription"
        ]

        desc_text = None
        for sel in desc_selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                if elems and len(elems) > 0:
                    # join visible text blocks
                    texts = [e.text.strip() for e in elems if e.text.strip()]
                    if texts:
                        desc_text = "\n\n".join(texts)
                        break
            except Exception:
                continue

        # fallback: first sizable block of body text (avoid nav/footer noise)
        if not desc_text:
            body = driver.find_element(By.TAG_NAME, "body")
            full_body = body.text.strip()
            # try to trim to a description-like chunk
            if len(full_body) > 500:
                desc_text = full_body[:5000]
            else:
                desc_text = full_body

        # close tab and return to main window
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        # final cleanup & trimming
        if desc_text:
            desc_text = desc_text.replace("\r", "\n").strip()
            if len(desc_text) > 8000:
                desc_text = desc_text[:8000]
        return desc_text

    except Exception:
        try:
            driver.close()
        except Exception:
            pass
        try:
            driver.switch_to.window(driver.window_handles[0])
        except Exception:
            pass
        logging.exception("Unable to fetch description for %s", link)
        return None

