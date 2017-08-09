import numpy as np
import cv2
import progressbar
import math
from sys import stdout
from PIL import Image
import helpers


def fry(img):
    coords = find_chars(img)
    img = add_b_emojis(img, coords)
    img = add_laughing_emojis(img, 5)
    eyecoords = find_eyes(img)
    img = add_flares(img, eyecoords)

    # bulge at random coordinates
    [w, h] = [img.width - 1, img.height - 1]
    w *= np.random.random(1)
    h *= np.random.random(1)
    r = int(((img.width + img.height) / 10) * (np.random.random(1)[0] + 1))
    img = bulge(img, np.array([int(w), int(h)]), r, 3, 5, 1.8)

    # some finishing touches
    print("Adding some finishing touches... ", end='')
    stdout.flush()
    img = add_noise(img, 0.2)
    img = change_contrast(img, 200)
    print("Done")

    return img


# Downloads image from url to RAM, fries it and saves to disk
def fry_url(url, n):
    # download image and check if image was downloaded successfully
    img = helpers.download_to_ram(url)
    if img is None:
        return

    # fry image n times
    for i in range(n):
        img = fry(img)

    print("Saving temporarily to disk for uploading...")
    img.save('./images/tmp.jpg')


def find_chars(img):
    gray = np.array(img.convert("L"))
    ret, mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    image_final = cv2.bitwise_and(gray, gray, mask=mask)
    ret, new_img = cv2.threshold(image_final, 180, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    dilated = cv2.dilate(new_img, kernel, iterations=1)
    # Image.fromarray(dilated).save('out.png') # for debugging
    _, contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    coords = []
    for contour in contours:
        # get rectangle bounding contour
        [x, y, w, h] = cv2.boundingRect(contour)
        # ignore large chars (probably not chars)
        if w > 70 and h > 70:
            continue
        coords.append((x, y, w, h))
    return coords


# find list of eye coordinates in image
def find_eyes(img):
    print("Searching for eyes...")
    coords = []
    face_cascade = cv2.CascadeClassifier('./classifiers/haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('./classifiers/haarcascade_eye.xml')
    gray = np.array(img.convert("L"))

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces:
        roi_gray = gray[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex, ey, ew, eh) in eyes:
            print("\tFound eye at ({0}, {1})".format(x+ex+ew/2, y+ey+eh/2))
            coords.append((x+ex+ew/2, y+ey+eh/2))
    if len(coords) == 0:
        print("\tNo eyes found.")
    return coords


def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))

    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)


def add_noise(img, factor):
    def noise(c):
        return c*(1+np.random.random(1)[0]*factor-factor/2)
    return img.point(noise)


# add lens flares to coords in given image
# TODO: Add automatic scaling of flares
def add_flares(img, coords):  
    # create a temporary copy if img
    tmp = img.copy()

    # add flares to temporary copy
    print("Adding lens flares...")
    flare = Image.open('./images/lens_flare.png')
    for coord in coords:
        print("\tFlare added to ({0}, {1})".format(coord[0], coord[1]))
        tmp.paste(flare, (int(coord[0]-flare.size[0]/2), int(coord[1]-flare.size[1]/2)), flare)

    return tmp


def add_b_emojis(img, coords):
    # create a temporary copy if img
    tmp = img.copy()

    print("Adding B emojis...")
    b = Image.open('./images/B.png')
    for coord in coords:
        if np.random.random(1)[0] < 0.1:
            print("\tB added to ({0}, {1})".format(coord[0], coord[1]))
            resized = b.copy()
            resized.thumbnail((coord[2], coord[3]), Image.ANTIALIAS)
            tmp.paste(resized, (int(coord[0]), int(coord[1])), resized)

    return tmp


def add_laughing_emojis(img, max):
    # create a temporary copy if img
    tmp = img.copy()

    print("Adding laughing emojis...")
    emoji = Image.open('./images/smilelaugh.png')
    for i in range(int(np.random.random(1)[0]*max)):
        # add laughing emoji to random coordinates
        coord = np.random.random(2)*np.array([img.width, img.height])
        print("\tLaughing emoji added to ({0}, {1})".format(int(coord[0]), int(coord[1])))
        resized = emoji.copy()
        size = int((img.width/10)*(np.random.random(1)[0]+1))
        resized.thumbnail((size, size), Image.ANTIALIAS)
        tmp.paste(resized, (int(coord[0]), int(coord[1])), resized)

    return tmp


# creates a bulge like distortion to the image
# parameters:
#   img = PIL image
#   f   = np.array([x, y]) coordinates of the centre of the bulge
#   r   = radius of the bulge
#   a   = flatness of the bulge, 1 = spherical, > 1 increases flatness
#   h   = height of the bulge
#   ior = index of refraction of the bulge material
def bulge(img, f, r, a, h, ior):
    print("Creating a bulge at ({0}, {1}) with radius {2}... ".format(f[0], f[1], r))

    # load image to numpy array
    width = img.width
    height = img.height
    img_data = np.array(img)

    # determine range of pixels to be checked (square enclosing bulge), max exclusive
    x_min = int(f[0] - r)
    if x_min < 0:
        x_min = 0
    x_max = int(f[0] + r)
    if x_max > width:
        x_max = width
    y_min = int(f[1] - r)
    if y_min < 0:
        y_min = 0
    y_max = int(f[1] + r)
    if y_max > height:
        y_max = height

    # make sure that bounds are int and not np array
    if isinstance(x_min, type(np.array([]))):
        x_min = x_min[0]
    if isinstance(x_max, type(np.array([]))):
        x_max = x_max[0]
    if isinstance(y_min, type(np.array([]))):
        y_min = y_min[0]
    if isinstance(y_max, type(np.array([]))):
        y_max = y_max[0]

    # array for holding bulged image
    bulged = np.copy(img_data)
    bar = progressbar.ProgressBar()
    for y in bar(range(y_min, y_max)):
        for x in range(x_min, x_max):
            ray = np.array([x, y])

            # find the magnitude of displacement in the xy plane between the ray and focus
            s = helpers.length(ray - f)

            # if the ray is in the centre of the bulge or beyond the radius it doesn't need to be modified
            if 0 < s < r:
                # slope of the bulge relative to xy plane at (x, y) of the ray
                m = -s/(a*math.sqrt(r**2-s**2))

                # find the angle between the ray and the normal of the bulge
                theta = np.pi/2 + np.arctan(1/m)

                # find the magnitude of the angle between xy plane and refracted ray using snell's law
                # s >= 0 -> m <= 0 -> arctan(-1/m) > 0, but ray is below xy plane so we want a negative angle
                # arctan(-1/m) is therefore negated
                phi = np.abs(np.arctan(1/m) - np.arcsin(np.sin(theta)/ior))

                # find length the ray travels in xy plane before hitting z=0
                k = (h+(math.sqrt(r**2-s**2)/a))/np.sin(phi)

                # find intersection point
                intersect = ray + helpers.normalise(f-ray)*k

                # assign pixel with ray's coordinates the colour of pixel at intersection
                if 0 < intersect[0] < width-1 and 0 < intersect[1] < height-1:
                    bulged[y][x] = img_data[int(intersect[1])][int(intersect[0])]
                else:
                    bulged[y][x] = [0, 0, 0]
            else:
                bulged[y][x] = img_data[y][x]
    img = Image.fromarray(bulged)
    return img
