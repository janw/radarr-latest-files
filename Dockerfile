FROM registry.gitlab.com/janw/python-poetry:3.7-alpine as reqexport

WORKDIR /src
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt -o requirements.txt

FROM python:3.7

WORKDIR /src
COPY --from=reqexport /src/requirements.txt .
COPY radarr_selector.py .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python", "radarr_selector.py" ]
