from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask import abort
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthdata.db'

db = SQLAlchemy(app)
ma = Marshmallow(app)


class export_dataframe(db.Model):
    index = db.Column('Index',db.Integer, primary_key = True)
    drg = db.Column('DRG Definition', db.Text)
    id = db.Column('Provider Id', db.Integer)
    name = db.Column('Provider Name', db.Text)
    addr = db.Column('Provider Street Address', db.Text)
    city = db.Column('Provider State', db.Text)
    post = db.Column('Provider Zip Code', db.Integer)
    hrr = db.Column('Hospital Referral Region (HRR) Description', db.Text)
    discharge = db.Column('Total Discharges', db.Integer)
    cover = db.Column('Average Covered Charges', db.Float)
    payment = db.Column('Average Total Payments', db.Float)
    medicare = db.Column('Average Medicare Payments', db.Float)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    #oop = db.Column('Average OOP Costs', db.Float)

class ExportSchema(ma.ModelSchema):
    class Meta:
        model = export_dataframe



def lat_lon(address):
    # grab some lat/long coords from wherever. For this example,
    # I just opened a javascript console in the browser and ran:
    #
    # navigator.geolocation.getCurrentPosition(function(p) {
    #   console.log(p);
    # })
    #
    key = 'key=AIzaSyC3X0TSZGpyq2OZ69Lr8hBmT1giHWvmhQ8'
    # Hit Google's reverse geocoder directly
    # NOTE: I *think* their terms state that you're supposed to
    # use google maps if you use their api for anything.
    base = "https://maps.googleapis.com/maps/api/geocode/json?" + key
    params = "&address={query}".format(
        query=address.replace(' ','+')
    )
    url = "{base}{params}".format(base=base, params=params)
    response = requests.get(url).json()
    try:
      response['results'][0]['geometry']['location']['address'] = address
      return response['results'][0]['geometry']['location']
    except:
      return {'address': None, 'lat': None, 'lng': None}


def sanitize(symptom, location):
    sym_dict = {
        "internal bleeding": "039 - EXTRACRANIAL PROCEDURES W/O CC/MCC" ,
        "alzheimer's": "057 - DEGENERATIVE NERVOUS SYSTEM DISORDERS W/O MCC",
        "parkinson's": "057 - DEGENERATIVE NERVOUS SYSTEM DISORDERS W/O MCC",
        "huntington's": "057 - DEGENERATIVE NERVOUS SYSTEM DISORDERS W/O MCC",
        "seizure": "101 - SEIZURES W/O MCC",
        "stroke": "101 - SEIZURES W/O MCC",
        "dizzy": "149 - DYSEQUILIBRIUM",
        "vertigo": "149 - DYSEQUILIBRIUM",
        "heart attack": "282 - ACUTE MYOCARDIAL INFARCTION, DISCHARGED ALIVE W/O CC/MCC",
        "high blood pressure": "305 - HYPERTENSION W/O MCC",
        "chest pain": "313 - CHEST PAIN",
        "diabetes": "638 - DIABETES W CC",
        "alcohol poisoning": "897 - ALCOHOL/DRUG ABUSE OR DEPENDENCE W/O REHABILITATION THERAPY W/O MCC'",
    }

    sym = sym_dict[symptom.lower()]

    coords = lat_lon(location)

    return sym, coords['lat'], coords['lng']


@app.route('/getLocations')
def index():
    symptom = request.args.get('symptom')
    location = request.args.get('location')

    if not symptom or not location:
        abort(404)

    sym, lat, lng = sanitize(symptom, location)

    health = export_dataframe.query.filter(export_dataframe.drg == sym,
                                           export_dataframe.lat > lat - 1,
                                           export_dataframe.lat < lat + 1,
                                           export_dataframe.lng > lng - 1,
                                           export_dataframe.lng < lng + 1)
    health_schema = ExportSchema(many=True)
    output = health_schema.dump(health).data
    #return '<h1>Hello World!<h1>'
    return jsonify({
        "center" : {
            "lat" : lat,
            "lng" : lng
        },
        "drg" : sym,
        "hospitals" : output,
         })

@app.route('/')
def base():
    return render_template('healthcareMap.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 33507))
    app.run(debug=True, port=port)
