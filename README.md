# Botany

Botany is a platform for running tournaments between Python bots.


## Contributing

Botany is my project, but I welcome contributions in the form of bug reports, feature requests, and code.

To report a bug or request a feature, please [raise an issue](https://github.com/inglesp/botany/issues/new) (checking for duplicates first).

To be accepted, a requested feature must be generally useful, and should not unreasonably increase the complexity of the codebase.

For non-trivial code changes, it would be best to first raise an issue that outlines the proposed change.

I have my own idiosyncratic ideas about how code should be written.
When reviewing a pull request, I may request changes to ensure the code is generally correct, but I won't want to get too bogged down in details.
As such, I may merge code and then partially re-write it.
Please do not be put out if I do this!

Thank you to [all the contributors](https://github.com/inglesp/botany/graphs/contributors).

Finally, please ensure that you are kind, considerate, and respectful when interacting on the issue tracker.


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
