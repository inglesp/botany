web: gunicorn botany.wsgi --log-file -

house_worker: python manage.py rqworker house
main_worker: python manage.py rqworker main

release: python manage.py migrate
