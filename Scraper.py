from xxlimited import Str
import boto3
import configparser
from datetime import datetime
import json
import os
import re
import requests
import time
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from sqlalchemy import create_engine
from typing import List
from webdriver_manager.chrome import ChromeDriverManager


class Scraper:

    def __init__(self, headless=False) -> None:
        self.url = "https://www.metacritic.com/browse/movies/score/metascore/year/filtered"
        s = Service(ChromeDriverManager().install())

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1024,768")
        
        if headless:
            options.add_argument("--headless")
            # self.driver = webdriver.Remote(
            #     "http://127.0.0.1:4444/wd/hub", options=options)
            self.driver = webdriver.Chrome(service=s, options=options)
        else:
            self.driver = webdriver.Chrome(service=s)
        self.driver.get(self.url)

    def decline_cookies(self, delay):
        """Rejects the cookie window if it is present."""
        try:  # if the reject cookies button is there then click it
            reject_cookies_btn = WebDriverWait(self.driver, delay).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="onetrust-reject-all-handler"]')))
            reject_cookies_btn.click()

        except NoSuchElementException:  # open the cookies settings, then click reject
            cookies_settings_btn = self.driver.find_element(
                by=By.XPATH, value='//*[@id="ot-sdk-btn"]')
            cookies_settings_btn.click()
            reject_cookies_btn = WebDriverWait(self.driver, delay).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="onetrust-pc-sdk"]/div[3]/div[1]/button[1]')))
            reject_cookies_btn.click()

        except TimeoutException:
            print("Loading cookies took too much time!")

        except:
            pass

    def return_to_film_list(self):
        """Moves the webdriver to the index page of films."""
        self.driver.get(
            "https://www.metacritic.com/browse/movies/score/metascore/year/filtered")

    def get_film_links(self) -> List:
        """Collects all the film links on the current page.

        Returns:
            links = A collection of film URLs (List).
        """
        films = self.driver.find_elements(
            By.XPATH, '//div[@class="title_bump"]//a[@class="title"]')
        links = [film.get_attribute('href') for film in films]
        return links

    def get_uuid(self) -> str:
        """Creates a unique identifier.

        Returns:
            A unique identifier (string).
        """
        return str(uuid.uuid4())

    def return_element_if_exists(self, xpath):
        try:
            ele = self.driver.find_element(By.XPATH, value=xpath)
        except NoSuchElementException:
            return None
        return ele

    def return_elements_if_exist(self, xpath):
        try:
            eles = self.driver.find_elements(By.XPATH, value=xpath)
            ele_list = [ele.text for ele in eles]
        except NoSuchElementException:
            return None
        return ele_list

    def get_friend_id(self) -> str:
        """Creates and returns a 'friendly id' by using the last part of the URL.

        Returns:
            The piece of the current page's url which comes after the last / character (string).
        """
        return self.driver.current_url.split("/")[-1]

    def get_film_title(self) -> str:
        """Finds and returns the current film's title as a string."""
        xpath = '//div[@class="product_page_title oswald"]/h1'
        result = self.return_element_if_exists(xpath)
        ret = result.text if result else result
        return ret

    def get_metascore(self) -> str:
        """Finds and returns the current film's metascore as a string."""
        xpath = '//a[@class="metascore_anchor"]/span'
        result = self.return_element_if_exists(xpath)
        ret = int(result.text) if result else result
        return ret

    def get_release_date(self) -> str:
        """Finds and returns the current film's release date as a string."""
        xpath = '//span[@class="release_date"]/span[2]'
        result = self.return_element_if_exists(xpath)
        release_date = result.text if result else result
        release_date = datetime.strptime(release_date, '%B %d, %Y').date()
        return release_date

    def get_actors(self) -> List:
        """Finds and returns the current film's starring actors as a List."""
        xpath = '//div[@class="summary_cast details_section"]/span[2]/a'
        return self.return_elements_if_exist(xpath)

    def get_directors(self) -> List:
        """Finds and returns the current film's directors as a List."""
        xpath = '//div[@class="director"]/a'
        return self.return_elements_if_exist(xpath)

    def get_genres(self) -> List:
        """Finds and returns the current film's genres as a List"""
        xpath = '//div[@class="genres"]/span[2]/span'
        return self.return_elements_if_exist(xpath)

    def get_rating(self) -> str:
        """Finds and returns the current film's ae rating as a string."""
        xpath = '//div[@class="rating"]/span[2]'
        result = self.return_element_if_exists(xpath)
        ret = result.text if result else result
        return ret

    def get_runtime(self) -> str:
        """Finds and returns the current film's runtime as a string."""
        xpath = '//div[@class="runtime"]/span[2]'
        result = self.return_element_if_exists(xpath)
        runtime = result.text if result else result
        runtime = int(re.sub("[^0-9]", "", runtime))
        return runtime

    def get_summary_img(self) -> str:
        """Finds and returns the current film's summary image source as a string."""
        xpath = '//img[@class="summary_img"]'
        result = self.return_element_if_exists(xpath)
        ret = result.get_attribute("src") if result else result
        return ret

    def save_raw_data(self, dir, data: dict, friend_id: str):
        """Saves the film data as a json file.

        Args:
            dir: A string of the target directory's name.
            friend_id: The friendly id of the data.
        """

        filename = ("{}/{}/{}_data.json").format(dir, friend_id, friend_id)
        # Convert from the Date object so that it can be saved as JSON.
        data['release_date'] = str(data['release_date'])
        try:
            with open(filename, "w", encoding="utf-8") as file:
                # file.write(json.dumps(data))
                json.dump(data, file, ensure_ascii=False)
            self.upload_file_s3(filename, "{}.json".format(friend_id))
        except FileNotFoundError:
            print("File not found.")

    def create_folder(self, dir: str):
        """Creates a directory in the current location.

        Args:
            dir: The name of the directory as a string.
        """

        if not os.path.isdir(dir):
            os.makedirs(dir)
        else:
            print("{} already existed.".format(dir))

    def save_images(self, images: list, friend_id: str):
        """Saves the images in the images directory.

        Args:
            images: A list of image URLs.
            friend_id: The friendly id of the current film.
        """
        if images:
            counter = 0
            for image in images:
                if image is not None:
                    filename = "raw_data/{}/images/{}_{}.jpg".format(
                        friend_id, friend_id, str(counter))
                    img_data = requests.get(image).content
                    with open(filename, 'wb') as handler:
                        handler.write(img_data)
                    self.upload_file_s3(
                        filename, "{}_{}.jpg".format(friend_id, counter))
                    counter += 1

    def upload_file_s3(self, filename: str, final_name: str):
        """Uploads the raw_data directory to the AWS s3 bucket.

        """
        s3_client = boto3.client('s3')
        s3_client.upload_file(filename, 'aicore-datapipe-bucket', final_name)

    def get_local_upload_choices(self):
        """Gets the user's choices to save data to machine locally, upload directly to RDS or both.
        """
        local = input("Save data locally? y/n ")
        upload = input("Upload data to RDS? y/n ")

        return local, upload

    def does_row_exist(self, engine, unique_key, value, table) -> bool:
        """Performs a SQL command to check if the given row is already present in the database.
        """
        result = engine.execute(f"""SELECT 1
                                    FROM {table}
                                    WHERE {unique_key} = '{value}';""").fetchall()
        if result == []:
            return False
        else:
            return True

    def connect_to_RDS(self):
        """Connects to the RDS database and returns the engine.
        """
        config = configparser.ConfigParser()
        config.read('my_config.ini')

        DATABASE_TYPE = config.get('DB', 'database_type')
        DBAPI = config.get('DB', 'dbapi')
        ENDPOINT = config.get('DB', 'endpoint')
        USER = config.get('DB', 'user')
        PASSWORD = config.get('DB', 'password')
        PORT = config.get('DB', 'port')
        DATABASE = config.get('DB', 'database')
        engine = create_engine(
            f"{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{ENDPOINT}:{PORT}/{DATABASE}")
        engine.connect()
        return engine

    def upload_data_to_RDS(self, data):
        """Uploads the data in tabular form to the Amazon RDS.
        """
        engine = self.connect_to_RDS()
        uuid = data['uuid']
        if not self.does_row_exist(engine, 'uuid', uuid, 'film'):
            engine.execute(f'''INSERT INTO film (uuid, friendly_id, title, metascore, release_date, rating, runtime)
                                VALUES ('{uuid}', '{data['friend_id']}', '{data['title']}', '{data['metascore']}',
                                '{data['release_date']}', '{data['rating']}', '{data['runtime']}');''')

        for actor in data['starring']:
            if not self.does_row_exist(engine, 'actor_name', actor, 'actor'):
                engine.execute(
                    f'''INSERT INTO actor (actor_name) VALUES ('{actor}');''')

            actor_id = engine.execute(
                f"""SELECT id FROM actor WHERE actor_name = '{actor}';""").first()[0]
            engine.execute(
                f'''INSERT INTO actor_link (film_id, actor_id) VALUES ('{uuid}', '{actor_id}');''')

        for director in data['director']:
            if not self.does_row_exist(engine, 'director_name', director, 'director'):
                engine.execute(
                    f'''INSERT INTO director (director_name) VALUES ('{director}');''')

            director_id = engine.execute(
                f"""SELECT id FROM director WHERE director_name = '{director}';""").first()[0]
            engine.execute(
                f'''INSERT INTO director_link (film_id, director_id) VALUES ('{uuid}', '{director_id}');''')

        for genre in data['genres']:
            if not self.does_row_exist(engine, 'genre_name', genre, 'genre'):
                engine.execute(
                    f'''INSERT INTO genre (genre_name) VALUES ('{genre}');''')

            genre_id = engine.execute(
                f"""SELECT id FROM genre WHERE genre_name = '{genre}';""").first()[0]
            engine.execute(
                f'''INSERT INTO genre_link (film_id, genre_id) VALUES ('{uuid}', '{genre_id}');''')


