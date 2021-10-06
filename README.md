Building: docker build -t how2die/chan-backend .
Running: docker run -e DB_HOST=db -e DB_NAME=chan -e FLASK_DEBUG=1 --name chan-backend --link some-postgres:db -p 5000:5000 how2die/chan-backend

Create Keycloak client, with Access Type bearer-only