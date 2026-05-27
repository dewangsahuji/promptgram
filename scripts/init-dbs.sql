-- This script runs once when the PostgreSQL container is first initialized.
-- It creates a dedicated database for each microservice.

CREATE DATABASE auth_db;
CREATE DATABASE prompt_db;
CREATE DATABASE social_db;
