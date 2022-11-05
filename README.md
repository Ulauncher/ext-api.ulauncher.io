# [API for Extensions Website](http://ext.ulauncher.io/)

This API server is written in Python using bottle, boto3 libraries

## Code Contribution

Any code contributions are welcomed as long as they are discussed in [Github Issues](https://github.com/Ulauncher/ext-api.ulauncher.io/issues) with maintainers.
Be aware that if you decided to change something and submit a PR on your own, it may not be accepted.

# Setup Development Environment

1. Sign up for auth0.com account and create an application (see instructions below)
1. Sign up for AWS account and create a user with limited access (see below)
1. Create `.env` file
    ```
    AUTH0_DOMAIN=<yourdomain>.auth0.com
    AUTH0_CLIENT_ID=<id>
    AUTH0_CLIENT_SECRET=<secret>

    GUNICORN_THREADS=1

    EXTENSIONS_TABLE_NAME=extensions
    EXT_IMAGES_BUCKET_NAME=<bucket-name>
    MONGODB_CONNECTION=mongodb://mongodb:27017
    DB_NAME=ulauncher
    LOG_LEVEL=10

    AWS_ACCESS_KEY_ID=<id>
    AWS_SECRET_ACCESS_KEY=<key>
    AWS_DEFAULT_REGION=us-east-1
    ```
1. `docker network create webproxy`
1. `docker-compose pull` (run this if you ran `docker-compose up` more than a day ago)
1. `docker-compose up -d`
1. `docker exec -it ext-api bash`
1. `./app.py init_db`
1. `./app.py run_server`
1. Open http://localhost:8080/api-doc.html to see API docs
1. Open http://localhost:3000, log in with your Github user and try adding an extension to make sure everything works fine

In order to access Mongodb run `docker exec -it ext-mongodb mongo ulauncher`

# How to Create Auth0 Application

1. After you sign up for auth0 account, click large button Create Application
1. Choose a name (e.g. ulauncher ext-api)
1. Choose Single Page Web App as an application type
1. Go to app settings and copy client ID, domain, and client secret to .env file
1. Set Allowed Callback URLs to http://localhost:3000/auth0-callback
1. In the left sidebar menu select Connections -> Social
1. Click on Github and turn it on
1. In the Popup window switch to Applications tab and enable Github connection for your application

# How to Create And Configure an AWS User

1. Choose IAM in Services menu
1. Go to Users and click Add User
1. Pick a username (example: ext-api-developer) and check "Programmatic access"
1. On the next step choose the last tab: Attach existing policies directly
1. Select "AmazonS3FullAccess" or set more restrictive permissions later by using IAM policy described below
1. Skip Tags step
1. Click create and copy Secret Access Key. You won't be able to see it again, so make sure to save it safely
1. Navigate to S3 service and create a bucket (example: ext-api-images)
1. Save the bucket name to `EXT_IMAGES_BUCKET_NAME` variable in `.env` file

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1556983150000",
            "Effect": "Allow",
            "Action": [
                "s3:DeleteObject",
                "s3:DeleteObjectTagging",
                "s3:DeleteObjectVersion",
                "s3:DeleteObjectVersionTagging",
                "s3:GetAccelerateConfiguration",
                "s3:GetAnalyticsConfiguration",
                "s3:GetBucketAcl",
                "s3:GetBucketCORS",
                "s3:GetBucketLocation",
                "s3:GetBucketLogging",
                "s3:GetBucketNotification",
                "s3:GetBucketPolicy",
                "s3:GetBucketRequestPayment",
                "s3:GetBucketTagging",
                "s3:GetBucketVersioning",
                "s3:GetBucketWebsite",
                "s3:GetInventoryConfiguration",
                "s3:GetIpConfiguration",
                "s3:GetLifecycleConfiguration",
                "s3:GetMetricsConfiguration",
                "s3:GetObject",
                "s3:GetObjectAcl",
                "s3:GetObjectTagging",
                "s3:GetObjectVersion",
                "s3:GetObjectVersionAcl",
                "s3:HeadBucket",
                "s3:ListBucket",
                "s3:ListObjects",
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name-goes-here",
                "arn:aws:s3:::your-bucket-name-goes-here/*"
            ]
        }
    ]
}
```