default: build

clean:

build: 
	docker build -t bquest/backend .	

run: 
	-pkill docker-compose
	docker-compose up

restart:
	docker-compose restart web

ssh: 
	docker exec -i -t `docker ps -q --filter status=running --filter ancestor=bquest/backend:latest` /bin/bash

# usage: make run_command cmd="echo hi"
run_command:
	docker exec -i -t `docker ps -q --filter status=running --filter ancestor=bquest/backend:latest` /bin/bash -c "$(cmd)"

shell:
	docker exec -i -t `docker ps -q --filter status=running --filter ancestor=bquest/backend:latest` /bin/bash -c "/code/src/manage.py shell_plus"

test:
	docker exec -i -t `docker ps -q --filter status=running --filter ancestor=bquest/backend:latest` /bin/bash -c "cd /code/src && ./manage.py test --no-input --parallel $(args)" 

clean_db:
	docker-compose exec db psql -U postgres -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'

init_db: clean_db 
	cat init_db.sql | docker exec -i `docker-compose ps -q db` psql -U postgres 
	docker-compose exec web /bin/bash -c "cd /code/src && ./manage.py migrate"

restore-db:

backup_db:
	docker exec -t `docker ps -q --filter status=running --filter ancestor=postgres:10.1-alpine` pg_dumpall -c -U postgres > bquest_dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql

save_requirements:
	docker exec -i -t `docker ps -q --filter status=running --filter ancestor=bquest/backend:latest` /bin/bash -c "pip3 freeze" | tail -n +2 > requirements.txt

install_package:
	docker exec -i -t `docker ps -q --filter status=running --filter ancestor=bquest/backend:latest` /bin/bash -c "pip3 install $(pkg)"
	docker exec -i -t `docker ps -q --filter status=running --filter ancestor=bquest/backend:latest` /bin/bash -c "pip3 freeze" | tail -n +2 > requirements.txt

