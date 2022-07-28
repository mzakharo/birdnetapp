from flask import Flask
from flask import send_from_directory
from flask import render_template
import os

FLUTTER_WEB_APP = 'flutter/build/web'


app = Flask(__name__, template_folder=FLUTTER_WEB_APP)

@app.route('/<path:name>')
def return_flutter_doc(name):

    datalist = str(name).split('/')
    DIR_NAME = FLUTTER_WEB_APP

    if len(datalist) > 1:
        for i in range(0, len(datalist) - 1):
            DIR_NAME += '/' + datalist[i]

    return send_from_directory(DIR_NAME, datalist[-1])

@app.route('/foo')
def say_foo():
    files = []
    folder = '/home/user/birdNet/'
    for x in os.walk(folder):
        files.append(x[2])
    return str(files)

@app.route('/')
def render_page():
    return render_template('/index.html')

if __name__ == '__main__':
    app.run()
