# Data Collection Pipeline project for the AiCore course

## Milestone 1 - Deciding Which Website to Use
- I chose Metacritic as the website I'd be scraping data from. This is because of the wide array of film information it contains.


## Milestone 2 - Prototyping Finding the Individual Page for Each Entry
In this milestone I created the Scraper.py file which contains the Scraper class. This class contains useful methods for performing web scraping:
- The decline_cookies method waits for the Cookies banner to appear and declines the website's cookies request so that execution can continue.
- The get_film_links method finds all of the film links present on the page and returns them in a list object.

I also added the functionality for running the Scraper.py file directly from the command line through the use of 
```python
if __name__ == "__main__"
```


## Milestone 3 - Retrieve Data from Details Page
In this milestone I wrote the code for creating a directory to hold the movie data I wanted,  accessing each of those data points on the webpage, and saving that data.
- Created a dictionary called data to store the various text data like who starred in the film, who directed it, etc.
- Used the built-in selenium methods to access the data points and then stored them in the data dictionary.
```python
directors = self.driver.find_elements(By.XPATH, value = '//div[@class="director"]/a')
data['director'] = [director.text for director in directors]
```
- Used context managers to create the folder raw_data if it doesn't exist, and save the text data to a json file for each film.
- Used a context manager to save the film image to a separate folder called images.
![plot](readme_images/save_details.png)
