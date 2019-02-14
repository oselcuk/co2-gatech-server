from flask import Flask, request, jsonify
import json

app = Flask(__name__)
with open('dummy-data.json') as dd:
    dummy_data = json.load(dd)
    departments = []
    for dep, details in dummy_data['departments'].items():
        departments.append(details)
        departments[-1]['url'] = '/departments/' + dep

deps_base = '/departments'
@app.route(deps_base, methods=['GET'])
def get_deps():
    args = request.args
    #TODO: validate args
    #TODO: use an argument parsing library for this
    total = len(departments)
    fields = args.get('fields')
    print (fields)
    offset = int(args.get('offset', 0))
    limit = int(args.get('limit', 10))
    limit = min(limit, 100, total - offset)
    result = departments[offset:limit + offset] if limit > 0 else []
    if fields:
        fields = fields.split(',')
        result = [{k:v for k,v in res.items() if k in fields}
                    for res in result]
    response = {
        'total': total,
        'ok': True,
        'result': result
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=80)