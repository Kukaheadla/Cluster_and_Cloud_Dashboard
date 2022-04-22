#!bin/bash
# this file simply holds some commands that you might find useful

# build and starts
docker-compose -f docker-compose.prod.yml up -d --build

# kills and removes containers
# docker-compose -f docker-compose.prod.yml down -v   