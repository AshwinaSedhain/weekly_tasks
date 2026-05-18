
# This file is to save those commands in one place incase i forget them.
# also insted of typing the long commmand everytime just write make build and its done
#start with  --make build --command 
# can srat the project just with make + the word
#for eg:- make build, make airflow-connection,make trigger-dags
#make down, make ps, make logs, make test



#builds and starts all Docker containers
build:
	docker-compose up --build -d

#starts containers without rebuilding
up:
	docker-compose up -d

#stops all containers
down:
	docker-compose down

#stops containers and deletes all data
down-volumes:
	docker-compose down -v

#	restarts all containers
restart:
	docker-compose restart

#shows live logs from all containers
logs:
	docker-compose logs -f

#runs all pytest tests
test:
	pip install -r tests/requirements.txt
	pytest tests/ -v

#adds the postgres connection to Airflow
airflow-connection:
	docker exec healthstream-airflow-web airflow connections add healthstream_postgres \
		--conn-type postgres \
		--conn-host postgres \
		--conn-login healthstream \
		--conn-password healthstream123 \
		--conn-schema healthstream \
		--conn-port 5432

#triggers all 4 DAGs at once
trigger-dags:
	docker exec healthstream-airflow-web airflow dags trigger healthstream_daily_etl
	docker exec healthstream-airflow-web airflow dags trigger healthstream_batch_processing
	docker exec healthstream-airflow-web airflow dags trigger healthstream_cleanup
	docker exec healthstream-airflow-web airflow dags trigger healthstream_reporting


#shows which containers are running
ps:
	docker-compose ps
