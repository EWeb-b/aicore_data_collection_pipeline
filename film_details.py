import re
import uuid
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver

class FilmDetails:

    def __init__(self) -> None:
        self.uuid = None
        self.friend_id = None
        self.title = None
        self.rating = None
        self.metascore = None
        self.release_date = None
        self.runtime = None
        self.actors = []
        self.directors = []
        self.genres = []
        self.summary_img = None

    def get_all_data(self, driver: webdriver) -> dict:
        self.uuid = str(uuid.uuid4())
        self.friend_id = driver.current_url.split("/")[-1]
        self.title = self.ret_ele_if_exist(driver, '//div[@class="product_page_title oswald"]/h1')
        self.rating = self.ret_ele_if_exist(driver, '//div[@class="rating"]/span[2]')
        try:
            self.metascore = int(self.ret_ele_if_exist(driver, '//a[@class="metascore_anchor"]/span'))
        except:
            self.metascore = 0

        try:
            self.release_date = datetime.strptime(self.ret_ele_if_exist(driver, '//span[@class="release_date"]/span[2]'), '%B %d, %Y').date()
        except:
            self.release_date = None

        try:
            self.runtime = int(re.sub("[^0-9]", "", self.ret_ele_if_exist(driver, '//div[@class="runtime"]/span[2]')))
        except:
            self.runtime = 0

        self.actors = self.return_elements_if_exist(driver, '//div[@class="summary_cast details_section"]/span[2]/a')
        self.directors = self.return_elements_if_exist(driver, '//div[@class="director"]/a')
        self.genres = self.return_elements_if_exist(driver, '//div[@class="genres"]/span[2]/span')

        try:
            self.summary_img = driver.find_element(By.XPATH, value='//img[@class="summary_img"]').get_attribute("src")
        except:
            self.summary_img = None

    def ret_ele_if_exist(self, driver, xpath: str) -> (WebElement | None):
        try:
            ele = driver.find_element(By.XPATH, value=xpath).text
        except:
            return None
        return ele

    def return_elements_if_exist(self, driver, xpath: str) -> (list | None):
        try:
            eles = driver.find_elements(By.XPATH, value=xpath)
            ele_list = [ele.text for ele in eles]
        except NoSuchElementException:
            return None
        return ele_list