from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

class DNBScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.base_url = "https://www.dnb.com"

    def random_delay(self):
        time.sleep(random.uniform(2, 5))

    def get_company_details(self, company_url):
        try:
            full_url = urljoin(self.base_url, company_url)
            print(f"Accessing company details at: {full_url}")

            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(full_url)
            self.random_delay()

            details = {}

            # Get address
            try:
                # Try to locate address inside <a>
                address_elem = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span.company_data_point[name="company_address"] a'))
                )
                details['address'] = address_elem.text.strip()
            except TimeoutException:
                try:
                    # Fallback to address without <a>
                    address_elem = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'span.company_data_point[name="company_address"] span'))
                    )
                    details['address'] = address_elem.text.strip()
                except TimeoutException:
                    details['address'] = ''


            # Get contacts
            contacts = []
            try:
                contacts_div = self.driver.find_element(By.CLASS_NAME, 'contacts-body')
                employees = contacts_div.find_elements(By.CLASS_NAME, 'employee')
                
                for employee in employees:
                    try:
                        name = employee.find_element(By.CLASS_NAME, 'name').text.strip()
                        if not name.startswith('Contact'):
                            position = employee.find_element(By.CLASS_NAME, 'position').text.strip()
                            contacts.append({
                                'name': name,
                                'position': position
                            })
                    except NoSuchElementException:
                        continue
                        
            except NoSuchElementException:
                pass

            details['contacts'] = contacts
            
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            return details
            
        except Exception as e:
            print(f"Error getting company details: {e}")
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            return {'address': '', 'contacts': []}

    def get_max_page(self):
        """Get the maximum page number from pagination"""
        try:
            pagination = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'integratedSearchPaginationPagination'))
            )
            pages = pagination.find_elements(By.CSS_SELECTOR, 'li.page a')
            if pages:
                # Get all page numbers and find the maximum
                page_numbers = [int(page.text) for page in pages if page.text.isdigit()]
                return max(page_numbers) if page_numbers else 1
            return 1
        except Exception as e:
            print(f"Error getting max page: {e}")
            return 1

    def scrape_page(self, results_div):
        """Scrape companies from a single page"""
        companies = []
        company_links = results_div.find_elements(By.CSS_SELECTOR, 'div.col-md-6 > a')
        
        for link in company_links:
            try:
                company_info = {}
                
                href = link.get_attribute('href')
                if href:
                    href = href.replace(self.base_url, '')
                    company_info['url'] = href
                    company_info['full_url'] = urljoin(self.base_url, href)
                
                company_info['name'] = link.text.strip()
                
                parent_data_div = link.find_element(By.XPATH, "../../..")
                location_div = parent_data_div.find_element(By.CLASS_NAME, 'col-md-4')
                company_info['location'] = location_div.text.replace('Country:', '').strip()
                
                details = self.get_company_details(company_info['url'])
                company_info.update(details)
                
                companies.append(company_info)
                print(f"Scraped: {company_info['name']}")
                print(f"Original href: {company_info['url']}")
                
            except Exception as e:
                print(f"Error processing company: {e}")
                continue
                
        return companies

    def scrape_companies(self, url):
        """Scrape companies from all available pages"""
        all_companies = []
        current_page = 1
        
        try:
            self.driver.get(url)
            self.random_delay()
            
            # Get max page number
            max_page = self.get_max_page()
            print(f"Found {max_page} pages to scrape")
            
            while current_page <= max_page:
                print(f"\nScraping page {current_page} of {max_page}")
                
                # Wait for results to load
                results_div = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'companyResults'))
                )
                
                # Scrape current page
                page_companies = self.scrape_page(results_div)
                all_companies.extend(page_companies)
                
                if current_page < max_page:
                    # Construct next page URL
                    parsed_url = urlparse(url)
                    query_params = parse_qs(parsed_url.query)
                    query_params['page'] = [str(current_page + 1)]
                    next_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(query_params, doseq=True)}"
                    
                    print(f"Navigating to page {current_page + 1}")
                    self.driver.get(next_url)
                    self.random_delay()
                
                current_page += 1
            
            return all_companies
            
        except Exception as e:
            print(f"Error scraping companies: {e}")
            return all_companies

    def save_to_csv(self, companies, filename='Highway, Street, and Bridge Construction.csv'):
        if not companies:
            print("No data to save")
            return
            
        flattened_data = []
        for company in companies:
            company_data = {
                'name': company['name'],
                'address': company['address'],
                'full_url': company['full_url']
            }
            
            contacts = company.get('contacts', [])
            for i, contact in enumerate(contacts, 1):
                company_data[f'contact_{i}_name'] = contact['name']
                company_data[f'contact_{i}_position'] = contact['position']
                
            flattened_data.append(company_data)
            
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False)
        print(f"\nData saved to {filename}")
        print(f"Total companies scraped: {len(flattened_data)}")

    def close(self):
        self.driver.quit()

# Usage example
if __name__ == "__main__":
    url = "https://www.dnb.com/business-directory/company-information.highway_street_and_bridge_construction.id.jawa_timur.html"
    
    try:
        scraper = DNBScraper()
        companies = scraper.scrape_companies(url)
        scraper.save_to_csv(companies)
    finally:
        scraper.close()
