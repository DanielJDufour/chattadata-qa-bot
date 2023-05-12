import csv
from time import sleep

import requests

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


url = "https://www.chattadata.org/browse"

fieldnames = ["status_code", "dataset_url", "external_link"]
with open("results.csv", "w") as f:
  csv.DictWriter(f, fieldnames=fieldnames).writeheader()

print("[chattadata-qa-bot] starting to scrape")
browser = webdriver.Firefox()
print("[chattadata-qa-bot] started web browser")

browser.get(url)
print(f"[chattadata-qa-bot] opened {url}")

browser.find_element(By.XPATH, "//a[@title='External Datasets']").click()
print(f"[chattadata-qa-bot] clicked filter")

first_page = True
next_url = None

while first_page or next_url:

  if first_page is False:
    browser.get(next_url)
    print("[chattadata-qa-bot] sleeping 10 seconds to let new page load")
    sleep(10)


  for element in browser.find_elements(By.CLASS_NAME, "browse2-result-name-link"):
    print("[chattadata-qa-bot] sleeping 5 seconds")
    sleep(5)
    
    dataset_url = element.get_attribute("href")
    print(f'[chattadata-qa-bot] dataset_url: "{dataset_url}"')

    # scroll link into view
    browser.execute_script("arguments[0].scrollIntoView();", element)
    print("[chattadata-qa-bot] sleeping 1 second")
    sleep(1)

    # command click to open dataset in a new tab
    ActionChains(browser) \
      .key_down(Keys.COMMAND) \
      .click(element) \
      .key_up(Keys.COMMAND) \
      .perform()

    browser.switch_to.window(browser.window_handles[-1])

    print("[chattadata-qa-bot] sleeping 10 seconds to let new page load")
    sleep(10)

    section = browser.find_element(By.CLASS_NAME, "dataset-download-section")
    print("[chattadata-qa-bot] dataset download section:", section)

    error_count = 0

    if section:
      for a in section.find_elements(By.TAG_NAME, "a"):
        # open external link in new tab
        external_link = a.get_attribute("href")
    
        print(f'[chattadata-qa-bot] requesting "{external_link}"')
        response = None
        try:
          response = requests.get(external_link)
        except Exception as e:
          print(f'[chattadata-qa-bot] failed to connect to "{external_link}"')
          with open("results.csv", "a") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writerow({
              "dataset_url": dataset_url,
              "external_link": external_link,
              "status_code": "none"
            })
          # break on first broken link
          break

        status_code = response.status_code
        print(f'[chattadata-qa-bot] status: {status_code}')

        if status_code >= 400:
          print(f'[chattadata-qa-bot] request to "{external_link}" returned an error')
          error_count += 1
          with open("results.csv", "a") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writerow({
              "dataset_url": dataset_url,
              "external_link": external_link,
              "status_code": status_code
            })
            print("[chattadata-qa-bot] saved to results.csv")
            # break on first broken link
            break

    if error_count == 0:
      print(f'[chattadata-qa-bot] no errors found on page "{dataset_url}"')

    # close tab for current dataset
    browser.close()

    # switch back to first window
    browser.switch_to.window(browser.window_handles[0])

  first_page = False

  try:
    next_page = browser.find_element(By.CSS_SELECTOR, ".pageLink.active + .pageLink")
    print(f'[chattadata-qa-bot] next_page:', next_page)

    next_url = next_page.get_attribute("href") if next_page else None
    print(f'[chattadata-qa-bot] set next_url to "{next_url}"')
  except Exception as e:
    print(f'[chattadata-qa-bot] reached the end')
    break


sleep(5)
browser.quit()
print("[chattadata-qa-bot] closed web browser")

print("[chattadata-qa-bot] finished")
