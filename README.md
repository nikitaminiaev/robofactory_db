## Install

	docker-compose build


## Usage
Before up container:

	docker-compose up -d

To restore a test db dump:

    docker exec -ti db bash
    psql -U admin -h db -p 5432 < /home/db/dump/schema.sql
(pass: root)

To execute the code in the api container:

    docker exec api python main.py

or:

    docker exec -ti api bash
    python main.py

### other useful commands:

To enter the db container and to postgres terminal:

    docker exec -ti db bash
    psql postgres://admin:root@localhost:5432
    \connect robofactory;

To enter the container with the python:

    docker exec -ti api bash

To make a db dump:

    docker exec -e PGPASSWORD=root db pg_dump --create -U admin -h db -p 5432 -d robofactory > ./db/dump/schema.sql


    