import boto3
import configparser
import os
import json
import requests
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from typing import Any

def does_row_exist(engine: Engine, column: str, value: Any, table: str) -> bool:
        """Performs a SQL command to check if the given row is already present in the database.

        Args:
            engine: The connection to the remote database.
            unique_key: The column of the table being checked.
            value: We check to see if this value is in the table.
            table: The table in the database being considered.

        Returns:
            Boolean: True if the row is in the database, False if not.
        """
        result = engine.execute(f"""SELECT 1
                                    FROM {table}
                                    WHERE {column} = '{value}';""").fetchall()
        if result == []:
            return False
        else:
            return True

def connect_to_RDS() -> Engine:
    """Connects to the RDS database and returns the engine.

    Returns:
        engine: An Engine object which has connected to the database.
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

def upload_data_to_RDS(data: dict) -> None:
    """Uploads the data in tabular form to the Amazon RDS.

    Args:
        data: The film data which will be saved the RDS, in the form of a dict.
    """
    engine = connect_to_RDS()
    uuid = data['uuid']
    if not does_row_exist(engine, 'uuid', uuid, 'film'):
        engine.execute(f'''INSERT INTO film (uuid, friendly_id, title, metascore, release_date, rating, runtime)
                            VALUES ('{uuid}', '{data['friend_id']}', '{data['title']}', '{data['metascore']}',
                            '{data['release_date']}', '{data['rating']}', '{data['runtime']}');''')

        for actor in data['starring']:
            if not does_row_exist(engine, 'actor_name', actor, 'actor'):
                engine.execute(
                    f'''INSERT INTO actor (actor_name) VALUES ('{actor}');''')

            actor_id = engine.execute(
                f"""SELECT id FROM actor WHERE actor_name = '{actor}';""").first()[0]
            engine.execute(
                f'''INSERT INTO actor_link (film_id, actor_id) VALUES ('{uuid}', '{actor_id}');''')

        for director in data['director']:
            if not does_row_exist(engine, 'director_name', director, 'director'):
                engine.execute(
                    f'''INSERT INTO director (director_name) VALUES ('{director}');''')

            director_id = engine.execute(
                f"""SELECT id FROM director WHERE director_name = '{director}';""").first()[0]
            engine.execute(
                f'''INSERT INTO director_link (film_id, director_id) VALUES ('{uuid}', '{director_id}');''')

        for genre in data['genres']:
            if not does_row_exist(engine, 'genre_name', genre, 'genre'):
                engine.execute(
                    f'''INSERT INTO genre (genre_name) VALUES ('{genre}');''')

            genre_id = engine.execute(
                f"""SELECT id FROM genre WHERE genre_name = '{genre}';""").first()[0]
            engine.execute(
                f'''INSERT INTO genre_link (film_id, genre_id) VALUES ('{uuid}', '{genre_id}');''')

def save_raw_data(dir, data: dict, friend_id: str):
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
        upload_file_s3(filename, "{}.json".format(friend_id))
    except FileNotFoundError:
        print("File not found.")

def create_folder(dir: str):
    """Creates a directory in the current location.

    Args:
        dir: The name of the directory as a string.
    """

    if not os.path.isdir(dir):
        os.makedirs(dir)
    else:
        print("{} already existed.".format(dir))

def save_images(images: list, friend_id: str):
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
                upload_file_s3(
                    filename, "{}_{}.jpg".format(friend_id, counter))
                counter += 1

def upload_file_s3(filename: str, final_name: str):
    """Uploads the raw_data directory to the AWS s3 bucket.

    """
    s3_client = boto3.client('s3')
    s3_client.upload_file(filename, 'aicore-datapipe-bucket', final_name)
