import boto3
import configparser
import os
import json
import psycopg2
import requests
from typing import Any
from psycopg2 import sql
from psycopg2.extensions import connection

def connect_to_RDS_psy():
    config = configparser.ConfigParser()
    config.read('my_config.ini')

    ENDPOINT = config.get('DB', 'endpoint')
    USER = config.get('DB', 'user')
    PASSWORD = config.get('DB', 'password')
    PORT = config.get('DB', 'port')
    DATABASE = config.get('DB', 'database')

    conn = psycopg2.connect(
        host = ENDPOINT,
        user = USER,
        password = PASSWORD,
        database = DATABASE,
        port = PORT
    )
    return conn

def does_row_exist(conn: connection, column: str, value: Any, table: str) -> bool:
        """Performs a SQL command to check if the given row is already present in the database.

        Args:
            conn: The connection to the remote database.
            column: The column of the table being checked.
            value: We check to see if this value is in the table.
            table: The table in the database being considered.

        Returns:
            Boolean: True if the row is in the database, False if not.
        """
        cur = conn.cursor()
        query = sql.SQL("SELECT 1 FROM {} WHERE {} = (%s)").format(sql.Identifier(table), sql.Identifier(column))
        cur.execute(query, (value,))
        result = cur.fetchone()
        cur.close()

        if result == None:
            return False
        else:
            return True

def upload_data_to_RDS(conn: connection, data: dict) -> None:
    """Uploads the data in tabular form to the Amazon RDS.

    Args:
        conn: The connection to the RDS.
        data: The film data which will be saved the RDS, in the form of a dict.
    """
    film_uuid = data['uuid']
    if not does_row_exist(conn, 'uuid', film_uuid, 'film'):
        cur = conn.cursor()
        query = sql.SQL("""
            INSERT INTO film (uuid, friendly_id, title, metascore, release_date, rating, runtime)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """)
        cur.execute(query, [film_uuid, data['friend_id'], data['title'], data['metascore'], data['release_date'], data['rating'], data['runtime']])
        conn.commit()
        cur.close()        

        actor_director_genre_upload(conn, 'actor', 'actor_name', 'actor_link', 'actor_id', data['actors'], film_uuid)
        actor_director_genre_upload(conn, 'director', 'director_name', 'director_link', 'director_id', data['directors'], film_uuid)
        actor_director_genre_upload(conn, 'genre', 'genre_name', 'genre_link', 'genre_id', data['genres'], film_uuid)

def actor_director_genre_upload(conn: connection, group: str, group_name: str, group_link: str, group_id: str, value_list: list, film_uuid: str) -> None:
    """Saves the actor, director, or genre data to the RDS and also creates the relationships in the RDS.

    Args:
        conn: The connection to the RDS.
        group: The name of the group. Either 'actor', 'director', or 'genre'.
        group_link: The name of the linking table.
        group_id: The name of the id column.
        value_list: The list of actors, directors, or genres to be saved.
        film_uuid: The uuid of the film.
    """
    cur = conn.cursor()
    for value in value_list:
        try:
            # Save the actor, director, or genre to the RDS if it's not already in there.
            if not does_row_exist(conn, group_name, value, group):
                query = sql.SQL("INSERT INTO {} ({}) VALUES (%s)").format(sql.Identifier(group), sql.Identifier(group_name))
                cur.execute(query, (value,))
                conn.commit()

            # Get the id of the actor, director, or genre.
            query2 = sql.SQL("SELECT id from {} WHERE {} = (%s)").format(sql.Identifier(group), sql.Identifier(group_name))
            cur.execute(query2, (value,))
            value_id = cur.fetchone()[0]
            conn.commit()

            # Link the actor, director, or genre with the film through the use of an association table.
            query3 = sql.SQL("INSERT INTO {} (film_id, {}) VALUES (%s, %s)").format(sql.Identifier(group_link), sql.Identifier(group_id))
            cur.execute(query3, [film_uuid, value_id])
            conn.commit()

        except (Exception, psycopg2.Error) as error:
            print(f"Error while saving {value}.", error)

    cur.close()

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
    """Saves the images in the images directory, and uploads them to the s3 bucket.

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

    Args:
        filename: The path to the file to be uploaded.
        final_name: The name the file will have in the s3 bucket.
    """
    s3_client = boto3.client('s3')
    s3_client.upload_file(filename, 'aicore-datapipe-bucket', final_name)
