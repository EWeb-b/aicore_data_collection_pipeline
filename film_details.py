import re
import uuid
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


def return_element_if_exists(driver, xpath: str) -> (WebElement | None):
    try:
        ele = driver.find_element(By.XPATH, value=xpath)
    except NoSuchElementException:
        return None
    return ele

def return_elements_if_exist(driver, xpath: str) -> (list | None):
    try:
        eles = driver.find_elements(By.XPATH, value=xpath)
        ele_list = [ele.text for ele in eles]
    except NoSuchElementException:
        return None
    return ele_list

def get_uuid() -> str:
    """Creates a unique identifier.

    Returns:
        A unique identifier (string).
    """
    return str(uuid.uuid4())

def get_friend_id(driver) -> str:
        """Creates and returns a 'friendly id' by using the last part of the URL.

        Returns:
            The piece of the current page's url which comes after the last / character (string).
        """
        return driver.current_url.split("/")[-1]

def get_film_title(driver) -> (str | None):
    """Finds and returns the current film's title as a string."""
    xpath = '//div[@class="product_page_title oswald"]/h1'
    result = return_element_if_exists(driver, xpath)
    ret = result.text if result else result
    return ret

def get_metascore(driver) -> (str | None):
    """Finds and returns the current film's metascore as a string."""
    xpath = '//a[@class="metascore_anchor"]/span'
    result = return_element_if_exists(driver, xpath)
    ret = int(result.text) if result else 0
    return ret

def get_release_date(driver) -> (str | None):
    """Finds and returns the current film's release date as a string."""
    xpath = '//span[@class="release_date"]/span[2]'
    result = return_element_if_exists(driver, xpath)
    try:
        release_date = datetime.strptime(
            result.text, '%B %d, %Y').date() if result else result
    except ValueError:
        release_date = None
    except:
        release_date = None
    return release_date

def get_actors(driver) -> (list | None):
    """Finds and returns the current film's starring actors as a List."""
    xpath = '//div[@class="summary_cast details_section"]/span[2]/a'
    return return_elements_if_exist(driver, xpath)

def get_directors(driver) -> (list | None):
    """Finds and returns the current film's directors as a List."""
    xpath = '//div[@class="director"]/a'
    return return_elements_if_exist(driver, xpath)

def get_genres(driver) -> (list | None):
    """Finds and returns the current film's genres as a List"""
    xpath = '//div[@class="genres"]/span[2]/span'
    return return_elements_if_exist(driver, xpath)

def get_rating(driver) -> (str | None):
    """Finds and returns the current film's ae rating as a string."""
    xpath = '//div[@class="rating"]/span[2]'
    result = return_element_if_exists(driver, xpath)
    ret = result.text if result else result
    return ret

def get_runtime(driver) -> (str | None):
    """Finds and returns the current film's runtime as a string."""
    xpath = '//div[@class="runtime"]/span[2]'
    result = return_element_if_exists(driver, xpath)
    try:
        runtime = int(re.sub("[^0-9]", "", result.text)
                        ) if result else 0
    except:
        runtime = 0
    return runtime

def get_summary_img(driver) -> (str | None):
    """Finds and returns the current film's summary image source as a string."""
    xpath = '//img[@class="summary_img"]'
    result = return_element_if_exists(driver, xpath)
    ret = result.get_attribute("src") if result else result
    return ret