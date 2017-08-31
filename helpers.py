import numpy as np
import time
import io
import os
import config
import pyimgur
import urllib.error
from urllib.request import urlopen
from PIL import Image

# text added to the end of the bot's reply
bot_stamp = '\n\n^^Beep! ^^I\'m ^^a ^^bot. ^^[Info](/r/DeepFryBot).'


# Generates contents of the bot's temporary reply
def gen_tmp_reply():
    global bot_stamp
    return "Fulfilling frying request..."+bot_stamp


# Generates the content of the bot's reply
def gen_reply(urls):
    global bot_stamp
    if len(urls) > 1:
        # generate comment with all fried urls
        response = 'Here you go:'
        for i in range(len(urls)):
            response += '\n\n{0}. '.format(i)
            response += urls[i]
        response += bot_stamp
        return response
    elif len(urls) == 1:
        return ('[Here you go.]({0})'+bot_stamp).format(urls[0])


# download image from url to ram
# returns Image if successful and None if unsuccessful
def download_to_ram(url):
    # try to open url for n tries
    n = 10
    for i in range(n):
        try:
            response = urlopen(url)
            break
        except urllib.error.HTTPError:
            time.sleep(1)
        except urllib.error.URLError:
            time.sleep(1)
    # save retrieved data to PIL image
    img = None
    try:
        img_bytes = response.read()
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except OSError as e:
        print("URL is not an image, skipping.\n")
    except UnboundLocalError as e:
        print(str(e))
    return img


# uploads temporary image to imgur and returns the url. On failure returns None.
def upload_to_imgur():
    try:
        if os.path.isfile('./images/tmp.jpg'):
            client_id = config.imgur_client_id
            path = os.path.abspath('./images/tmp.jpg')
            im = pyimgur.Imgur(client_id)

            uploaded_image = im.upload_image(path, title="Deep fried by /u/DeepFryBot")
            os.remove('./images/tmp.jpg')
            return uploaded_image.link
        else:
            return None
    except Exception as e:
        print(str(e))


# remove special characters from string
def remove_specials(string):
    return ''.join(c for c in string if c.isalnum()).lower()


# return the length of vector v
def length(v):
    return np.sqrt(np.sum(np.square(v)))


# returns the unit vector in the direction of v
def normalise(v):
    return v/length(v)
