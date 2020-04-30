This is an alpha version of Docker support for cartography.

## Docker Deploys
1. Ensure that the docker daemon is installed in running.
2. Ensure that the following environment variables are set in the shell
	- AWS_ACCESS_KEY_ID
	- AWS_SECRET_ACCESS_KEY
	- AWS_SESSION_TOKEN
	- NEO4J_USERNAME (If this is the first time you are deploying cartography, then this value must be `neo4j`.)
	- NEO4J_PASSWORD
3. Run `docker-compose build`
4. Run `docker-compose up`

### Testing with Docker
1. Ensure that the docker daemon is installed in running.
2. Run `docker-compose build`
3. Run `docker-compose up`
