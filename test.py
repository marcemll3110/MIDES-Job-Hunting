import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
# Ensure the ChromeDriver executable is in the correct path
# Adjust the path to the ChromeDriver executable as needed
# For Windows, it might be 'chromedriver.exe'
# For macOS/Linux, it might be '/path/to/chromedriver'
# Make sure to replace the path with the actual location of your ChromeDriver executable

path = os.path.dirname(os.path.abspath(__file__))
print(path)

# Determine the correct ChromeDriver executable based on the OS
if os.name == 'nt':  # Windows
    executable_path = os.path.join(path, 'chromedriver.exe')
else:  # macOS/Linux
    executable_path = os.path.join(path, 'chromedriver')

service = Service(executable_path=executable_path)
driver = webdriver.Chrome(service=service)

driver.get('https://www.buscojobs.com.uy')

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, 'que'))  # Wait until the search box is present
)

input_element = driver.find_element(By.ID, 'que')  # Find the search box using class name
input_element.clear()
input_element.send_keys('Carpintero' + Keys.ENTER)  # Type the search query
time.sleep(3)  # Wait for 10 seconds to see the page

job_cards = driver.find_elements(By.CLASS_NAME, 'ListadoOfertas_containerLink__NlwJU')  # Find all job cards
print(f"Found {len(job_cards)} job cards.")
for card in job_cards:
    print(card.get_attribute("aria-label"))  # Print the text of each job card
    print(card.get_attribute("href"))  # Print the link of each job card




driver.quit()  # Close the browser
print("Test completed successfully.")

