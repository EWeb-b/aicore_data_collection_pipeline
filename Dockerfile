FROM python:3.10

COPY my_config.ini .
COPY requirements.txt .
COPY Scraper.py .
COPY testing.py .

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2==2.9.3
RUN pip install -r requirements.txt

CMD ["python", "Scraper.py"]

