from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from dotenv import load_dotenv
import os

load_dotenv()

class WebScraper:
    def __init__(self):
        """
        Initialize Chrome WebDriver with options.
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(30)

    def search_and_extract_case(self, case_type_input, case_no_input, case_year_input):
        """
        Search for a court case and extract the data.
        """
        self.driver.get(os.getenv('WEBSITE_LINK'))

        try:
            # Locate elements
            case_type = self.driver.find_element(By.XPATH, '//select[contains(@id , "case_type") or contains(@name , "case_type")]')
            year_element = self.driver.find_element(By.XPATH, '//select[contains(@id , "year")]')
            case_no_element = self.driver.find_element(By.XPATH, '//input[@type="text" and (contains(@id , "case") or contains(@id , "number"))]')
            captcha_code = self.driver.find_element(By.XPATH, '//span[contains(@id ,"code" ) or contains(@id , "captcha")]')
            captcha_field = self.driver.find_element(By.XPATH, '//input[@type="text" and contains(@id , "captcha")]')
            submit_button = self.driver.find_element(By.XPATH, '//button[@id="search" or @id="submit" or contains(text() , "Submit")]')

            # Select values
            Select(case_type).select_by_visible_text(case_type_input)
            Select(year_element).select_by_visible_text(case_year_input)
            case_no_element.send_keys(case_no_input)

            code = captcha_code.text.strip()
            captcha_field.send_keys(code)

            time.sleep(2)
            submit_button.click()
            time.sleep(10)

            rows = self.driver.find_elements(By.CSS_SELECTOR, '#caseTable tbody tr')
            if len(rows) == 1 and "No data available in table" in rows[0].text:
                print("No records found for the given search criteria")
                return [{
                    'case_title': "NA",
                    'status': "NA",
                    'petitioner': "NA",
                    'respondent': "NA",
                    'next_date': "NA",
                    'last_date': "NA",
                    'court_no': "NA",
                    'order_link': "NA"
                }]

            data = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if len(cols) < 4:
                    continue

                s_no = cols[0].text.strip()
                case_info_raw = cols[1]
                try:
                    case_text = case_info_raw.find_element(By.TAG_NAME, 'a').text.strip()
                except:
                    case_text = ""

                try:
                    status = case_info_raw.find_element(By.TAG_NAME, 'font').text.strip().replace('[', '').replace(']', '')
                except:
                    status = ""

                try:
                    order_link = case_info_raw.find_element(By.TAG_NAME, 'strong').find_element(By.XPATH, '..').get_attribute('href')
                except:
                    order_link = None

                parties = cols[2].get_attribute('innerText').replace('\xa0', ' ').strip()
                parts = ' '.join(parties.split()).split('VS.')
                petitioner = parts[0].strip()
                respondent = parts[1].strip() if len(parts) > 1 else None

                listing_text = cols[3].get_attribute('innerText').strip().split('\n')
                next_date = last_date = court_no = ""
                for line in listing_text:
                    if "NEXT DATE:" in line:
                        next_date = line.replace("NEXT DATE:", "").strip()
                    elif "Last Date:" in line:
                        last_date = line.replace("Last Date:", "").strip()
                    elif "COURT NO:" in line:
                        court_no = line.replace("COURT NO:", "").strip()

                data.append({
                    'case_title': case_text,
                    'status': status,
                    'petitioner': petitioner,
                    'respondent': respondent,
                    'next_date': next_date if next_date != 'NA' else None,
                    'last_date': last_date,
                    'court_no': court_no,
                    'order_link': order_link
                })

            return data

        except Exception as e:
            print(f"Error occurred: {e}")
            return []
        
    def get_order_data(self , order_link):
        """
            get orders data if available
        """
        self.driver.get(order_link)
        time.sleep(5)
        try:
            table_body = self.driver.find_element(By.TAG_NAME , "tbody")
            rows = table_body.find_elements(By.TAG_NAME , "tr")
            data =  []

            for row in rows:
                row_data = row.find_elements(By.TAG_NAME , "td")
                # sr.no
                sr_no = row_data[0].text
                # order link
                a_tag = row_data[1].find_elements(By.TAG_NAME , "a")
                if a_tag:
                    order_link = a_tag[0].get_attribute("href")
                else:
                    order_link = None
                # order date
                order_date = row_data[2].text
                # corrigendum link
                a_tag = row_data[3].find_elements(By.TAG_NAME , "a")
                if a_tag:
                    corrigendum_link = a_tag[0].get_attribute("href")
                else:
                    corrigendum_link = None
                # hindi order
                a_tag = row_data[4].find_elements(By.TAG_NAME , "a")
                if a_tag:
                    hindi_order = a_tag[0].get_attribute("href")
                else:
                    hindi_order = None
                data.append({
                    "sr_no":int(sr_no),
                    "order_link":order_link,
                    "order_date":order_date,
                    "corrigendum_link":corrigendum_link,
                    "hindi_order":hindi_order,
                })
            return data
        except Exception as e:
            print(e)
            return []

    def search_multiple_cases(self, cases_list):
        """
        Search for multiple cases.
        """
        all_results = {}

        for i, case in enumerate(cases_list):
            print(f"Searching case {i+1}/{len(cases_list)}: {case}")
            case_key = f"{case['case_type']} - {case['case_number']}/{case['case_year']}"
            result = self.search_and_extract_case(
                case['case_type'],
                case['case_number'],
                case['case_year']
            )
            all_results[case_key] = result

            if i < len(cases_list) - 1:
                time.sleep(3)

        return all_results

    def close(self):
        """
        Close the WebDriver session.
        """
        self.driver.quit()
