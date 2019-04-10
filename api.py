from datetime import datetime

import connexion
from google.cloud import firestore

db = firestore.Client.from_service_account_json('co2-gatech-service-key.json')

KG_TO_LB = 2.20462
KM_TO_MI = 0.621371


def parse_date(date):
    return datetime.strptime(date, '%Y-%m-%d') if date else None


def department_to_dict(dep):
    d = dep.to_dict()
    d['department'] = dep.id
    return d


def list_departments(offset, limit, fields, units, begin=None, end=None):
    # TODO: Respect the arguments when we have more than one department
    kTotalEmissions = 'total_emissions'
    kTotalDistance = 'total_distance'
    kDepartment = 'department'

    dep_refs = db.collection('departments').get()
    deps = list(map(department_to_dict, dep_refs))
    if begin or end:
        begin = parse_date(begin) or datetime.min
        end = parse_date(end) or datetime.max
        relevant_flights = db.collection('flights').where(
            'departure_date', '>=', begin
        ).where('departure_date', '<=', end).get()
        sums = {dep[kDepartment]: [0, 0] for dep in deps}
        for flight in relevant_flights:
            d = flight.to_dict()
            s = sums[d[kDepartment].id]
            s[0] += d['emission']
            s[1] += d['distance']
        for dep in deps:
            dep[kTotalEmissions], dep[kTotalDistance] = sums[dep[kDepartment]]

    if units == 'imperial':
        for dep in deps:
            # kg to lb
            dep[kTotalEmissions] *= KG_TO_LB
            # km to mi
            dep[kTotalDistance] *= KM_TO_MI
    return {'result': deps, 'total': 1}


def get_top_emitters(offset, limit, units, begin=None, end=None):
    flights_ref = db.collection('flights')
    if begin or end:
        begin = parse_date(begin) or datetime.min
        end = parse_date(end) or datetime.max
        flights_ref.where('departure_date', '>=',
                          begin).where('departure_date', '<=', end)
    emitters = {}
    for flight in flights_ref.get():
        d = flight.to_dict()
        passenger = d['passenger']
        if passenger not in emitters:
            emitters[passenger] = [0, 0, 0]
        # emission, distance, #flights
        data = emitters[passenger]
        data[0] += d['emission']
        data[1] += d['distance']
        data[2] += 1

    emitters = list(emitters.values())
    total = len(emitters)
    emitters.sort(reverse=True)
    emitters = emitters[offset:(limit + offset)]
    if units == 'imperial':
        for emitter in emitters:
            emitter[0] *= KG_TO_LB
            emitter[1] *= KM_TO_MI

    def idx_and_data_to_row(e):
        i, d = e
        return {
            'rank': offset + 1 + i,
            'totalEmissions': d[0],
            'totalDistance': d[1],
            'numberOfFlights': d[2]
        }

    emitters = map(idx_and_data_to_row, enumerate(emitters))
    return {'result': list(emitters), 'total': total}


def add_department(idd, name):
    return 404


def get_department(
    department,
    offset,
    limit,
    fields,
    units,
    begin=None,
    end=None,
    granularity=None
):
    # TODO: respect granularity
    flights_ref = db.collection('flights').order_by('departure_date')
    if begin or end:
        begin = parse_date(begin) or datetime.min
        end = parse_date(end) or datetime.max
        flights_ref.where('departure_date', '>=',
                          begin).where('departure_date', '<=', end)
    if department != 'all':
        dep_ref = db.document('departments', department)
        flights_ref.where('department', '==', dep_ref)
    # For now we're just returning all data in one chunk
    # We are also ignoring cost to offset stuff because we don't have
    #  calculations for that yet
    haul_map = {haul: 0 for haul in ('short', 'medium', 'long')}
    class_map = {
        clas: 0
        for clas in ('economy', 'economy+', 'business', 'first')
    }
    total = 0
    for flight in flights_ref.get():
        d = flight.to_dict()
        emission = d['emission']
        total += emission
        haul_map[d['haul']] += emission
        class_map[d['travel_class']] += emission

    def add_percentages(d):
        return {
            k: {
                'emissions': v,
                'percentage': 100 * v / total
            }
            for k, v in d.items()
        }

    haul_map = add_percentages(haul_map)
    class_map = add_percentages(class_map)

    return [
        {
            'period':
                {
                    'begin': begin or datetime.min,
                    'end': end or datetime.max
                },
            'totalEmissions': total,
            'emissionsByHaul': haul_map,
            'emissionsByClass': class_map
        }
    ]


app = connexion.App(__name__, specification_dir='.', debug=True)
app.add_api('api.yaml')

if __name__ == '__main__':
    app.run(port=80)
