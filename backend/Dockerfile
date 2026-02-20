FROM python:3.11-slim-bullseye

ENV HOME=/usr/local/lib

# Update the system
RUN apt-get update && apt-get install -y gcc curl g++ \
    && curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 - \
    && rm -rf /var/lib/apt/lists/*

# Env for poetry
ENV PATH=/etc/poetry/bin:$PATH
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml

# Remove any pre-existing installation of pymupdf to avoid conflicts
RUN pip uninstall -y pymupdf || true
# Install pymupdf separately to ensure no conflicts
RUN pip install pymupdf
# Install dependencies
RUN poetry install --no-root

# Download NLTK data
RUN python -m nltk.downloader averaged_perceptron_tagger punkt

# Copy the application files
COPY ./ /app

RUN chmod +x /app/run.sh

EXPOSE 8000

ENV PROCESS=server

ENTRYPOINT ["/app/run.sh"]
