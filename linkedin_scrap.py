import logging
import time
import random
import os
import pandas as pd
import requests
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
from dotenv import load_dotenv, find_dotenv

# Load the .env file
# load_dotenv()
load_dotenv(dotenv_path=".env", override=True)

print(f"Using .env file at: {find_dotenv()}")

# Fetch credentials
username = os.getenv('USERNAME')
# password = os.getenv('PASSWORD')

print(f"Username: {username}")


class LinkedInScraper:
    def __init__(self, excel_path=None):
        """Initialize the LinkedIn scraper with the excel file path"""
        if excel_path is None:
            # Default path if none provided
            self.excel_path = os.path.join(os.getcwd(), 'linkedin_data.xlsx')
        else:
            # Use provided path
            self.excel_path = excel_path
            
        self.results = []
        self.setup_driver()
        
        # Create output directory if it doesn't exist
        self.output_dir = os.path.join(os.path.dirname(self.excel_path), 'linkedin_results')
        os.makedirs(self.output_dir, exist_ok=True)
        
    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        # Uncomment the line below if you want to run in headless mode
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        
        # Add user agent to appear more like a regular browser
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)  # Increase page load timeout
            self.wait = WebDriverWait(self.driver, 15)  # Increase wait timeout
        except Exception as e:
            print(f"Error setting up driver: {e}")
            print("Trying alternative approach...")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_page_load_timeout(30)
                self.wait = WebDriverWait(self.driver, 15)
            except Exception as e2:
                print(f"Alternative approach also failed: {e2}")
                print("Please ensure Chrome and ChromeDriver are installed and compatible")
                exit(1)
        
    def read_excel(self):
        """Read credentials and search role from Excel file"""
        try:
            df = pd.read_excel(self.excel_path)
            if 'role' not in df.columns:
                raise Exception("Excel must contain 'role' columns")
            
            # Get the first row's data
            credentials = df.iloc[0]
            return credentials['role']
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            self.driver.quit()
            exit(1)
    
    def login(self, username, password):
        """Login to LinkedIn with the provided credentials"""
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(random.randint(5, 10))  # Random wait to avoid detection
            
            # Enter username
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.clear()  # Clear any pre-filled text
            username_field.click()  # Click to focus the field
            time.sleep(random.uniform(0.5, 1.5))  # Random wait to avoid detection
            username_field.send_keys(username)
            
            # Enter password
            password_field = self.wait.until(EC.presence_of_element_located((By.ID, "password")))
            password_field.clear()  # Clear any pre-filled text
            password_field.click()  # Click to focus the field
            time.sleep(random.uniform(0.5, 1.5))  # Random wait to avoid detection
            password_field.send_keys(password)
            
            # Click login button
            login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
            login_button.click()
            
            # Wait for login to complete
            time.sleep(random.randint(5, 10))  # Random wait to avoid detection
            
            # Check if login was successful by verifying we're on the home page
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'global-nav__me')]")))
                print("Login successful")
                return True
            except TimeoutException:
                print("Login failed or authentication challenge detected")
                return False
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def search_role(self, role):
        """Search for the given role and apply people filter"""
        try:
            # Navigate to LinkedIn search page directly
            self.driver.get("https://www.linkedin.com/search/results/all/")
            # self.driver.find_element(By.XPATH, "//input[@placeholder='Search']").click()
            time.sleep(random.randint(5, 10))  # Random wait to avoid detection
            
            # Wait for the search box and click on it
            search_box = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@class, 'search-global-typeahead__input')]")))
            search_box.click()
            search_box.clear()
            search_box.send_keys(role)
            search_box.send_keys(Keys.ENTER)
            
            # Wait longer for search results to load
            time.sleep(random.randint(5, 10))  # Random wait to avoid detection
            
            # Try different approaches to find and click the People filter
            try:
                # First attempt - standard approach
                people_filter = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'People')]")))
                people_filter.click()
            except:
                try:
                    # Second attempt - alternative selector
                    people_filter = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'People')]")))
                    people_filter.click()
                except:
                    try:
                        # Third attempt - clicking on filter section first
                        filter_section = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'search-reusables__filter-bar')]")))
                        filter_section.find_element(By.XPATH, ".//button[contains(text(), 'People') or contains(@aria-label, 'People')]").click()
                    except:
                        # Fourth attempt - try direct URL with query parameter
                        search_url = f"https://www.linkedin.com/search/results/people/?keywords={role.replace(' ', '%20')}"
                        print(f"Using direct URL: {search_url}")
                        self.driver.get(search_url)
            
            # Wait longer for the people filter to be applied
            time.sleep(random.randint(5, 10))  # Random wait to avoid detection
            
            # Verify that we're looking at people results
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'search-results__cluster')]")))
                print("Successfully filtered to people results")
                return True
            except:
                # One more attempt with a direct URL
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={role.replace(' ', '%20')}"
                print(f"Using direct URL as fallback: {search_url}")
                self.driver.get(search_url)
                time.sleep(random.randint(5, 10))  # Random wait to avoid detection
                return True
            
        except Exception as e:
            print(f"Error during role search: {e}")
            # Try one final approach - direct URL navigation
            try:
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={role.replace(' ', '%20')}"
                print(f"Using direct URL after error: {search_url}")
                self.driver.get(search_url)
                time.sleep(random.randint(5, 10))  # Random wait to avoid detection
                return True
            except:
                return False
    
    def scrape_profiles_on_page(self):
        """Scrape all profile names and URLs on the current page"""
        try:
            # Wait longer for search results to load
            time.sleep(random.randint(5, 10))  # Random wait to avoid detection
            
            # Try multiple selector approaches
            profile_containers = []
            selectors_to_try = [
                "//span[@dir='ltr']/parent::a",
                # "//li[contains(@class, 'reusable-search__result-container')]",
                # "//div[contains(@class, 'entity-result')]",
                # "//div[contains(@class, 'search-results__list')]//li"
            ]
            
            for selector in selectors_to_try:
                try:
                    profile_containers = self.driver.find_elements(By.XPATH, selector)
                    if profile_containers:
                        print(f"Found {len(profile_containers)} profiles using selector: {selector}")
                        print(f" Profile containers is {profile_containers}")
                        break
                except:
                    continue
            # profile_dictionary = {}
            # for profile in profile_containers:


            
            page_results = []
            
            if not profile_containers:
                print("No profile containers found. Trying alternative approach...")
                # Try a more general approach
                try:
                    # Look for any links that have LinkedIn profile patterns
                    profile_links = self.driver.find_elements(By.XPATH, "//span[@dir='ltr']/parent::a")
                    print(f"Profile links found: {len(profile_links)} links using selector: //span[@dir='ltr']/parent::a")
                    
                    for link in profile_links:
                        try:
                            profile_url = link.get_attribute('href')
                            if profile_url :
                                # Clean the URL
                                profile_url = profile_url.split('?')[0]  # Remove URL parameters
                                print(f"Found profile link: {profile_url}-1")
                                
                                # Try to get name from various approaches
                                name = ""
                                try:
                                    # Try parent element
                                    parent = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'entity-result__item')]")
                                    name_el = parent.find_element(By.XPATH, ".//span[contains(@class, 'entity-result__title-text')]")
                                    name = name_el.text.strip()
                                except:
                                    try:
                                        # Try the link text itself
                                        name = link.text.strip()
                                    except:
                                        # Use part of URL as fallback
                                        name = profile_url.split('/in/')[1].replace('/', '')
                                
                                if profile_url and name and profile_url not in [r['profile_url'] for r in page_results]:
                                    page_results.append({
                                        'name': name,
                                        'profile_url': profile_url,
                                        'linkedin_scraping_dog_info': self.linkedin_scraping_dog(profile_url)

                                    })
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"Alternative approach also failed: {e}")
            else:
                # Process the containers found with the original approach
                for container in profile_containers:
                    try:
                        # Try multiple ways to find the profile link
                        # profile_link_element = None
                        # selectors_to_try = [
                        #     ".//a[contains(@class, 'app-aware-link') and contains(@href, '/in/')]",
                        #     ".//a[contains(@href, '/in/')]",
                        #     ".//a[contains(@class, 'entity-result__title-text')]//a"
                        # ]
                        #
                        # for selector in selectors_to_try:
                        #     try:
                        #         profile_link_element = container.find_element(By.XPATH, selector)
                        #         if profile_link_element:
                        #             break
                        #     except:
                        #         continue
                        #
                        # if not profile_link_element:
                        #     continue
                            
                        profile_url = container.get_attribute('href')
                        if profile_url:
                            profile_url = profile_url.split('?')[0] # Remove URL parameters
                            profile_id = profile_url.split('/')[-1]  # Extract profile ID from URL
                            print(f"Found profile link: {profile_url}")
                            print(f"The profile url is {profile_url}")
                            linkedin_scraping_dog_info = self.linkedin_scraping_dog(profile_id)
                        
                        # Get name from the link or separate element
                        name = ""
                        try:
                            name_element = container.find_element(By.XPATH, ".//span[contains(@class, 'entity-result__title-text')]/a/span")
                            name = name_element.text.strip()
                            print(f"Found profile name: {name}")
                        except:
                            try:
                                name = container.text.strip()
                            except:
                                # Use part of URL as fallback
                                if '/in/' in profile_url:
                                    name = profile_url.split('/in/')[1].replace('/', '')
                        
                        if name and profile_url and profile_url not in [r['profile_url'] for r in page_results]:
                            page_results.append({
                                'name': name,
                                'profile_url': profile_url,
                                'linkedin_scraping_dog_info': linkedin_scraping_dog_info
                            })
                            
                    except Exception as e:
                        continue
            
            print(f"Scraped {len(page_results)} profiles from current page")
            return page_results
            
        except Exception as e:
            print(f"Error scraping profiles: {e}")
            return []

    def go_to_next_page(self):
        """Navigate to the next page using URL manipulation with end-page detection"""
        try:
            print("\n----- Starting Next Page Navigation -----")

            # Get the current URL and check if it contains page parameter
            current_url = self.driver.current_url
            print(f"Current URL: {current_url}")
            page=None
            if "page=" in current_url:
                # Extract current page number
                import re
                match = re.search(r'page=(\d+)', current_url)
                if match:
                    current_page = int(match.group(1))
                    next_page = current_page + 1
                    next_url = re.sub(r'page=\d+', f'page={next_page}', current_url)

                    # Before navigating, check if we're already on the last page
                    if self._is_last_page():
                        print(f"Detected last page (page {current_page}). No more results.")
                        return False

                    # Navigate to the next page
                    print(f"Navigating directly to: {next_url}")
                    self.driver.get(next_url)

                    # Wait for the page to load
                    time.sleep(5)

                    # Verify page changed successfully
                    if self._verify_page_change(current_page, next_page):
                        print(f"✓ Successfully navigated to page {next_page}")
                        return True
                    else:
                        print(f"× Failed to navigate to page {next_page}")
                        return False
                return page
            else:
                # If URL doesn't contain page parameter, try to find pagination container
                print("URL doesn't contain page parameter, looking for pagination controls...")

                # Try to find the Next button and get the URL from its href
                try:
                    # Save a screenshot for debugging
                    self.driver.save_screenshot("pagination_debug.png")
                    print("Screenshot saved as pagination_debug.png")

                    # Try alternative next page methods
                    if self._try_click_next_button():
                        print("✓ Successfully navigated using button click")
                        return True

                    # If all else fails, try to append page=2 to the URL
                    if "?" in current_url:
                        next_url = current_url + "&page=2"
                    else:
                        next_url = current_url + "?page=2"

                    print(f"Trying first page URL: {next_url}")
                    self.driver.get(next_url)
                    time.sleep(5)

                    # Check if the URL change was successful
                    if "page=2" in self.driver.current_url:
                        print("✓ Successfully navigated to page 2")
                        return True
                    else:
                        print("× Failed to navigate to page 2")
                        return False
                except Exception as e:
                    print(f"Error finding alternative pagination: {str(e)}")
                    return False

        except Exception as e:
            print(f"Error in go_to_next_page: {str(e)}")
            self.driver.save_screenshot("error_next_page.png")
            return False

    def _is_last_page(self):
        """Determine if we're on the last page based on multiple indicators"""
        try:
            # Method 1: Check if the Next button is disabled
            next_buttons = self.driver.find_elements(By.XPATH,
                                                     "//button[contains(@class, 'next') or contains(@aria-label, 'Next')]")

            for button in next_buttons:
                if button.get_attribute("disabled") == "true" or "disabled" in button.get_attribute("class"):
                    print("Next button is disabled")
                    return True

            # Method 2: Check for "end of results" message
            end_messages = [
                "//p[contains(text(), 'end of results')]",
                "//div[contains(text(), 'end of results')]",
                "//span[contains(text(), 'end of results')]",
                "//p[contains(text(), 'No more results')]",
                "//div[contains(text(), 'No more results')]"
            ]

            for message in end_messages:
                if self.driver.find_elements(By.XPATH, message):
                    print("Found 'end of results' message")
                    return True

            # Method 3: Count search results and check if fewer than expected
            try:
                results = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'search-result')]")
                print(f"Found {len(results)} results on this page")

                # If less than typical full page (usually 10 or 25), might be last page
                if 0 < len(results) < 5:  # Adjust threshold as needed
                    print("Found fewer results than normal, likely last page")
                    return True
            except:
                pass

            # Method 4: Check HTML source for indicators
            page_source = self.driver.page_source.lower()
            last_page_indicators = [
                "end of results",
                "no more results",
                "last page",
                "final page"
            ]

            for indicator in last_page_indicators:
                if indicator in page_source:
                    print(f"Found '{indicator}' in page source")
                    return True

            # Not the last page
            return False

        except Exception as e:
            print(f"Error in _is_last_page: {str(e)}")
            # If we're unsure, assume it's not the last page and try anyway
            return False

    def _verify_page_change(self, previous_page, expected_page):
        """Verify that page change was successful"""
        try:
            # Method 1: Check URL contains expected page number
            current_url = self.driver.current_url
            if f"page={expected_page}" in current_url:
                print(f"URL confirms successful page change to page {expected_page}")
                return True

            # Method 2: Look for page indicator in the UI
            try:
                page_indicators = self.driver.find_elements(By.XPATH,
                                                            f"//button[contains(@class, 'selected') or contains(@class, 'active') or contains(@aria-current, 'true')]")

                for indicator in page_indicators:
                    if indicator.text.strip() == str(expected_page):
                        print(f"UI pagination indicates we're on page {expected_page}")
                        return True
            except:
                pass

            # Method 3: Check if content has changed by comparing page source hash
            if hasattr(self, 'previous_page_hash'):
                import hashlib
                current_hash = hashlib.md5(self.driver.page_source.encode()).hexdigest()
                if current_hash != self.previous_page_hash:
                    print("Page content has changed (hash check)")
                    self.previous_page_hash = current_hash
                    return True
                else:
                    print("Page content hasn't changed (same hash)")
                    return False
            else:
                # First run, store the hash
                import hashlib
                self.previous_page_hash = hashlib.md5(self.driver.page_source.encode()).hexdigest()
                return True

            return False

        except Exception as e:
            print(f"Error in _verify_page_change: {str(e)}")
            return False

    def _try_click_next_button(self):
        """Attempt to find and click the next button"""
        try:
            # Try multiple selectors to find the next button
            selectors = [
                "//button[contains(@aria-label, 'Next')]",
                "//button[contains(@class, 'next')]",
                "//button[.//span[text()='Next']]",
                "//a[contains(@class, 'next')]"
            ]

            for selector in selectors:
                buttons = self.driver.find_elements(By.XPATH, selector)
                if buttons:
                    print(f"Found {len(buttons)} potential Next buttons")
                    for button in buttons:
                        try:
                            # Try to click it
                            print("Attempting to click button...")
                            button.click()
                            time.sleep(3)

                            # Check if URL changed
                            if "page=" in self.driver.current_url:
                                print("✓ Button click successful")
                                return True
                        except:
                            # Try JavaScript click
                            try:
                                self.driver.execute_script("arguments[0].click();", button)
                                time.sleep(3)
                                if "page=" in self.driver.current_url:
                                    print("✓ JavaScript click successful")
                                    return True
                            except Exception as e:
                                print(f"Click failed: {str(e)}")

            return False
        except Exception as e:
            print(f"Error in _try_click_next_button: {str(e)}")
            return False

    def _verify_page_changed(self):
        """Verify the page has changed after clicking Next"""
        try:
            # Option 1: Look for content loading indicators
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'search-results__list')]"))
            )

            # Option 2: Check if URL parameters changed (if applicable)
            # current_url = self.driver.current_url
            # if "page=" in current_url:
            #     print(f"URL confirms page change: {current_url}")

            # Option 3: Wait for skeleton loaders to disappear (if LinkedIn uses them)
            try:
                WebDriverWait(self.driver, 5).until_not(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'skeleton')]"))
                )
            except:
                pass  # It's okay if there are no skeleton loaders

            return True
        except Exception as e:
            print(f"Page verification failed: {str(e)}")
            return False
    
    def save_results_to_excel(self, role):
        """Save scraped results to an Excel file with role and current datetime"""
        try:
            from datetime import datetime
            
            # Format current date and time
            current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Clean the role name for filename (remove special characters)
            clean_role = ''.join(c if c.isalnum() or c in [' ', '_'] else '_' for c in role)
            clean_role = clean_role.replace(' ', '_')
            
            # Create filename with role and datetime
            output_filename = f"linkedin_{clean_role}_{current_datetime}.xlsx"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Save to Excel
            self.save_to_mongodb(self.results)
            print(f"Saving results to {output_path}")
            df = pd.DataFrame(self.results)
            df.to_excel(output_path, index=False)
            print(f"Results saved to {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def run(self):
        """Run the complete LinkedIn scraping process"""
        try:
            # Read credentials and role from Excel
            # print(f"{load_dotenv().get('USERNAME')}")
            username, password = os.getenv('USERNAME'), os.getenv('PASSWORD')
            print(f"Using credentials: {username}")
            if not username or not password:
                print("Username or password not found in environment variables. Exiting...")
                return
            role = self.read_excel()
            print(f"Loaded credentials for {username} and searching for role: {role}")
            
            # Login to LinkedIn
            if not self.login(username, password):
                print("Login failed. Exiting...")
                self.driver.quit()
                return
            
            # Search for the role and apply people filter
            if not self.search_role(role):
                print("Search failed. Exiting...")
                self.driver.quit()
                return
            
            page_num = 1
            has_next_page = True
            
            while has_next_page:
                print(f"Scraping page {page_num}")
                
                # Scrape profiles on current page
                page_results = self.scrape_profiles_on_page()
                self.results.extend(page_results)
                
                # Try to go to next page
                has_next_page = self.go_to_next_page()
                #remove these lines in production
                if page_num < 5:
                    page_num += 1
                else:
                    break
            
            print(f"Total profiles scraped: {len(self.results)}")
            
            # Save results to Excel with role and datetime in filename
            self.save_results_to_excel(role)
            
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close the browser
            self.driver.quit()

    def linkedin_scraping_dog(self, profile_id):
         api_key = "682fb90d765368e823493cca"
         api_key = "682fb90d765368e823493cca"

         url = "https://api.scrapingdog.com/linkedin"
  
         params = {
            "api_key": api_key,
            "type": "profile",
            "linkId": profile_id,
            "private": "false"
            }
        
         response = requests.get(url, params=params)
  
         if response.status_code == 200:
            data = response.json()
            return data
         else:
            return f"Request failed with status code: {response.status_code}"


    
    def save_to_mongodb(self, data):
        DB_NAME = "flexon"
        COLLECTION_NAME = "jobApplicants"
        MONGO_URI = "mongodb://botguru-ru:51DLgWA0VsStrA6jcwIhjMwG9ENNZEdgmbgSgu5qeP5ufQaecfykdWr87ZwqPbs5w8prv1YmfDONACDbTz7f3A%3D%3D@botguru-ru.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@botguru-ru@"
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        if isinstance(data, list):
            if data:
                result = collection.insert_many(data)
                print(f"Inserted {len(result.inserted_ids)} documents into MongoDB.")
            else:
                print("No data to insert into MongoDB.")
        else:
            result = collection.insert_one(data)
            print(f"Data inserted with ID: {result.inserted_id}")
    
       

if __name__ == "__main__":
    # Define the specific Excel file path
    excel_path = r"C:\Users\navee\OneDrive\Desktop\LinkedinScrap\linkedin_data.xlsx"
    print(f"Using Excel file at: {excel_path}")
    
    # Check if file exists at the specified location
    if not os.path.exists(excel_path):
        # Create sample Excel file if it doesn't exist
        print(f"File not found at {excel_path}. Creating sample Excel file...")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)
        
        # Create sample file
        sample_data = {
            'username': ['your_email@example.com'],
            'password': ['your_password'],
            'role': ['Software Engineer']
        }
        pd.DataFrame(sample_data).to_excel(excel_path, index=False)
        print(f"Sample file created at {excel_path}")
        print("Please update the file with your actual credentials and desired role before running again.")
        exit(0)
    
    # Run the scraper with the specified Excel path
    scraper = LinkedInScraper(excel_path)
    scraper.run()