set FLASK_ENV=production
waitress-serve --port=80 --call flaskr:create_app