FROM postgres:14.1-alpine

ENV POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=postgres

EXPOSE 5432
