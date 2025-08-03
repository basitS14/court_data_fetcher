from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.options import Options


# Set up Chrome options
options = Options()
options.add_argument('--headless')  # Run in headless mode
options.add_argument('--disable-gpu')  # Optional: helps in Windows
options.add_argument('--no-sandbox')  # Optional: for Linux
options.add_argument('--window-size=1920,1080')  # Optional: for full rendering

def search_and_extract_case(case_type_input, case_no_input, case_year_input):
    """
    Search for a court case and extract the data
    
    Args:
        case_type_input: Case type (e.g., "W.P.(CRL)")
        case_no_input: Case number (e.g., "985")
        case_year_input: Case year (e.g., "2024")
    
    Returns:
        List of dictionaries containing case data
    """
    
    # Initialize driver
    driver = webdriver.Chrome(options=options)
    driver.get('https://delhihighcourt.nic.in/app/get-case-type-status')  
    driver.implicitly_wait(30)

    try:
        # Find elements
        # case_type = driver.find_element(By.ID, 'case_type')  
        # year_element = driver.find_element(By.ID, 'case_year')
        # case_no_element = driver.find_element(By.ID, 'case_number')
        # captcha_code = driver.find_element(By.ID, 'captcha-code')
        # captcha_field = driver.find_element(By.ID, 'captchaInput')
        # submit_button = driver.find_element(By.ID, 'search')

        # used XPath for robusteness against website layout change
        case_type = driver.find_element(By.XPATH, '//select[contains(@id , "case_type") or contains(@name , "case_type")  ]')  
        year_element = driver.find_element(By.XPATH, '//select[contains(@id , "year")]')
        case_no_element = driver.find_element(By.XPATH, '//input[@type="text" and contains(@id , "case") or contains(@id , "number")]')
        captcha_code = driver.find_element(By.XPATH, '//span[contains(@id ,"code" ) or contains(@id , "captcha")]')
        captcha_field = driver.find_element(By.XPATH, '//input[@type="text" and contains(@id , "captcha")]')
        submit_button = driver.find_element(By.XPATH, '//button[@id="search" or @id="submit" or contains(text() , "Submit")]')

        # Select elements
        select_case = Select(case_type)
        select_year = Select(year_element)

        # Performing select operations
        select_case.select_by_visible_text(case_type_input)
        select_year.select_by_visible_text(case_year_input)

        # Getting captcha code
        code = captcha_code.text

        # Performing typing
        case_no_element.send_keys(case_no_input)
        captcha_field.send_keys(code)

        time.sleep(2)
        # Submit button
        submit_button.click()

        # Wait for results
        time.sleep(10)
        
        # Locate the table body rows
        rows = driver.find_elements(By.CSS_SELECTOR, '#caseTable tbody tr')

        # Check if no data available
        if len(rows) == 1:
            first_row_text = rows[0].text.strip()
            if "No data available in table" in first_row_text:
                print("No records found for the given search criteria")
                return []

        # Extract data
        data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, 'td')
            
            # Skip if not enough columns or contains "no data" message
            if len(cols) < 4:
                continue
                
            # Check if it's a "no data" row
            if len(cols) == 1 and "No data available" in cols[0].text:
                continue


            # Case Info (extract status and main text separately)
            case_info_raw = cols[1]
            
            try:
                case_text = case_info_raw.find_element(By.TAG_NAME, 'a').text.strip()
            except:
                case_text = ""
                
            try:
                status = case_info_raw.find_element(By.TAG_NAME, 'font').text.strip()
                status = status.replace('[', '').replace(']', '')  # Remove brackets
            except:
                status = ""

            try:
                order_link = case_info_raw.find_element(By.TAG_NAME, 'strong').find_element(By.XPATH, '..').get_attribute('href')
            except:
                order_link = None

            # Petitioner vs Respondent
            parties = cols[2].get_attribute('innerText').replace('\xa0', ' ').strip()
            cleaned = ' '.join(parties.split())
            parts = cleaned.split('VS.')
            petitioner = parts[0].strip()
            respondent = parts[1].strip() if len(parts) > 1 else None


            # Listing info
            listing_text = cols[3].get_attribute('innerText').strip().split('\n')
            
            next_date = ""
            last_date = ""
            court_no = ""
            
            for line in listing_text:
                if "NEXT DATE:" in line:
                    next_date = line.replace("NEXT DATE:", "").strip()
                elif "Last Date:" in line:
                    last_date = line.replace("Last Date:", "").strip()
                elif "COURT NO:" in line:
                    court_no = line.replace("COURT NO:", "").strip()

            # Add to list
            data.append({
                'Case': case_text,
                'Status': status,
                'Petitioner': petitioner,
                'Respondent':respondent,
                'Petitioner vs Respondent': parties,
                'Next Date': next_date if next_date != 'NA' else None,
                'Last Date': last_date,
                'Court No.': court_no,
                'Order Link': order_link
            })

        return data
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return []
        
    finally:
        # Close driver
        driver.quit()

def search_multiple_cases(cases_list):
    """
    Search for multiple cases
    
    Args:
        cases_list: List of dictionaries with keys: case_type, case_number, case_year
    
    Returns:
        Dictionary with results for each case
    """
    all_results = {}
    
    for i, case in enumerate(cases_list):
        print(f"Searching case {i+1}/{len(cases_list)}: {case}")
        
        case_key = f"{case['case_type']} - {case['case_number']}/{case['case_year']}"
        result = search_and_extract_case(
            case['case_type'], 
            case['case_number'], 
            case['case_year']
        )
        
        all_results[case_key] = result
        
        # Add delay between searches
        if i < len(cases_list) - 1:
            time.sleep(3)
    
    return all_results

# Example usage
if __name__ == "__main__":
    # Single case search
    # print("=== SINGLE CASE SEARCH ===")
    # case_type_input = "W.P.(CRL)"
    # case_no_input = "985"
    # case_year_input = "2024"
    
    # result = search_and_extract_case(case_type_input, case_no_input, case_year_input)
    
    # if result:
    #     print(f"Found {len(result)} case(s):")
    #     for item in result:
    #         print("\n--- Case Details ---")
    #         for key, value in item.items():
    #             print(f"{key}: {value}")
    # else:
    #     print("No cases found or error occurred")
    
    # Multiple cases search example
    print("\n=== MULTIPLE CASES SEARCH ===")
    cases_to_search = [
        {"case_type": "W.P.(CRL)", "case_number": "985", "case_year": "2024"},
        {"case_type": "W.P.(CRL)", "case_number": "986", "case_year": "2024"}
    ]
    
    # Uncomment to test multiple cases
    multiple_results = search_multiple_cases(cases_to_search)
    
    for case_key, cases in multiple_results.items():
        print(f"\n=== {case_key} ===")
        if cases:
            for case in cases:
                print(case)
        else:
            print("No records found")