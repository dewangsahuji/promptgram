# promptgram

Completed the authorisation setup using cookies










terminal 

docker run --name postgres-db ^
-e POSTGRES_PASSWORD=01010101 ^
-e POSTGRES_USER=postgres ^
-e POSTGRES_DB=prompt_platform ^
-p 5432:5432 ^
-v pg_data:/var/lib/postgresql ^
-d postgres


docker run -d --name prompt-redis -p 6379:6379 redis:7-alpine





