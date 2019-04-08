from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask import abort
import requests
import os

SYMPTOM_DICT = {
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



def get_coordinates(input_address):
    # grab some lat/long coords from wherever. For this example,
    # I just opened a javascript console in the browser and ran:
    #
    # navigator.geolocation.getCurrentPosition(function(p) {
    #   console.log(p);
    # })
    #
    # Hit Google's reverse geocoder directly
    # NOTE: I *think* their terms state that you're supposed to
    # use google maps if you use their api for anything.
    base = "https://maps.googleapis.com/maps/api/geocode/json"
    params = "?key={key}&address={address}".format(
        key=os.environ['GEOCODE_API'],
        address=input_address.replace(' ','+')
    )
    url = f"{base}{params}"
    response = requests.get(url).json()
    try:
      latitude = response['results'][0]['geometry']['location']['lat']
      longitude = response['results'][0]['geometry']['location']['lng']
      return latitude, longitude
    except Exception as e:
      print(e)
      return None, None


def sanitize(symptom, location):
    symptom = SYMPTOM_DICT[symptom.lower()]
    latitude, longitude = get_coordinates(location)
    return symptom, latitude, longitude


@app.route('/getLocations')
def index():
    symptom = request.args.get('symptom')
    location = request.args.get('location')
    if not symptom or not location:
        abort(404)
    symptom, latitude, longitude = sanitize(symptom, location)
    health = export_dataframe.query.filter(export_dataframe.drg == symptom,
                                           export_dataframe.lat > latitude - 1,
                                           export_dataframe.lat < latitude + 1,
                                           export_dataframe.lng > longitude - 1,
                                           export_dataframe.lng < longitude + 1)
    health_schema = ExportSchema(many=True)
    output = health_schema.dump(health).data
    return jsonify({
        "center" : {
            "lat" : latitude,
            "lng" : longitude
        },
        "drg" : symptom,
        "hospitals" : output,
         })

@app.route('/')
def base():
    return render_template('healthcareMap.html')

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
