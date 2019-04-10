from datetime import datetime
from random import random

from google.cloud import firestore

db = firestore.Client.from_service_account_json('co2-gatech-service-key.json')

if __name__ == '__main__':
    # db.collection('departments').document('BAS').set(
    #     {
    #         'created_on': datetime.now(),
    #         'department_id': 351,
    #         'name': 'Bepartment of Bearth and Atmospheric Sciences',
    #         'total_distance': 0,
    #         'total_emissions': 0,
    #         'total_offset': 0
    #     }
    # )
    td, te = 0, 0
    bas_ref = db.document('departments', 'BAS')
    for flight in db.collection('flights').get():
        if random() > 0.5:
            continue
        fk = flight.id + '0'
        fd = flight.to_dict()
        fd['department'] = bas_ref
        fd['passenger'] = fd['passenger'][:-1] + 'g'
        db.document('flights', fk).set(fd)
        td += fd['distance']
        te += fd['emission']
    db.document('departments',
                'BAS').update({
                    'total_distance': td,
                    'total_emissions': te
                })
