## Install

	docker-compose build


## Usage
before up container:

	docker-compose up -d

to restore a text db dump:

    docker exec -ti db bash
    psql -U admin -h db -p 5432 < /home/db/dump/schema.sql

to execute the code in the api container:

    docker exec api python main.py

or:

    docker exec -ti api bash
    python main.py

### other useful commands:

to enter the db container and to postgres terminal:

    docker exec -ti db bash
    psql postgres://admin:root@localhost:5432
    \connect robofactory;

to enter the container with the python:

    docker exec -ti api bash

to make a db dump:

    docker exec -e PGPASSWORD=root db pg_dump --create -U admin -h db -p 5432 -d robofactory > ./db/dump/schema.sql


    