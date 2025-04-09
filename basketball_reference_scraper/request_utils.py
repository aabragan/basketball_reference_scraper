from time import sleep, time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from requests import get
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
last_request = time()


# def get_selenium_wrapper(url, xpath):
#     global last_request
#     # Verify last request was 3 seconds ago
#     if 0 < time() - last_request < 3:
#         sleep(3)
#     last_request = time()
#     try:
#         driver.get(url)
#         element = driver.find_element(By.XPATH, xpath)
#         return f'<table>{element.get_attribute("innerHTML")}</table>'
#     except:
#         print("Error obtaining data table.")
#         return None


# def get_wrapper(url):
#     global last_request
#     # Verify last request was 3 seconds ago
#     if 0 < time() - last_request < 3:
#         sleep(3)
#     last_request = time()
#     r = get(url)
#     while True:
#         if r.status_code == 200:
#             content = r.content
#             return BeautifulSoup(content, "html.parser")
#         elif r.status_code == 429:
#             retry_time = int(r.headers["Retry-After"])
#             print(f"Retrying after {retry_time} sec...")
#             sleep(retry_time)
#         else:
#             content = r.content
#             return BeautifulSoup(content, "html.parser")


def get_wrapper(url: str) -> BeautifulSoup:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        soup = BeautifulSoup(page.content(), "html.parser")
        browser.close()
        return soup


# def get_wrapper(url):
#     global last_request
#     # Verify last request was 3 seconds ago
#     if 0 < time() - last_request < 3:
#         sleep(3)
#     last_request = time()
#     with sync_playwright() as p:
#         browser = p.firefox.launch()
#         page = browser.new_page()
#         page.goto(url)
#         soup = BeautifulSoup(page.content(), "html.parser")
#         browser.close()

#     while True:
#         if r.status_code == 200:
#             return r
#         elif r.status_code == 429:
#             retry_time = int(r.headers["Retry-After"])
#             print(f"Retrying after {retry_time} sec...")
#             sleep(retry_time)
#         else:
#             return r
