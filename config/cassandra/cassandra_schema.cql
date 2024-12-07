CREATE KEYSPACE IF NOT EXISTS web_analytics
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE web_analytics;

DROP TABLE IF EXISTS web_analytics.LOG;

CREATE TABLE web_analytics.LOG (
    date text,
    timestamp timestamp,
    request_uri text,
    remote_addr text,
    request_method text,
    status int,
    body_bytes_sent int,
    request_time double,
    http_referrer text,
    http_user_agent text,
    PRIMARY KEY ((date), request_uri, timestamp)
);


DROP TABLE IF EXISTS web_analytics.RESULTS;

CREATE TABLE web_analytics.RESULTS (
    date text,
    page_url text,
    visits int,
    last_processed timestamp,
    PRIMARY KEY (date, page_url)
);