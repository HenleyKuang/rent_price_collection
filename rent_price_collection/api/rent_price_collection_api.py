from collections import namedtuple
from flask import Flask, json, request
from flask_cors import CORS

from rent_price_collection.storage.all_listings_mysql import (
    AllListingsMySql,
    SearchParameterObject,
    SEARCH_PARAMETERS,
)

app = Flask(__name__)
CORS(app)

all_listings_mysql = AllListingsMySql()

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/search", methods=['GET'])
def search():
    search_parameters_list = []
    for name in SEARCH_PARAMETERS:
        try:
            value = request.args[name]
            search_parameters_list.append(value)
        except KeyError:
            search_parameters_list.append(None)

    offset = 0
    try:
        offset = request.args["offset"]
    except KeyError:
        pass

    sortby = "date_updated"
    try:
        sortby = request.args["sortby"]
    except KeyError:
        pass

    sortdesc = False
    try:
        sortdesc = request.args["sortdesc"]
    except KeyError:
        pass

    search_parameter_object = SearchParameterObject._make(search_parameters_list)
    results = all_listings_mysql.search_listings(search_parameter_object, offset=offset, sortby=sortby, desc=sortdesc)
    response = app.response_class(
        response=json.dumps(results),
        status=200,
        mimetype='application/json'
    )
    return response

if __name__ == "__main__":
    app.run("0.0.0.0", 8081, use_reloader=True, debug=True)
