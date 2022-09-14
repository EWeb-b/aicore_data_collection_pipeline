import unittest
from Scraper import Scraper
import time

MATRIX_URL = "https://www.metacritic.com/movie/the-matrix"

class ScraperTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.t_scraper = Scraper()

    def test_get_film_links(self):
        self.t_scraper.driver.get("https://www.metacritic.com/browse/movies/score/metascore/year/filtered")
        self.t_scraper.decline_cookies()
        links = self.t_scraper.get_film_links()
        assert ("https://www.metacritic.com/movie/aftershock-2022" in links)

    def test_get_film_title(self):
        time.sleep(1)
        self.t_scraper.driver.get(MATRIX_URL)
        self.t_scraper.decline_cookies()
        title = self.t_scraper.get_film_title()
        assert title == "The Matrix"

    def test_get_metascore(self):
        time.sleep(1)
        self.t_scraper.driver.get(MATRIX_URL)
        self.t_scraper.decline_cookies()
        metascore = self.t_scraper.get_metascore()
        assert metascore == "73"
        
    def test_get_release_date(self):
        time.sleep(1)
        self.t_scraper.driver.get(MATRIX_URL)
        self.t_scraper.decline_cookies()
        release_date = self.t_scraper.get_release_date()
        assert release_date == "March 31, 1999"
        
    def test_get_actors(self):
        time.sleep(1)
        self.t_scraper.driver.get(MATRIX_URL)
        self.t_scraper.decline_cookies()
        actors = self.t_scraper.get_actors()
        assert actors == ["Carrie-Anne Moss", "Keanu Reeves", "Laurence Fishburne"]
        
    def test_get_directors(self):
        time.sleep(1)
        self.t_scraper.driver.get(MATRIX_URL)
        self.t_scraper.decline_cookies()
        directors = self.t_scraper.get_directors()
        assert directors == ["Lana Wachowski", "Lilly Wachowski"]
        
    def test_get_genres(self):
        time.sleep(1)
        self.t_scraper.driver.get(MATRIX_URL)
        self.t_scraper.decline_cookies()
        genres = self.t_scraper.get_genres()
        assert genres == ["Action", "Adventure", "Sci-Fi", "Thriller"]

    def test_get_rating(self):
        time.sleep(1)
        self.t_scraper.driver.get(MATRIX_URL)
        self.t_scraper.decline_cookies()
        rating = self.t_scraper.get_rating()
        assert rating == "R"
        
    def test_get_runtime(self):
        time.sleep(1)
        self.t_scraper.driver.get(MATRIX_URL)
        self.t_scraper.decline_cookies()
        runtime = self.t_scraper.get_runtime()
        assert runtime == "136 min"
        
    def test_get_image_src(self):
        time.sleep(1)
        self.t_scraper.driver.get(MATRIX_URL)
        self.t_scraper.decline_cookies()
        img_src = self.t_scraper.get_image_src()
        assert img_src == "https://static.metacritic.com/images/products/movies/5/14d38f138eb320954cd1e07d0449e5a6-250h.jpg"

    def tearDown(self) -> None:
        self.t_scraper.driver.quit()
        del self.t_scraper


unittest.main(argv=[""], verbosity=2, exit=False)
        
        