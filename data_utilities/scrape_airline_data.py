import requests
import string
import re
from lxml import etree
from io import StringIO
import csv

def scrape():
    codes = []
    for c in string.digits + string.ascii_uppercase:
        res = requests.post('http://www.avcodes.co.uk/airllistres.asp', data={'iataairllst': c, 'B1': 'Submit', 'statuslst': 'Y'})
        links = re.findall(r'details\.asp\?ID=(\d+)', res.text)
        codes.extend(links)
        # break
    # print('Found codes: ', codes)

    keys = set()
    airlines = {}
    for code in codes:
        data = getById(code)
        keys.update(data.keys())
        airlines[code] = data

    with open('airlines.csv', 'w', encoding='utf-8', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        for k,v in airlines.items():
            print('Writing ', k)
            dict_writer.writerow(v)

def getById(idd):
    print('Parsing ', idd)
    url = 'http://www.avcodes.co.uk/details.asp'
    res = requests.get(url, params={'ID': idd})
    parser = etree.XMLParser(recover=True)
    xml = etree.parse(StringIO(res.text), parser)
    rows = xml.findall('.//td')
    data = {}
    for row in rows:
        text = etree.tostring(row, method='text', encoding='unicode')
        if ':' in text:
            k, v = text.split(':', 1)
            data[k.strip()] = v.strip().replace('\n', ' ')
    return data

if __name__ == '__main__':
    scrape()
    # print(getById('27309'))