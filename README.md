## Install

	docker-compose build


## Usage
Before up container:

	docker-compose up -d

check that the containers are running:

    docker ps

restore a test db dump:

    docker exec -ti db bash
    psql -U admin -h db -p 5432 < /home/db/dump/schema.sql
(pass: root)

    exit

execute the code in the api container:

    docker exec api python main.py

or:

    docker exec -ti api bash
    python main.py

### other useful commands:

enter the db container and to postgres terminal:

    docker exec -ti db bash
    psql postgres://admin:root@localhost:5432
    \connect robofactory;

enter the container with the python:

    docker exec -ti api bash

make a db dump:

    docker exec -e PGPASSWORD=root db pg_dump --create -U admin -h db -p 5432 -d robofactory > ./db/dump/schema.sql

exit the container:
    
    exit

stop container:

    docker stop api

### migrations

create migration

    alembic revision --autogenerate -m "Create parts_cad table"

execute all new migrations:

    alembic upgrade head

roll back migration:

    alembic downgrade -1