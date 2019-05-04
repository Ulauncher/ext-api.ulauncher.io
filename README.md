# Env Setup

1. Sign up for auth0.com account and create an application (see instructions below)
1. Create `.env` file
    ```
    AUTH0_DOMAIN=<yourdomain>.auth0.com
    AUTH0_CLIENT_ID=<id>
    AUTH0_CLIENT_SECRET=<secret>

    EXTENSIONS_TABLE_NAME=extensions
    EXT_IMAGES_BUCKET_NAME=dev-ulauncher-ext-image
    MONGODB_CONNECTION=mongodb://mongodb:27017
    DB_NAME=ulauncher
    LOG_LEVEL=10

    AWS_ACCESS_KEY_ID=<id>
    AWS_SECRET_ACCESS_KEY=<key>
    AWS_DEFAULT_REGION=us-east-1
    ```
1. `docker network create webproxy`
1. `docker-compose up -d`
1. `docker exec -it ext-api bash`
1. `./app.py init_db`
1. `./app.py run_server`
1. Open http://localhost:8080/api-doc.html to see API docs

In order to access Mongodb run `docker exec -it ext-mongodb mongo ulauncher`

# How to create an auth0 application

1. After you sign up for auth0 account, click large button Create Application
1. Choose a name (e.g. ulauncher ext-api)
1. Choose Single Page Web App as an application type
1. Go to app settings and copy client ID, domain, and client secret to .env file
1. In the left sidebar menu select Connections -> Social
1. Click on Github and turn it on
1. In the Popup window switch to Applications tab and enable Github connection for your application
