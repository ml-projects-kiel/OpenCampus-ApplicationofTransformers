
format:
	poetry run black --line-length=100 .

format-check:
	poetry run flake8 --config=.flake8

lint: format format-check

install:
	poetry install

kernel:
	poetry run python -m ipykernel install --user --name OpenCampusNLP

requirements:
	poetry export --without-hashes -f requirements.txt -o requirements.txt

test:
	poetry run coverage run --source=NLP_NLP_Project -m pytest -v -p no:warnings
	poetry run coverage report -m --skip-covered

docker:
	docker build --tag=NLP_NLP_Project --memory=2g .
