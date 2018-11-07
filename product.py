from flask import Flask
from flask import jsonify
from pymongo import MongoClient
from vaultawsec2 import get_mongo_creds

import os

DB_ADDR = 'DB_ADDR'
DB_PORT = 'DB_PORT'
DB_USER = 'DB_USER'
DB_PW = 'DB_PW'

DB_NAME = 'bbthe90s'
COL_NAME = 'products'

PRODUCT_PORT = 'PRODUCT_PORT'
PRODUCT_ADDR = 'PRODUCT_ADDR'

mongo_creds = None

def connect_to_db():
    db_addr = os.environ.get(DB_ADDR)
    db_port = int(os.environ.get(DB_PORT))

    global mongo_creds
    mongo_creds = get_mongo_creds()

    if mongo_creds:
        db_username = mongo_creds[0]
        db_pw = mongo_creds[1]
    else:
        db_username = os.environ.get(DB_USER)
        db_pw = os.environ.get(DB_PW)

    if not db_addr or not db_port:
        # try default connection settings
        client = MongoClient()
    else:
        if not db_pw or not db_username:
            client = MongoClient(db_addr, db_port)
        else:
            client = MongoClient(db_addr, db_port, username=db_username, password=db_pw)

    return client

db_client = connect_to_db()

app = Flask(__name__)

# these can be seeded into the DB for testing if necessary
prods = [{ 'inv_id': 1, 'name':'jncos', 'cost':35.57, 'img':None},
         { 'inv_id': 2, 'name':'denim vest', 'cost':22.50, 'img':None},
         { 'inv_id': 3, 'name':'pooka shell necklace', 'cost':12.37, 'img':None},
         { 'inv_id': 4, 'name':'shiny shirt', 'cost':17.95, 'img':None}]

@app.route("/product", methods=['GET'])
def get_products():
    res = get_products_from_db()
    return jsonify(res)

@app.route("/product/metadata", methods=['GET'])
def get_metadata():
    global mongo_creds

    if mongo_creds:
        db_username = mongo_creds[0]
        db_pw = mongo_creds[1]
    else:
        db_username = os.environ.get(DB_USER)
        db_pw = os.environ.get(DB_PW)

    m = ['X'] * (len(db_pw)-6)
    mask = ''.join(m)
    meta_pw = mask + db_pw[len(db_pw)-6:]

    metadata_dict = {
     "DB_USER": db_username,
     "DB_PW_last_6": meta_pw
    }

    return jsonify(metadata_dict)

@app.route("/product/healthz", methods=['GET'])
def get_health():
    return "OK"

#prints a message with state and timestamp
def tprint(msg):
    now = datetime.datetime.now()
    t = now.strftime("%y-%m-%d %H:%M:%S")
    print("[%s] %s" % (str(t),msg))

def get_products_from_db():
    try:
        return [rec for rec in db_client[DB_NAME][COL_NAME].find({}, {'_id': False})]

    except Exception as e:
        tprint(str(e))
        tprint("Retrying once -->")
        traceback.print_exc()

        global db_client
        db_client = connect_to_db()
        return [rec for rec in db_client[DB_NAME][COL_NAME].find({}, {'_id': False})]

if __name__ == '__main__':
    PORT = os.environ.get(PRODUCT_PORT)
    ADDR = os.environ.get(PRODUCT_ADDR)
    app.run(host=ADDR, port=PORT)
