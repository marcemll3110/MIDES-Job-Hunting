"""
Scraping functions for job hunting automation
"""
import os
import time
import pandas as pd
import datetime
import certifi
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JobSearchBot:
    """
    A web automation bot for searching jobs on various job portals
    """
    
    def __init__(self, headless=True, timeout=10):
        """
        Initialize the job search bot
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Timeout for element waits in seconds
        """
        self.timeout = timeout
        self.driver = None
        self.headless = headless
        
    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Additional options for better performance and stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(5)
            logger.info("WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def search_jobs_linkedin(self, keyword, location="", max_results=50):
        """
        Search for jobs on LinkedIn
        
        Args:
            keyword (str): Job keyword to search for
            location (str): Location for job search
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        base_url = "https://www.linkedin.com/jobs/search/"
        
        try:
            if not self.driver:
                self.setup_driver()
            
            # Ensure driver is properly initialized
            if not self.driver:
                logger.error("Failed to initialize WebDriver")
                return jobs
            
            # Construct search URL
            search_params = f"?keywords={keyword.replace(' ', '%20')}"
            if location:
                search_params += f"&location={location.replace(' ', '%20')}"
            
            url = base_url + search_params
            logger.info(f"Searching LinkedIn jobs with URL: {url}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # Wait for job listings to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-search-card"))
            )
            
            # Scroll to load more results
            self._scroll_to_load_more(max_results)
            
            # Extract job information
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job-search-card")
            
            for card in job_cards[:max_results]:
                try:
                    job_info = self._extract_linkedin_job_info(card)
                    if job_info:
                        jobs.append(job_info)
                except Exception as e:
                    logger.warning(f"Failed to extract job info from card: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(jobs)} jobs from LinkedIn")
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn jobs: {e}")
        
        return jobs
    
    def search_jobs_indeed(self, keyword, location="", max_results=50):
        """
        Search for jobs on Indeed
        
        Args:
            keyword (str): Job keyword to search for
            location (str): Location for job search
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        base_url = "https://www.indeed.com/jobs"
        
        try:
            if not self.driver:
                self.setup_driver()
            
            # Ensure driver is properly initialized
            if not self.driver:
                logger.error("Failed to initialize WebDriver")
                return jobs
            
            # Construct search URL
            search_params = f"?q={keyword.replace(' ', '+')}"
            if location:
                search_params += f"&l={location.replace(' ', '+')}"
            
            url = base_url + search_params
            logger.info(f"Searching Indeed jobs with URL: {url}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # Wait for job listings to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job_seen_beacon"))
            )
            
            # Scroll to load more results
            self._scroll_to_load_more(max_results)
            
            # Extract job information
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
            
            for card in job_cards[:max_results]:
                try:
                    job_info = self._extract_indeed_job_info(card)
                    if job_info:
                        jobs.append(job_info)
                except Exception as e:
                    logger.warning(f"Failed to extract job info from card: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(jobs)} jobs from Indeed")
            
        except Exception as e:
            logger.error(f"Error searching Indeed jobs: {e}")
        
        return jobs
    
    def search_jobs_generic(self, url, keyword, search_selectors, max_results=50):
        """
        Generic job search function for any job portal
        
        Args:
            url (str): Base URL of the job portal
            keyword (str): Job keyword to search for
            search_selectors (dict): CSS selectors for different elements
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        
        try:
            if not self.driver:
                self.setup_driver()
            
            # Ensure driver is properly initialized
            if not self.driver:
                logger.error("Failed to initialize WebDriver")
                return jobs
            
            logger.info(f"Searching jobs on {url} with keyword: {keyword}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # Find and fill search input
            if 'search_input' in search_selectors:
                search_input = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, search_selectors['search_input']))
                )
                search_input.clear()
                search_input.send_keys(keyword)
                search_input.send_keys(Keys.RETURN)
                time.sleep(3)
            
            # Wait for results to load
            if 'job_listings' in search_selectors:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, search_selectors['job_listings']))
                )
            
            # Extract job information using provided selectors
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, search_selectors.get('job_listings', 'div'))
            
            for card in job_cards[:max_results]:
                try:
                    job_info = self._extract_generic_job_info(card, search_selectors)
                    if job_info:
                        jobs.append(job_info)
                except Exception as e:
                    logger.warning(f"Failed to extract job info from card: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(jobs)} jobs from {url}")
            
        except Exception as e:
            logger.error(f"Error searching jobs on {url}: {e}")
        
        return jobs
    
    def search_jobs_buscojobs_uy(self, keyword, location="", max_results=50):
        """
        Search for jobs on BuscoJobs Uruguay
        
        Args:
            keyword (str): Job keyword to search for
            location (str): Location for job search
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        base_url = "https://www.buscojobs.com.uy"
        
        try:
            if not self.driver:
                self.setup_driver()
            
            # Ensure driver is properly initialized
            if not self.driver:
                logger.error("Failed to initialize WebDriver")
                return jobs
            
            # Navigate to BuscoJobs Uruguay
            logger.info(f"Searching BuscoJobs Uruguay jobs with keyword: {keyword}")
            self.driver.get(base_url)
            time.sleep(3)
            
            # Wait for search form to load
            try:
                # Look for search input field
                search_input = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='buscar'], input[placeholder*='trabajo'], input[type='search'], input[name*='search']"))
                )
                
                # Clear and enter keyword
                search_input.clear()
                search_input.send_keys(keyword)
                
                # Look for location input if provided
                if location:
                    try:
                        location_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='ubicación'], input[placeholder*='location'], input[name*='location']")
                        location_input.clear()
                        location_input.send_keys(location)
                    except NoSuchElementException:
                        logger.info("Location input not found, proceeding with keyword search only")
                
                # Submit search
                search_input.send_keys(Keys.RETURN)
                time.sleep(3)
                
            except TimeoutException:
                logger.warning("Search form not found, trying direct URL approach")
                # Try direct URL approach if search form is not found
                search_url = f"{base_url}/buscar?q={keyword.replace(' ', '+')}"
                if location:
                    search_url += f"&location={location.replace(' ', '+')}"
                self.driver.get(search_url)
                time.sleep(3)
            
            # Wait for job listings to load
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='job'], [class*='listing'], [class*='card'], [class*='result']"))
                )
            except TimeoutException:
                logger.warning("Job listings not found with standard selectors, trying alternative approach")
            
            # Scroll to load more results
            self._scroll_to_load_more(max_results)
            
            # Try multiple selectors for job cards
            job_selectors = [
                "[class*='job']",
                "[class*='listing']", 
                "[class*='card']",
                "[class*='result']",
                "article",
                ".job-item",
                ".listing-item",
                ".card-item"
            ]
            
            job_cards = []
            for selector in job_selectors:
                try:
                    cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        job_cards = cards
                        logger.info(f"Found {len(cards)} job cards using selector: {selector}")
                        break
                except Exception:
                    continue
            
            # Extract job information
            for card in job_cards[:max_results]:
                try:
                    job_info = self._extract_buscojobs_job_info(card)
                    if job_info:
                        jobs.append(job_info)
                except Exception as e:
                    logger.warning(f"Failed to extract job info from card: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(jobs)} jobs from BuscoJobs Uruguay")
            
        except Exception as e:
            logger.error(f"Error searching BuscoJobs Uruguay jobs: {e}")
        
        return jobs
    
    def _scroll_to_load_more(self, max_results):
        """Scroll down to load more job results"""
        try:
            if not self.driver:
                return
                
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            loaded_results = 0
            
            while loaded_results < max_results:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Count current results
                current_results = len(self.driver.find_elements(By.CSS_SELECTOR, "[class*='job'], [class*='listing']"))
                loaded_results = current_results
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
        except Exception as e:
            logger.warning(f"Error during scrolling: {e}")
    
    def _extract_linkedin_job_info(self, job_card):
        """Extract job information from LinkedIn job card"""
        try:
            job_info = {
                'title': '',
                'company': '',
                'location': '',
                'posted_date': '',
                'job_url': '',
                'source': 'LinkedIn'
            }
            
            # Extract title
            title_elem = job_card.find_element(By.CSS_SELECTOR, "[class*='job-card-list__title']")
            if title_elem:
                job_info['title'] = title_elem.text.strip()
                job_info['job_url'] = title_elem.get_attribute('href')
            
            # Extract company
            company_elem = job_card.find_element(By.CSS_SELECTOR, "[class*='job-card-container__company-name']")
            if company_elem:
                job_info['company'] = company_elem.text.strip()
            
            # Extract location
            location_elem = job_card.find_element(By.CSS_SELECTOR, "[class*='job-card-container__metadata-item']")
            if location_elem:
                job_info['location'] = location_elem.text.strip()
            
            # Extract posted date
            date_elem = job_card.find_element(By.CSS_SELECTOR, "[class*='job-card-container__list-item']")
            if date_elem:
                job_info['posted_date'] = date_elem.text.strip()
            
            return job_info
            
        except Exception as e:
            logger.warning(f"Error extracting LinkedIn job info: {e}")
            return None
    
    def _extract_indeed_job_info(self, job_card):
        """Extract job information from Indeed job card"""
        try:
            job_info = {
                'title': '',
                'company': '',
                'location': '',
                'posted_date': '',
                'job_url': '',
                'source': 'Indeed'
            }
            
            # Extract title
            title_elem = job_card.find_element(By.CSS_SELECTOR, "[class*='jobTitle']")
            if title_elem:
                job_info['title'] = title_elem.text.strip()
                job_info['job_url'] = title_elem.get_attribute('href')
            
            # Extract company
            company_elem = job_card.find_element(By.CSS_SELECTOR, "[class*='companyName']")
            if company_elem:
                job_info['company'] = company_elem.text.strip()
            
            # Extract location
            location_elem = job_card.find_element(By.CSS_SELECTOR, "[class*='companyLocation']")
            if location_elem:
                job_info['location'] = location_elem.text.strip()
            
            # Extract posted date
            date_elem = job_card.find_element(By.CSS_SELECTOR, "[class*='date']")
            if date_elem:
                job_info['posted_date'] = date_elem.text.strip()
            
            return job_info
            
        except Exception as e:
            logger.warning(f"Error extracting Indeed job info: {e}")
            return None
    
    def _extract_generic_job_info(self, job_card, selectors):
        """Extract job information using generic selectors"""
        try:
            job_info = {
                'title': '',
                'company': '',
                'location': '',
                'posted_date': '',
                'job_url': '',
                'source': 'Generic'
            }
            
            # Extract title
            if 'title' in selectors:
                title_elem = job_card.find_element(By.CSS_SELECTOR, selectors['title'])
                if title_elem:
                    job_info['title'] = title_elem.text.strip()
                    job_info['job_url'] = title_elem.get_attribute('href')
            
            # Extract company
            if 'company' in selectors:
                company_elem = job_card.find_element(By.CSS_SELECTOR, selectors['company'])
                if company_elem:
                    job_info['company'] = company_elem.text.strip()
            
            # Extract location
            if 'location' in selectors:
                location_elem = job_card.find_element(By.CSS_SELECTOR, selectors['location'])
                if location_elem:
                    job_info['location'] = location_elem.text.strip()
            
            # Extract posted date
            if 'date' in selectors:
                date_elem = job_card.find_element(By.CSS_SELECTOR, selectors['date'])
                if date_elem:
                    job_info['posted_date'] = date_elem.text.strip()
            
            return job_info
            
        except Exception as e:
            logger.warning(f"Error extracting generic job info: {e}")
            return None
    
    def _extract_buscojobs_job_info(self, job_card):
        """Extract job information from BuscoJobs Uruguay job card"""
        try:
            job_info = {
                'title': '',
                'company': '',
                'location': '',
                'posted_date': '',
                'job_url': '',
                'source': 'BuscoJobs Uruguay'
            }
            
            # Try multiple selectors for job title
            title_selectors = [
                "h1", "h2", "h3", "h4",
                "[class*='title']",
                "[class*='job-title']",
                "[class*='position']",
                "a[href*='job']",
                "a[href*='trabajo']"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    if title_elem:
                        job_info['title'] = title_elem.text.strip()
                        # Get URL if it's a link
                        if title_elem.tag_name == 'a':
                            job_info['job_url'] = title_elem.get_attribute('href')
                        break
                except NoSuchElementException:
                    continue
            
            # Try multiple selectors for company name
            company_selectors = [
                "[class*='company']",
                "[class*='empresa']",
                "[class*='employer']",
                "span[class*='company']",
                "div[class*='company']"
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    if company_elem:
                        job_info['company'] = company_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Try multiple selectors for location
            location_selectors = [
                "[class*='location']",
                "[class*='ubicación']",
                "[class*='place']",
                "[class*='city']",
                "span[class*='location']",
                "div[class*='location']"
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    if location_elem:
                        job_info['location'] = location_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Try multiple selectors for posted date
            date_selectors = [
                "[class*='date']",
                "[class*='fecha']",
                "[class*='time']",
                "[class*='posted']",
                "span[class*='date']",
                "div[class*='date']"
            ]
            
            for selector in date_selectors:
                try:
                    date_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    if date_elem:
                        job_info['posted_date'] = date_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # If no job URL found, try to find any link in the card
            if not job_info['job_url']:
                try:
                    link_elem = job_card.find_element(By.CSS_SELECTOR, "a[href]")
                    job_info['job_url'] = link_elem.get_attribute('href')
                except NoSuchElementException:
                    pass
            
            # Only return if we have at least a title
            if job_info['title']:
                return job_info
            
        except Exception as e:
            logger.warning(f"Error extracting BuscoJobs job info: {e}")
        
        return None
    
    def save_jobs_to_excel(self, jobs, filename=None):
        """
        Save job results to Excel file
        
        Args:
            jobs (list): List of job dictionaries
            filename (str): Output filename (optional)
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_search_results_{timestamp}.xlsx"
        
        try:
            df = pd.DataFrame(jobs)
            df.to_excel(filename, index=False)
            logger.info(f"Job results saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving jobs to Excel: {e}")
            return None
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")


def search_jobs_multiple_sources(keywords, locations=None, max_results_per_source=25):
    """
    Search for jobs across multiple sources
    
    Args:
        keywords (list): List of job keywords to search for
        locations (list): List of locations to search in (optional)
        max_results_per_source (int): Maximum results per source
        
    Returns:
        list: Combined list of all job results
    """
    if locations is None:
        locations = [""]
    
    all_jobs = []
    bot = JobSearchBot(headless=True)
    
    try:
        for keyword in keywords:
            for location in locations:
                logger.info(f"Searching for '{keyword}' in '{location}'")
                
                # Search LinkedIn
                linkedin_jobs = bot.search_jobs_linkedin(keyword, location, max_results_per_source)
                all_jobs.extend(linkedin_jobs)
                
                # Search Indeed
                indeed_jobs = bot.search_jobs_indeed(keyword, location, max_results_per_source)
                all_jobs.extend(indeed_jobs)
                
                # Search BuscoJobs Uruguay
                buscojobs_jobs = bot.search_jobs_buscojobs_uy(keyword, location, max_results_per_source)
                all_jobs.extend(buscojobs_jobs)
                
                # Add small delay between searches
                time.sleep(2)
    
    finally:
        bot.close()
    
    # Remove duplicates based on title and company
    unique_jobs = []
    seen = set()
    
    for job in all_jobs:
        job_key = (job.get('title', ''), job.get('company', ''))
        if job_key not in seen:
            seen.add(job_key)
            unique_jobs.append(job)
    
    logger.info(f"Total unique jobs found: {len(unique_jobs)}")
    return unique_jobs


def search_jobs_buscojobs_only(keywords, locations=None, max_results_per_source=25):
    """
    Search for jobs only on BuscoJobs Uruguay
    
    Args:
        keywords (list): List of job keywords to search for
        locations (list): List of locations to search in (optional)
        max_results_per_source (int): Maximum results per source
        
    Returns:
        list: List of job results from BuscoJobs Uruguay
    """
    if locations is None:
        locations = [""]
    
    all_jobs = []
    bot = JobSearchBot(headless=True)
    
    try:
        for keyword in keywords:
            for location in locations:
                logger.info(f"Searching BuscoJobs Uruguay for '{keyword}' in '{location}'")
                
                # Search BuscoJobs Uruguay
                buscojobs_jobs = bot.search_jobs_buscojobs_uy(keyword, location, max_results_per_source)
                all_jobs.extend(buscojobs_jobs)
                
                # Add small delay between searches
                time.sleep(2)
    
    finally:
        bot.close()
    
    # Remove duplicates based on title and company
    unique_jobs = []
    seen = set()
    
    for job in all_jobs:
        job_key = (job.get('title', ''), job.get('company', ''))
        if job_key not in seen:
            seen.add(job_key)
            unique_jobs.append(job)
    
    logger.info(f"Total unique jobs found on BuscoJobs Uruguay: {len(unique_jobs)}")
    return unique_jobs


if __name__ == "__main__":

    
    # Example usage for BuscoJobs Uruguay only
    keywords = ["Desarrollador Python", "Data Scientist", "Ingeniero de Software"]
    locations = ["Montevideo", "Uruguay"]
    
    # Search for jobs on BuscoJobs Uruguay
    jobs = search_jobs_buscojobs_only(keywords, locations, max_results_per_source=10)
    
    # Save results
    if jobs:
        bot = JobSearchBot()
        bot.save_jobs_to_excel(jobs, "buscojobs_uruguay_results.xlsx")
        bot.close()
        
        print(f"Found {len(jobs)} jobs on BuscoJobs Uruguay. Results saved to buscojobs_uruguay_results.xlsx")
        
        # Print first few results
        for i, job in enumerate(jobs[:5]):
            print(f"\n{i+1}. {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Posted: {job.get('posted_date', 'N/A')}")
            print(f"   URL: {job.get('job_url', 'N/A')}")
    else:
        print("No jobs found on BuscoJobs Uruguay.")