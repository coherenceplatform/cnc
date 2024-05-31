# Deploying FastAPI to GCP using CNC

We are going to deploy a [FastAPI](https://fastapi.tiangolo.com/) app to Google Cloud using the `run-lite` flavor which is the lowest cost container deployment architecture available at the low end of cloud right now. It will be free to get started (depending on usage and free tier eligibility).

Before starting, follow the steps at [Getting Started](../README.md). In particular:
- `cnc` installed with `pip install cocnc`.
- `gcloud` installed ([docs](https://cloud.google.com/sdk/docs/install)) and have run `gcloud auth application-default login` (unless you have an alternative auth setup for `gcloud`). 

## database choice (if applicable)

You can use a `Cloud SQL` instance by creating a `database` service type in `cnc`, see the [Django](./django.md) setup example for what that looks like. In this case, `cnc` will automatically manage a secret and inject `DATABASE_URL` automatically, which will correspond to the database instance created for each environment.

With the `run-lite` flavor using more free-compatible services, it would be common to pair this deployment with a managed database offering such as [firebase](firebase.com), [supabase](supabase.com), [neon](neon.tech), or similar. in this case, you'd set an environment variable for `DATABASE_URL` yourself (possibly using a secret_id instead of providing the value directly) and do the setup for that database instance outside of `cnc`. In this example, we'll use this option.

## repo setup 

You've followed the [steps](https://fastapi.tiangolo.com/) at FastAPI to get started. [Here's](https://github.com/coherenceplatformdemos/fastapi-cnc-demo-1) an example.

## add requirements file

You can either write your own `Dockerfile` and supply it under the `build` as `dockerfile` in the `cnc.yml` ([docs](../configuration/cnc.md)) or you can use the built in support for `nixpacks`. As per nixpacks [docs](https://nixpacks.com/docs/providers/python) we are going to add a `requirements.txt` to configure as a python build. Add the following to `requirements.txt`:

```
fastapi
psycopg2
sqlalchemy
uvicorn
```

## cnc.yml

You add this to `cnc.yml`

```yaml
services:
  app:
     # activating the venv is due to using nixpacks, if you write your own dockerfile you don't need this part of the command
    command: ". /opt/venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port $PORT"
    x-cnc:
      type: backend
    build:
      context: .
```

## environments.yml

You add this to `environments.yml`

```yaml
name: my-fastapi-app
provider: gcp
flavor: run-lite
version: 1

collections:
- name: dev
  region: us-east1
  base_domain: dev.mynextsite.com
  account_id: "my-gcp-project"
  environments:
  - name: staging
    environment_variables:
    - name: DATABASE_URL
      value: "value://from_db_provider"
```

See more about available options including environment variables in [configuration](../configuration/README.md).

## Provision your infra

- run `cnc provision apply`. confirm with `yes` when requested by terraform, and then wait for the infra to provision, should take just a few minutes

## Deploy your app

- run `cnc update perform staging --service-tag app=v1`. you can set `v1` to whatever you want to use for the release tag, usually the `git` SHA is a good choice here, can get that with `git rev-parse --short HEAD`.
- the first deploy will take the longest, once this runs once locally building the images will be faster due to docker cache in subsequent runs.
    - you can also run this step from CI/CD e.g. github actions once it works for you and you want to automate it

## visit the URL

- In the GCP console, check out your Cloud Run service and access it with the URL provided. You can add a custom domain to each service, as well, using the GCP UI.

## Next steps

- add another environment
- customize your terraform
- add additional services
- explore the toolbox