if __name__ == "__main__":

    scraper = Scraper(headless=True)
    choices = scraper.get_local_upload_choices()
    scraper.decline_cookies(10)
    film_links = scraper.get_film_links()

    for film in film_links[:100]:
        scraper.driver.get(film)
        scraper.decline_cookies(1)

        data = {'uuid': [], 'friend_id': [], 'title': [], 'metascore': [], 'release_date': [], 'starring': [],
                'director': [], 'genres': [], 'rating': [], 'runtime': [], 'summary_img': []}

        data['uuid'] = scraper.get_uuid()
        data['friend_id'] = scraper.get_friend_id()
        data['title'] = scraper.get_film_title()
        data['metascore'] = scraper.get_metascore()
        data['release_date'] = scraper.get_release_date()
        data['starring'] = scraper.get_actors()
        data['director'] = scraper.get_directors()
        data['genres'] = scraper.get_genres()
        data['rating'] = scraper.get_rating()
        data['runtime'] = scraper.get_runtime()
        data['summary_img'] = scraper.get_summary_img()

        imgs = []
        imgs.append(data['summary_img'])

        print(data)

        if choices[0] == "y":  # Save the data locally.
            print("Saving data locally.")
            scraper.create_folder('raw_data')
            scraper.create_folder('raw_data/{}'.format(data['friend_id']))
            scraper.create_folder(
                'raw_data/{}/images'.format(data['friend_id']))
            scraper.save_raw_data('raw_data', data, data['friend_id'])
            scraper.save_images(imgs, data['friend_id'])

        if choices[1] == "y":  # Upload the data to RDS.
            print("Uploading data to RDS.")
            scraper.upload_data_to_RDS(data)

        print("{} done.".format(data['friend_id']))
        time.sleep(2)
        scraper.return_to_film_list()

    scraper.driver.quit()
