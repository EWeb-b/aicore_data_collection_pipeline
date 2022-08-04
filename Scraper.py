from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import uuid
import os
import json
import requests



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

    def get_image_src(self):
        img_src = self.driver.find_element(By.XPATH, value = '//img[@class="summary_img"]').get_attribute("src")
        return img_src

    def get_film_data(self):
        data = {'uuid':[],'friend_id':[],'title':[],'metascore':[],'release_date':[],'starring':[],
                'director':[],'genres':[],'rating':[],'runtime':[],'images':[]}

        data['uuid'] = str(uuid.uuid4())
        data['friend_id'] = self.driver.current_url.split("/")[-1]

        data['title'] = self.driver.find_element(By.XPATH, value = '//div[@class="product_page_title oswald"]/h1').text
        data['metascore'] = self.driver.find_element(By.XPATH, value = '//a[@class="metascore_anchor"]/span').text
        data['release_date'] = self.driver.find_element(By.XPATH, value = '//span[@class="release_date"]/span[2]').text

        actors = self.driver.find_elements(By.XPATH, value = '//div[@class="summary_cast details_section"]/span[2]/a')
        data['starring'] = [actor.text for actor in actors]

        directors = self.driver.find_elements(By.XPATH, value = '//div[@class="director"]/a')
        data['director'] = [director.text for director in directors]

        genres = self.driver.find_elements(By.XPATH, value = '//div[@class="genres"]/span[2]/span')
        data['genres'] = [genre.text for genre in genres]

        data['rating'] = self.driver.find_element(By.XPATH, value = '//div[@class="rating"]/span[2]').text
        data['runtime'] = self.driver.find_element(By.XPATH, value = '//div[@class="runtime"]/span[2]').text

        data['images'] = self.get_image_src()

        return data

    def save_raw_data(self, data): #TODO use try, except block

        if os.path.isdir('raw_data'):
            filename = "raw_data/" + data['friend_id'] + ".json"
            print(filename)
            with open(filename, "w") as file:
                file.write(json.dumps(data))

        else:
            self.create_data_folder( data)

    def create_data_folder(self, data):

        if not os.path.isdir('raw_data'):
            os.makedirs('raw_data')
            self.save_raw_data(data)

    def save_image(data):

        for x, image in enumerate(data['images']):
            filename = "raw_data/images/{}_{}.jpg".format(data['friend_id'], str(x))
            img_data = requests.get(image).content
            with open(filename, 'wb') as handler:
                handler.write(img_data)

        


if __name__ == "__main__":

    myScraper = Scraper(URL)
    print(myScraper)
    time.sleep(5)
    myScraper.decline_cookies()
    filmLinks = myScraper.get_film_links()
    print (filmLinks)





    