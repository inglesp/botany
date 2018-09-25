# Botany

Botany is a platform for running tournaments between Python bots.

## Development

The code is split into three modules:

 * `server`: a Django app that handles submission of bot code, runs the tournament, and displays a leaderboard
 * `client` a terminal application for developing and testing bots
 * `core`: code common to the server and the client, including code for running games and validating bots

### Developing the server

Setup:

* Ensure Postgres and Redis are installed and running locally
* Create a virtualenv and run:
  * `pip install -r requirements-dev.txt`
  * `pip install -r server/requirements.txt`
* Copy `server/.env-sample` to `server/.env`
* You may need to change the `DATABASE_URL` and `REDIS_URL` values in `.env`
  * By default, we expect a Postgres database called `botany` to exist
    * Run `createdb botany`

* Run database migrations (in `server/`)
  * `python manage.py migrate`

Running the server:

* From the `server` directory, run `python manage.py runserver`

Running the tests:

* From the `server` directory, run `python manage.py test`
