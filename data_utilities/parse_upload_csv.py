import csv
import datetime
import os

from Crypto.Hash import SHA256
from google.cloud import firestore

from distance_calculator import distance_between_airports_km as dist

db = firestore.Client.from_service_account_json('co2-gatech-service-key.json')


def travel_class_from_code(c):
    # Taken from:
    #  https://your.yale.edu/work-yale/campus-services/travel-relocation-fleet/travel/air-travel/airfare-codes # noqa: E501
    c = c.upper()
    if c in ['W']:
        return 'economy+'
    if c in ['C', 'D', 'J', 'I', 'Z']:
        return 'business'
    if c in ['A', 'F', 'P', 'R']:
        return 'first'
    return 'economy'


def haul_from_km(km):
    if km < 463:
        return 'short'
    if km < 3700:
        return 'medium'
    return 'long'


airline_details = None


def airline_from_code(code):
    global airline_details
    if not airline_details:
        with open(
            'airlines.csv', newline='', encoding='utf-8'
        ) as airlines_file:
            airlines = csv.DictReader(airlines_file)
            airline_details = [ad for ad in airlines]
    # print('Airline details: ', airline_details)
    code = str(code)
    for airline in airline_details:
        if code == airline['IATA Accounting Code'
                           ] or code == airline['IATA Code']:
            return airline
    print('Couln\'t find code: ', code)
    return None


def dept_ref_from_code(code):
    return list(
        db.collection('departments').where('department_id', '==',
                                           int(code)).get()
    )[0].reference


def parse_date(date):
    return datetime.datetime.strptime(date, '%m/%d/%y')


def parse_and_insert_airports(path):
    airports_ref = db.collection('airports')
    count = 0
    with open(path, newline='', encoding='utf-8') as airports_file:
        airports = csv.DictReader(airports_file)
        for airport in airports:
            if 'airport' not in airport['type']:
                continue
            code = airport['iata_code'] or airport['local_code']
            if not code:
                continue
            count += 1
            if count <= 20100:
                continue
            name = airport['name']
            coords = firestore.GeoPoint(
                float(airport['latitude_deg']),
                float(airport['longitude_deg'])
            )
            location = '{}, {}'.format(
                airport['municipality'], airport['iso_country']
            )  # TODO: Parse this and iso_region
            airports_ref.document(code).set(
                {
                    'coordinates': coords,
                    'location': location,
                    'name': name
                }
            )
            # count += 1
            if count % 100 == 0:
                print('Added ', count)


def emission_factor(haul, clas):
    # Table taken from:
    #  https://pics.uvic.ca/sites/default/files/AirTravelWP_FINAL.pdf
    # page 8, table 1
    table = [
        [.14678, .16508, .27867], [.23484, .24761, .24761],
        [.42565, .24761, .24761], [.58711, .24761, .24761]
    ]
    # TODO: turn these into enums, probably extract flights into a class
    hi = ['long', 'medium', 'short'].index(haul)
    ci = ['economy', 'economy+', 'business', 'first'].index(clas)
    return table[ci][hi]


def parse_csv(path):
    flights_ref = db.collection('flights')
    added_emissions = {}
    with open(path, encoding='utf-8-sig', newline='') as flights_file:
        flights = csv.DictReader(flights_file)
        for flight in flights:
            if flight['Status'] != 'Sale':
                # TODO: keep refunds to remove corresponding sales later
                continue
            stops = list(
                map(
                    lambda x: db.document('airports', x),
                    flight['Travel Route'].split('/')
                )
            )
            coords = list(
                map(lambda x: x.get().to_dict()['coordinates'], stops)
            )
            classes = flight['Travel Class'].split('/')
            vendors = flight['Vendor(s)'].split('/')
            if len(stops) != len(classes) + 1 or len(classes) != len(vendors):
                print('Malformed data for flight: ', flight['Ticket Number'])
                rl = len(stops) - 1

                def pad(l, n):
                    return (l + n * [l[-1]])[:n]

                classes = pad(classes, rl)
                vendors = pad(vendors, rl)
                # continue
            obj = {}
            obj['passenger'] = get_name_hash(flight['Passenger Name'])
            dep = dept_ref_from_code(flight['3 dgt Numeric Dept Code'])
            obj['department'] = dep
            obj['departure_date'] = parse_date(flight['Departure Date'])
            obj['arrival_date'] = parse_date(flight['Final Arrival Date'])
            obj['issue_date'] = parse_date(flight['Issue Date'])
            obj['cost'] = float(
                flight['Air Fare'].replace(',', '').replace('$', '')
            )
            obj['owning_ticket'] = flight['Ticket Number']
            if dep not in added_emissions:
                added_emissions[dep] = [0, 0]  # km, co2
            stats = added_emissions[dep]
            for i in range(len(classes)):
                obj['airline'] = airline_from_code(vendors[i])['ICAO Callsign']
                obj['plane'] = db.document('planes/Airbus-350')  # TODO
                obj['from'] = stops[i]
                obj['to'] = stops[i + 1]
                distance = dist(coords[i], coords[i + 1]) * 1.08
                obj['distance'] = distance
                obj['haul'] = haul_from_km(distance)
                obj['travel_class'] = travel_class_from_code(classes[i])
                # Emission calculations come from our client
                # TODO: extract these to a function and make the constants
                #  easily changable
                factor = emission_factor(obj['haul'], obj['travel_class'])
                # calculate the emission per passenger, accounting for
                #  radiative forcing
                obj['emission'] = distance * factor * 1.9
                idd = '{}.{}'.format(obj['owning_ticket'], i + 1)
                flights_ref.document(idd).set(obj)
                stats[0] += distance
                stats[1] += obj['emission']
    for dep, (km, co2) in added_emissions.items():
        d = dep.get(['total_emissions', 'total_distance']).to_dict()
        d['total_distance'] += km
        d['total_emissions'] += co2
        dep.update(d)


def get_name_hash(name, salt=None):
    if not salt:
        salt = os.environ['SECRET_SALT']
    if type(name) is str:
        name = name.encode('utf-8')
    return SHA256.new(name).hexdigest()


if __name__ == '__main__':
    # parse_and_insert_airports('../data/csvs/airports.csv')
    # parse_csv('../data/csvs/2017.csv')
    parse_csv('../data/csvs/2018.csv')
