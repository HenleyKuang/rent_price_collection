uwsgi --http :8081 --wsgi-file rent_price_collection/api/wsgi.py --master --processes 2 --threads 4