# import the necessary packages
from PIL import Image
import pytesseract
import argparse
import cv2
import os
from flask import *
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--preprocess", type=str, default="thresh",
    help="type of preprocessing to be done")
args = vars(ap.parse_args())

app = Flask(__name__)

# print (args)
def ocr_func(args): 
    # load the example image and convert it to grayscale
    image = cv2.imread(args["image"])
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # check to see if we should apply thresholding to preprocess the
    # image
    try:
        pp = args["preprocess"]
    except:
        pp = "blur"

    if pp == "thresh":
        gray = cv2.threshold(gray, 0, 255,
            cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # make a check to see if median blurring should be done to remove
    # noise
    elif pp == "blur":
        gray = cv2.medianBlur(gray, 3)
    # write the grayscale image to disk as a temporary file so we can
    # apply OCR to it
    filename = "{}.png".format(os.getpid())
    cv2.imwrite(filename, gray)


    # load the image as a PIL/Pillow image, apply OCR, and then delete
    # the temporary file
    text = pytesseract.image_to_string(Image.open(filename))
    os.remove(filename)
    # print(text)
    return text
    # show the output images
    # cv2.imshow("Image", image)
    # cv2.imshow("Output", gray)
    # cv2.waitKey(0)


@app.route('/hello', methods=['POST'])
def test1():
    print("hello")
    return "Hello world"


@app.route('/ocr', methods=['POST'])
def ocr():

    img_path = "./imgs"

    if not os.path.exists(img_path):
        os.mkdir(img_path)

    files = request.files['file']
    files.save(img_path + '/' + files.filename)

    args = {}

    args['image'] = os.path.join(img_path, files.filename)

    text = ocr_func(args)

    result = {'data':text}
    result_json = json.dumps(result)
    return result_json


if __name__ == '__main__':
    port = os.getenv("OCR_PORT", "NOPORT")
    if port == "NOPORT":
        port = 80
    app.run('0.0.0.0', debug=True, port=int(port))