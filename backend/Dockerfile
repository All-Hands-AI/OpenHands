FROM python:3.10-slim-buster AS base

# Set the working directory
WORKDIR /app
# manually install sqlite3 from source code
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tcl \
    wget \
    unzip \
    procps \
    && wget https://www.sqlite.org/src/tarball/sqlite.tar.gz \
    && tar xvfz sqlite.tar.gz \
    && cd sqlite \
    # && ./configure \
    && ./configure --enable-fts5 \
    && make \
    && make install \
    && cd .. \
    && rm -rf sqlite \
    && rm sqlite.tar.gz \
    && apt-get remove -y build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# RUN sqlite3 --version
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# RUN apt-get update && apt-get install -y procps
CMD ["uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]
