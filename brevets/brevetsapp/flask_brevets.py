"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""

import flask
from flask import request
from pymongo import MongoClient
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations
import config
import os

import logging

###
# Globals
###
app = flask.Flask(__name__)
CONFIG = config.configuration()

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetsdb


def db_insert(data):
    """Helper function to control database insertion"""
    valid = int(data['num'])
    if valid == 0:
        raise IndexError
    for i in range(valid):
        i_string = str(i)
        item = {
            'index': int(data['data[' + i_string + '][index]']),
            'miles': float(data['data[' + i_string + '][miles]']),
            'km': float(data['data[' + i_string + '][km]']),
            'location': data['data[' + i_string + '][location]'],
            'open': data['data[' + i_string + '][open]'],
            'close': data['data[' + i_string + '][close]']
        }
        db.timestable.insert_one(item)
    return


def db_find_one(dict):
    """For testing purposes, find an entry"""
    return db.timestable.find_one(dict)


def db_delete_one(entry):
    """For testing purposes, delete an entry"""
    return db.timestable.delete_one(entry)

###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html')


@app.route("/display")
def display():
    app.logger.debug("Display page entry")
    return flask.render_template('display.html', items=list(db.timestable.find()))


@app.route("/submit", methods=["POST"])
def submit():
    app.logger.debug("Attempting to submit data")
    db.timestable.drop()
    db_insert(request.form)
    return flask.jsonify(output=str(request.form))


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('404.html'), 404


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 999, type=float)
    dist = request.args.get('dist', type=int)
    date = request.args.get('date', type=str)
    app.logger.debug("km={}".format(km))
    app.logger.debug("dist={}".format(dist))
    app.logger.debug("date={}".format(date))
    app.logger.debug("request.args: {}".format(request.args))

    open_time = acp_times.open_time(km, dist, arrow.get(date)).format('YYYY-MM-DDTHH:mm')
    close_time = acp_times.close_time(km, dist, arrow.get(date)).format('YYYY-MM-DDTHH:mm')
    result = {"open": open_time, "close": close_time}
    return flask.jsonify(result=result)


#############

app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")
