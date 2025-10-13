# Intellico-App
AI-powered research paper analyzer built with Python, NLP models, and React. Designed to summarize dental science papers, extract key methodologies, visualize workflows, and link relevant studies.


# Setup
First use the command:
```bash
docker compose up -d --build
```
This command will build the build the containers using a docker-compose file.
The containers will be up and running. 
After this is done you can test the website.

If running on WSL then follow up that command with this:
```bash
ngrok http 2600
```

What this will do is that it will forward the wsl local host to a ngrok IP and that will help you to access the app on windows browser

## Code updates:
When you update the code and want to check the changes just follow these steps:

```bash
docker compose down
```
This will stop all the containers inside the network that we were running.

```bash
docker compose up -d --build
```

This will rebuild the containers.
Once the containers are rebuilt you can test the website again.