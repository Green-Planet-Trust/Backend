''' 
Taken from IBM Solution-Starter-Kit-Energy-2020
Heavily adapted by Team Green Planet for IBM 2020 IBM Intern hackathon
'''

from cloudant.client import Cloudant
import csv
import time
import configparser
import json

from flask import Flask, request
from flask_restx import Api, Resource, fields, reqparse
from flask_cors import CORS

app = Flask(__name__)
''' CORS is needed for dev on our own machines '''
CORS(app)

api = Api(app, version='1.0', title='Cloud Impact Rating API',
          description='A protoype API system allowing the storage and retrieval of Climate Impact Rating data for products',
          prefix='/v1'
          )


''' Allows for private storage of config files '''
config = configparser.ConfigParser()
config.read('config.ini')

''' Provide the secret credentials '''
api_access = config['DEFAULT']

client = Cloudant.iam(
    api_access['username'],
    api_access['apikey'],
    connect=True
)

product_ns = api.namespace(
    'product', description='User CIR Product Operations')

# Define the API models we will use (these will show up in the Swagger Specification).

rating = api.model('Rating', {
    'Production': fields.Float(required=False, description='The efficiency-in-use rating (0-9, where 0 is best) of this item'),
    'Transportation': fields.Float(required=False, description='The energy (J) to produce this item'),
    'Retail': fields.Float(required=False, description='The CO2 released (Kg) to produce this item'),
})

product = api.model('Product', {
    'id': fields.String(readonly=True, description='The unique product registration identifier'),
    'UID': fields.String(readonly=True, description='The unique product registration identifier'),
    'CarbonFootprint': fields.Float(required=True, description='The barcode for this product id, in EAN-13 format'),
    'CurrentCompany': fields.String(required=True, description='The type of product'),
    'isRecycleable': fields.String(required=True, description='The category of this product, with its type'),
    'Stages': fields.Nested(rating),
    'Date': fields.String(required=True, description='The category of this product, with its type'),
    'description': fields.String(required=True, description='The description of this product, with its type'),
    'previous': fields.String(required=True, description='The description of this product, with its type')
})

db_name = 'cir-db3'

# A Data Access Object to handle the reading and writing of Product records to the Cloudant DB


class ProductDAO(object):
    def __init__(self):
        if db_name in client.all_dbs():
            self.cir_db = client[db_name]
        else:
            # Create the DB and immport the dummy data
            self.cir_db = client.create_database(db_name)
            self.import_data()

    def import_data(self):
        print("Importing dummy data", end='', flush=True)
        with open('newDummyData.txt') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count > 0:
                    data = {
                        'UID': row[0],
                        'CarbonFootprint': float(row[1]),
                        'CurrentCompany': row[2],
                        'isRecycleable': row[3],
                        'Stages': {
                            'Production': float(row[4]),
                            'Transportation': float(row[5]),
                            'Retail': float(row[6])
                        },
                        'Date': row[7],
                        'descpription': row[8],
                        'previous': row[9]
                    }
                    # Have to rate limit it to less than 10 a second, due to free tier
                    time.sleep(0.15)
                    self.create(data)
                    print(".", end='', flush=True)
                line_count += 1
        print("complete")

    def list(self):
        return [x for x in self.cir_db]

    def get(self, id):
        try:
            my_document = self.cir_db[id]
            my_document['id'] = my_document['UID']
        except KeyError:
            api.abort(404, "Product {} not registered".format(id))
        return my_document

    def get_by_barcode(self, barcode_id):
        # For now this is easy, since id is the same as barcode_id....in the future this would need an
        # index of some such search ability
        try:
            my_document = self.cir_db[barcode_id]
            my_document['id'] = my_document['UID']
        except KeyError:
            api.abort(404, "Product {} not registered".format(id))
        return my_document

    def create(self, data):
        # For now, we'll set the id to be the same as the barcode_id. For production systems, we would
        # probably want these seperate, and to implement indexed searching by barcode_id for GET.
        try:
            data['_id'] = str(data['UID'])
            my_document = self.cir_db.create_document(data)
            my_document['id'] = my_document['UID']
        except KeyError:
            api.abort(404, "Product {} already registered".format(id))
        return my_document

    def update(self, id, data):
        # Not currently supported
        try:
            my_document = self.cir_db[id]
            for key, value in data.items():
                my_document[key] = value

            my_document.save()

        except KeyError:
            api.abort(404, "Product {} does not exist".format(id))
        return

    def delete(self, id):
        try:
            my_document = self.cir_db[id]
            my_document.delete()
        except KeyError:
            api.abort(404, "Product {} not registered".format(id))
        return


# Handlers for the actual API urls

# In a more production orientated version, you might well split these endpoints into
# those for a consumer (which is really just "look up by barcode"), and those that
# allow manufacturers to publish their product data.

@product_ns.route('', methods=['GET', 'POST', 'PUT'])
class Product(Resource):
    @api.marshal_with(product)
    @api.doc('List products')
    @api.doc(params={'barcode_id': 'The barcode ID of this product (optional)'})
    def get(self):
        # Currently we support either a full list, or query by barcode_id.
        parser = reqparse.RequestParser()
        parser.add_argument('barcode_id', required=False, location='args')
        args = parser.parse_args()
        if args['barcode_id']:
            return [ProductDAO().get_by_barcode(args['barcode_id'])]
        else:
            return ProductDAO().list()

    @api.marshal_with(product, code=201)
    @api.doc(body=product)
    def post(self):
        return ProductDAO().create(json.loads((request.data).decode('utf8'))), 201


@product_ns.route('/<string:id>', methods=['GET', 'POST', 'PUT'])
class ProductWithID(Resource):
    @api.marshal_with(product)
    @api.doc(params={'id': 'The unique ID of this product'})
    def get(self, id):
        return ProductDAO().get(id)

    @api.marshal_with(product)
    @api.doc(params={'id': 'The unique ID of this product'})
    def delete(self, id):
        return ProductDAO().delete(id)

    @api.marshal_with(product)
    @api.doc(body=product, params={'id': 'The unique ID of this product'})
    def put(self, id):
        return ProductDAO().update(id=id, data=json.loads((request.data).decode('utf8')))

    def post(self, id):
        return ProductDAO().create(data=json.loads((request.data).decode('utf8')))


if __name__ == '__main__':
    app.run()
