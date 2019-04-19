# CO<sub>2</sub> \@ Georgia Tech
CO<sub>2</sub> @ Georgia Tech is a project aiming to raise awareness of the environmental impacts of institute business related flights at Georgia Tech. This repo is the back-end, which can be used on its own, or in conjunction with [co2-gatech](https://github.com/oselcuk/co2-gatech) as its frontend. This README is for the backend, see the [README for co2-gatech](https://github.com/oselcuk/co2-gatech/blob/master/README.md).

Go to https://co2-gatech.appspot.com for a live demo.

## Release notes
### v0.1.0 (2019-04-19)
#### Features
 * [OpenAPI](https://swagger.io/docs/specification/about/) specs for the API ([api.yaml](api.yaml))
 * Parameter validation using [connexion](https://connexion.readthedocs.io)
 * `/departments` and `/top_emitters` endpoints working
 * Includes some [utility scripts](data_utilities) for importing flight data from CSV files, to be used until Georgia Tech makes a decision about the new flight expensing software they will use
 * Uses FireStore as the data layer

#### Bug Fixes
n/a

#### Known issues
 * `POST` and `DELETE` operations are currently not supported, due to the uncertainty around how data uploading will happen
 * For the same reason, authentication isn't currently set up, and will depend on if the upload process is automated or not
 * Paging is currently not implemented for `GET`s to `/departments`
 * `granularity` values other than `year` are not implemented for `/departments/{department}`
 * FireStore is not ideal as the data layer due to the high volume of read operations we need to do for most API endpoints. We should consider moving to a sql-like database for speed gains.

## Installation
### Pre-requisites
 * [python 3.6 or newer](https://www.python.org/download/releases/3.0/)
 * [pip](https://pypi.org/project/pip/).
 * A FireStore service account key json file, placed in the root of the project under the name `co2-gatech-service-key.json`
 * `virtualenv` is **strongly** recommended, in order to prevent version conflicts for dependencies

### Downloading
 * `git clone git@github.com:oselcuk/co2-gatech-server.git` or [download the repo](https://github.com/oselcuk/co2-gatech-server/archive/master.zip) and unzip.

### Dependencies
`pip install -r requirements.txt` or manually install the following libraries and their dependencies:
 * `connexion[swagger-ui]`
 * `google-cloud-firestore`
 * `pycryptodome`

### Deployment
Simply run `python api.py` for local deployment for testing purposes.

For production builds, use a production WSGI server of your choice such as [`Gunicorn`](https://gunicorn.org/) to run `api:app`.

An `app.yaml` file is included with the project for deployment on Google App Engine. If using, simply run `gcloud app deploy` with a valid GAE configuration.

API will be served at `host/api/`. For instance, if serving on `localhost:5000`, `GET localhost:5000/api/departments/EAS` would return data for EAS department.

#### Deployment with the frontend
To deploy with the front-end, check out the front-end repo into a folder named `front-end` (`git clone git@github.com:oselcuk/co2-gatech.git front-end/co2-gatech`) and deploy with `gcloud app deploy` as before.

Front-end will be served on the root of the GAE instance.

## Documentation

Interactive API docs are generated from the OpenAPI specs and served at `/api/ui`. It can be found on the live demo at https://co2-gatech.appspot.com/api/ui and also at https://app.swaggerhub.com/apis-docs/co2-gatech/api/1
