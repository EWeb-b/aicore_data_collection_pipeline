from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time



URL = "https://www.metacritic.com/browse/movies/score/metascore/year/filtered"
DELAY = 10

class Scraper:

    def __init__(self, url):
        self.url = url
        self.driver = webdriver.Chrome()
        self.driver.get(url)

    #TODO: change this to take an argument for vertical position and scroll to there instead.
    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def decline_cookies(self):
        try: # if the reject cookies button is there then click it
            reject_cookies_btn = WebDriverWait(self.driver, DELAY).until(EC.presence_of_element_located((By.XPATH, '//*[@id="onetrust-reject-all-handler"]')))
            reject_cookies_btn.click()

        except NoSuchElementException: # open the cookies settings, then click reject
            cookies_settings_btn = self.driver.find_element(by=By.XPATH, value='//*[@id="ot-sdk-btn"]')
            cookies_settings_btn.click()
            reject_cookies_btn = WebDriverWait(self.driver, DELAY).until(EC.presence_of_element_located((By.XPATH, '//*[@id="onetrust-pc-sdk"]/div[3]/div[1]/button[1]')))
            reject_cookies_btn.click()

        except TimeoutException:
            print ("Loading cookies took too much time!")

        except:
            pass

    def get_film_links(self):
        films = self.driver.find_elements(By.XPATH, '//div[@class="title_bump"]//a[@class="title"]')
        links = [film.get_attribute('href') for film in films]
        return links


if __name__ == "__main__":

    myScraper = Scraper(URL)
    print(myScraper)
    time.sleep(5)
    myScraper.decline_cookies()
    filmLinks = myScraper.get_film_links()
    print (filmLinks)

#TODO: change to be like notebook aicore version



    