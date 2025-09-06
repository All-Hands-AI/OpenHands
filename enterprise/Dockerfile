ARG OPENHANDS_VERSION=latest
ARG BASE="ghcr.io/all-hands-ai/openhands"
FROM ${BASE}:${OPENHANDS_VERSION}

# Datadog labels
LABEL com.datadoghq.tags.service="deploy"
LABEL com.datadoghq.tags.env="${DD_ENV}"

# Install Node.js v20+ and npm (which includes npx)
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get install -y jq gettext && \
    apt-get clean

RUN pip install alembic psycopg2-binary cloud-sql-python-connector pg8000 gspread stripe python-keycloak asyncpg sqlalchemy[asyncio] resend tenacity slack-sdk ddtrace posthog "limits==5.2.0" coredis prometheus-client shap scikit-learn pandas numpy

WORKDIR /app
COPY enterprise .

RUN chown -R openhands:openhands /app && chmod -R 770 /app
USER openhands

# Command will be overridden by Kubernetes deployment template
CMD ["uvicorn", "saas_server:app", "--host", "0.0.0.0", "--port", "3000"]
