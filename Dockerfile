FROM python:3.10-slim@sha256:2bac43769ace90ebd3ad83e5392295e25dfc58e58543d3ab326c3330b505283d
WORKDIR /usr/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ ./

# Create directories for archive and logs with appropriate permissions
RUN mkdir -p /archive /usr/app/logs \
    && adduser --disabled-password --gecos "" botuser \
    && chown -R botuser:botuser /usr/app /archive

USER botuser

CMD [ "python3", "./main.py" ]
