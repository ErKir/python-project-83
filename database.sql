CREATE TABLE urls (
    id         bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name       varchar(255) UNIQUE NOT NULL, 
    created_at timestamp NOT NULL
);

CREATE TABLE url_checks (
    id          bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id      bigint,
    status_code varchar(255),
    h1          varchar(255),
    title       varchar(255),
    description varchar(65535),
    created_at timestamp NOT NULL
);
