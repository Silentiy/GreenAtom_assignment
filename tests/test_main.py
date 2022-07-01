from datetime import datetime
from datetime import timedelta
from random import randrange
import requests
from fastapi.testclient import TestClient

from ..main import app
from ..extras import create_test_image


client = TestClient(app)


# test post requests
def test_send_one_jpg_file():
    url = "http://127.0.0.1:8000/frames/"
    files = [('files', (f"im1.jpg", create_test_image().read(), 'image/jpeg'))]

    response = requests.post(url=url, files=files)
    assert response.status_code == 200


def test_send_from_2_to_15_jpg_files():
    url = "http://127.0.0.1:8000/frames/"
    files = list()
    for i in range(randrange(2, 15)):
        files.append(('files', (f"im{i}.jpg", create_test_image().read(), 'image/jpeg')))

    response = requests.post(url=url, files=files)
    assert response.status_code == 200


def test_send_no_files():
    url = "http://127.0.0.1:8000/frames/"
    files = list()

    response = requests.post(url=url, files=files)
    assert response.status_code == 422


def test_send_16_jpg_files():
    url = "http://127.0.0.1:8000/frames/"
    files = list()
    for i in range(16):
        files.append(('files', (f"im{i}.jpg", create_test_image().read(), 'image/jpeg')))

    response = requests.post(url=url, files=files)
    assert response.status_code == 400


# test get requests
def test_get_files_with_existing_registration_date():
    now = datetime.now()
    date_lower = now - timedelta(days=1)
    date_upper = now + timedelta(days=1)
    date_lower_str = date_lower.strftime("%Y-%m-%d_%H:%M:%S")
    date_upper_str = date_upper.strftime("%Y-%m-%d_%H:%M:%S")
    limit = 3

    parameters = f"?date_lower={date_lower_str}&date_upper={date_upper_str}&limit={limit}"
    url = f"http://127.0.0.1:8000/frames/get/{parameters}"

    response = requests.get(url=url)
    assert response.status_code == 200


def test_get_files_with_non_existing_registration_date():
    now = datetime.now()
    date_lower = now - timedelta(days=10)
    date_upper = now - timedelta(days=9)
    date_lower_str = date_lower.strftime("%Y-%m-%d_%H:%M:%S")
    date_upper_str = date_upper.strftime("%Y-%m-%d_%H:%M:%S")
    limit = 3

    parameters = f"?date_lower={date_lower_str}&date_upper={date_upper_str}&limit={limit}"
    url = f"http://127.0.0.1:8000/frames/get/{parameters}"
    response = requests.get(url=url)

    response = requests.get(url=url)
    assert response.status_code == 404


# test delete requests
def test_delete_files_with_existing_uuids():
    now = datetime.now()
    date_lower = now - timedelta(days=1)
    date_upper = now + timedelta(days=1)
    date_lower_str = date_lower.strftime("%Y-%m-%d_%H:%M:%S")
    date_upper_str = date_upper.strftime("%Y-%m-%d_%H:%M:%S")
    limit = 2
    parameters = f"?date_lower={date_lower_str}&date_upper={date_upper_str}&limit={limit}"
    url = f"http://127.0.0.1:8000/frames/get/{parameters}"
    data = requests.get(url=url).json()

    files_uuids = list()
    for element in data:
        files_uuids.append(element['stored_file_name'])

    files_string = "&files_names=".join(files_uuids)
    url = f"http://127.0.0.1:8000/frames/delete/?files_names={files_string}"

    response = requests.delete(url=url)
    assert response.status_code == 204


def test_delete_files_with_non_existing_uuids():
    files_uuids = ["non_existing_name_1.jpg", "non_existing_name_2.jpg"]

    files_string = "&files_names=".join(files_uuids)
    url = f"http://127.0.0.1:8000/frames/delete/?files_names={files_string}"

    response = requests.delete(url=url)
    assert response.status_code == 404
