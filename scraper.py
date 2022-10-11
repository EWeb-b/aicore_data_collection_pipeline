# Local files.
import data_saving
import film_details

# Other imports.
import sys
import time
from psycopg2.extensions import connection
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Any
from webdriver_manager.chrome import ChromeDriverManager


class Scraper:

    def __init__(self, headless=False) -> None:
        self.url = "https://www.metacritic.com/browse/movies/score/metascore/all/filtered?page=0"
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

    def decline_cookies(self, delay: int) -> None:
        """Rejects the cookie window if it is present.

        Args:
            delay: The amount of time to wait for the Cookies window to appear.
        """
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

    def click_next_page(self):
        """Clicks the next page of the film list."""
        next_page_btn = self.driver.find_element(
            By.XPATH, '//span[@class="flipper next"]//a[@class="action"]')
        next_page_link = next_page_btn.get_attribute('href')
        self.driver.get(next_page_link)

    def get_film_links(self) -> list:
        """Collects all the film links on the current page.

        Returns:
            links = A collection of film URLs (List).
        """
        films = self.driver.find_elements(
            By.XPATH, '//div[@class="title_bump"]//a[@class="title"]')
        links = [film.get_attribute('href') for film in films]
        return links

    def get_local_upload_choices(self, args: list) -> tuple:
        """Gets the user's choices to save data to machine locally, upload directly to RDS or both. From command line args.

        Args:
            args: This is simply sys.argv, the command line arguments when the file is run.
        """
        correct_usage_msg = """Argument error. Correct usage: `python3 scraper.py <local_choice> <upload_choice>` where <local_choice> and
                                <upload_choice> are y or n and refer to if you want to save the scraped data locally and/or upload it to the AWS RDS."""

        try:
            local, upload = args[1], args[2]
            if len(args) == 3:
                if local in ["y", "n"] and upload in ["y", "n"]:
                    return local, upload
                else:
                    raise ValueError(' '.join(correct_usage_msg.split()))
            else:
                raise ValueError(' '.join(correct_usage_msg.split()))
        except IndexError as e:
            print(e, ' '.join(correct_usage_msg.split()))
            sys.exit(1)
    
    def scrape_single_film_data(self) -> tuple[dict, list]:
        """Scrapes all of the data of a singular film and returns the data. Assumes scraper is already on the film's page.

        Returns:
            data: A dictionary of the film's data.
            imgs: A list of the image urls. 
        """
        data = {'uuid': [], 'friend_id': [], 'title': [], 'metascore': [], 'release_date': [], 'starring': [],
                'director': [], 'genres': [], 'rating': [], 'runtime': [], 'summary_img': []}

        data['uuid'] = film_details.get_uuid()
        data['friend_id'] = film_details.get_friend_id(self.driver)
        data['title'] = film_details.get_film_title(self.driver)
        data['metascore'] = film_details.get_metascore(self.driver)
        data['release_date'] = film_details.get_release_date(self.driver)
        data['starring'] = film_details.get_actors(self.driver)
        data['director'] = film_details.get_directors(self.driver)
        data['genres'] = film_details.get_genres(self.driver)
        data['rating'] = film_details.get_rating(self.driver)
        data['runtime'] = film_details.get_runtime(self.driver)
        data['summary_img'] = film_details.get_summary_img(self.driver)

        imgs = []
        imgs.append(data['summary_img'])

        return data, imgs

    def manage_saving_data(self, data: dict, imgs: list, friend_id: str, choices: tuple, conn=None) -> None:
        """Performs the high-level operations for saving the film data by calling other functions depending on user choices.

        Args:
            data: The dictionary of film data to be saved.
            imgs: A list of image urls.
            friend_id: A string similar to the film's title. Serves as a unique identifier.
            choices: A tuple of strings, inputted by the user, to indicate their preferences on saving the film data.
        """
        if choices[0] == "y":  # Save the data locally.
            print("Saving data locally.")
            data_saving.create_folder('raw_data/{}'.format(friend_id))
            data_saving.create_folder(
                'raw_data/{}/images'.format(friend_id))
            data_saving.save_raw_data('raw_data', data, friend_id)
            data_saving.save_images(imgs, friend_id)

        if choices[1] == "y":  # Upload the data to RDS.
            print("Uploading data to RDS.")
            data_saving.upload_data_to_RDS(conn, data)

    def run_scraper(self) -> None:
        """Performs the main execution loop of the webscraper.
        Loops through all the films on the page, scraping each one. Then moves on to the next page and repeats
        until it has gone through all the pages.
        """
        # Gets the user's choices on uploading/saving data locally.
        choices = scraper.get_local_upload_choices(sys.argv)
        if choices[0] == "y":
            data_saving.create_folder('raw_data')
        if choices[1] == "y":
            conn = data_saving.connect_to_RDS_psy()
        scraper.decline_cookies(10)

        while True:
            scraper.decline_cookies(1)
            film_links = scraper.get_film_links()
            current_page = scraper.driver.current_url

            for film in film_links:
                # Navigate to film's page.
                scraper.driver.get(film)
                scraper.decline_cookies(1)

                # Scrape this film's data.
                data, imgs = scraper.scrape_single_film_data()

                # Save the data locally, upload to RDS, do both, or do neither.
                scraper.manage_saving_data(data, imgs, data['friend_id'], choices, conn)

                print(data)
                print("{} done.".format(data['friend_id']))
                time.sleep(1)

                # Return to the page we were on.
                scraper.driver.get(current_page)

            # If a next page exists, click it. Otherwise we are done and program can exit.
            if film_details.return_element_if_exists(scraper.driver, '//span[@class="flipper next"]//a[@class="action"]') is None:
                break
            else:
                scraper.click_next_page()

        # Close the psycopg2 connection and the selenium webdriver.
        if conn is not None:
            conn.close()
        scraper.driver.quit()


if __name__ == "__main__":

    scraper = Scraper(headless=True)
    scraper.run_scraper()

