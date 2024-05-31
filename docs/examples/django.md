# Deploying Django to AWS using CNC

We are going to deploy a django app with a postgres DB to ECS using the built-in `ecs` flavor of `cnc`. Read more about `ecs` deployment [here](../flavors/aws/ecs.md).

Before starting, follow the steps at [Getting Started](../README.md). If you are using `aws sso` for your credentials locally, you'll need to set `AWS_PROFILE=PROFILE_NAME` in your environment.

## repo setup 

Following the instructions at the [django tutorial](https://docs.djangoproject.com/en/5.0/intro/tutorial01/) we have set up our app. Here's an example: [django](https://github.com/coherenceplatformdemos/django-cnc-demo-1).

As indicated in the tutorial, we update settings with the right configuration to talk to our database. For `django` with `postgres` this looks like:

```
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": "5432",
    }
}
```

The environment variables refereced will be automatically populated by `cnc` based on the configuration's resources. In your app, you'd want to handle setting these in development to the right values, having defaults that work locally when these are not set (e.g. in dev), or using an alternate `settings.py` with different values.

## cnc.yml

You add this to `cnc.yml`. Read more about the file format [here](../configuration/cnc.md).

```yaml
services:
  app:
    # activating the venv is due to using nixpacks, if you write your own dockerfile you don't need this part of the command
    command: ". /opt/venv/bin/activate && python manage.py runserver 0.0.0.0:$PORT"
    x-cnc:
      type: backend
    build:
      context: .
  db:
    x-cnc:
      type: database
      version: 15
    image: postgres
```

## environments.yml

You add this to `environments.yml`. Read more about the file format [here](../configuration/environments.md).

```yaml
# name this whatever you want
name: django-app
provider: aws
flavor: ecs
version: 1

collections:
# eventually you would likely add a "prod" collection in another AWS account as well by adding another element here
- name: dev
  region: us-east-1
  base_domain: dev.mynextsite.com
  account_id: "123476727859"
  environments:
  - name: staging
    environment_variables:
    - name: FOO
      value: bar
```

See more about available options including environment variables in [configuration](../configuration/README.md).

## add requirements file

You can either write your own `Dockerfile` and supply it under the `build` as `dockerfile` in the `cnc.yml` or you can use the built in support for `nixpacks`. As per nixpacks [docs](https://nixpacks.com/docs/providers/python) we are going to add a `requirements.txt` to configure as python build. Add the following to `requirements.txt`:

```
django
psycopg2
```

## Provision your infra

- run `cnc provision apply`. confirm with `yes` when requested by terraform, and then wait for the infra to provision. should take just a few minutes. the only thing this will create is the NS records zone for your base domain. you only need to do this once per collection, and then can add as many environments as you like under that domain without waiting for this again or touching DNS settings again.
- run `cnc info environments` and grab the `NS` records to set for your DNS provider for the domain you set in `base_domain` above.
- after applying those NS records to your provider, run `cnc provision apply`. confirm with `yes` when requested by terraform, and then wait for the infra to provision, should take longer than the first time perhaps 10 mins or so.

## Deploy your app

- run `cnc update perform staging --service-tag app=v1`. you can set `v1` to whatever you want to use for the release tag, usually the `git` SHA is a good choice here, can get that with `git rev-parse --short HEAD`.
- the first deploy will take the longest, once this runs once locally building the images will be faster due to docker cache in subsequent runs.
    - 15 mins is normal for first time, 3ish mins after that
    - you can also run this step from CI/CD e.g. github actions once it works for you and you want to automate it

## visit the URL

- run `cnc info environments` again, and visit the URL for your `staging` environment.

## Next steps

- add another environment
- customize your terraform
- add additional services
- explore the toolbox