# Env Setup

1. Create `.env` file
    ```
    AUTH0_DOMAIN=<yourdomain>.auth0.com
    AUTH0_CLIENT_ID=<id>
    AUTH0_CLIENT_SECRET=<secret>
    
    AWS_ACCESS_KEY_ID=<id>
    AWS_SECRET_ACCESS_KEY=<key>
    AWS_DEFAULT_REGION=us-east-1
    ```
1. Create `remote_env.json` and upload it to any S3 bucket. Then change `remote_env` in `zappa_settings.json`
1. `./build-utils/dev-container.sh`
1. `pip install -r requirements.txt`
1. `zappa deploy <env>`
