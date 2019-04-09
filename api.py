from datetime import datetime

import connexion
from google.cloud import firestore

db = firestore.Client.from_service_account_json('co2-gatech-service-key.json')


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
            dep[kTotalEmissions] *= 2.20462
            # km to mi
            dep[kTotalDistance] *= 0.621371
    return {
        'result': deps,
        'total': 1,
        'timePeriod': '{}:{}'.format(begin, end)
    }


def add_department(idd, name):
    return 404


def get_department(
    department, offset, limit, fields, units, period, granularity
):
    pass


if __name__ == '__main__':
    app = connexion.App(__name__, specification_dir='.', debug=True)
    app.add_api('api.yaml')
    app.run(port=80)
