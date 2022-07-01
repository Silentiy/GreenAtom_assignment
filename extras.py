from io import BytesIO
from PIL import Image
from random import randrange


def create_test_image():
    """ Creates small square images with random colors
    for test purposes """

    color = (randrange(1, 255), randrange(1, 255), randrange(1, 255))
    file = BytesIO()
    image = Image.new('RGB', size=(50, 50), color=color)
    image.save(file, 'jpeg')
    file.name = 'test.jpeg'
    file.seek(0)
    return file
