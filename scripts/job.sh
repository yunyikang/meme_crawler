#!/bin/bash
# export DB_PASSWORD_FILE=$DB_PASSWORD_FILE 
# export API_KEY_FILE=$API_KEY_FILE 
# export API_SECRET_FILE=$API_SECRET_FILE 
# export DB_USER=$DB_USER 

scriptPath=$(dirname "$(readlink -f "$0")")
source "${scriptPath}/.env.sh"

# the docker-compose variables should be available here
echo "DB_USER = ${DB_USER}"
echo "scriptPath = ${scriptPath}"

/usr/local/bin/python /app/crawl.py
