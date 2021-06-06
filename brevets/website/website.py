import flask
from flask import Flask, render_template
import requests

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')


@app.route('/listdata', methods=["POST"])
def listdata():
    app.logger.debug("Got a form submission")
    if flask.request.form.get('dtype') is '':
        dtype = 'json'
    else:
        dtype = flask.request.form.get('dtype')
    if flask.request.form.get('topk') is not '':
        topk = flask.request.form.get('topk')
    else:
        topk = '0'
    which = flask.request.form.get('which')
    app.logger.debug(f"dtype: {dtype}")
    app.logger.debug(f"topk: {topk}")
    app.logger.debug(f"which: {which}")
    r = requests.get('http://restapi:5000/' + which + '/' + dtype + '?top=' + topk)
    return render_template('listdata.html', data=r.text)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
