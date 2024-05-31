# Deploying Django to GCP on k8s using CNC

You've got many options for `flavors` to deploy with `cnc`. For many apps on GCP, we recommend Cloud Run due to the low cost of getting started. `run-lite` flavor will be as cheap as possible, free for many apps. And the `run` flavor adds a hybrid approach of using some k8s services using GKE Autopilot as well as other enterprise best practices. For bigger teams who have made k8s investments or who want to use k8s, `cnc` also offers the `GKE` flavor which uses GKE Autopilot to offer a lot of customization and integration options. This example is illustrative of other languages/frameworks as well, e.g. rails will be similar.
- In this example we are also going to customize the deployment.yml and the deploy script to call a custom webhook before deploying.

Before starting, follow the steps at [Getting Started](../README.md). In particular:
- `cnc` installed with `pip install cocnc`. `cnc` uses python3 so in some environments you'd run `pip3 install cocnc`.
- `terraform` installed (see [here](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)).
- `gcloud` installed ([docs](https://cloud.google.com/sdk/docs/install)) and have run `gcloud auth application-default login` (unless you have an alternative auth setup for `gcloud`). 
- `kubectl` installed, possible with `gcloud components` or using an alternative method. Read more [here](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl).

## repo setup 

Following the instructions at the [django tutorial](https://docs.djangoproject.com/en/5.0/intro/tutorial01/) we have set up our app. We're setting up a complex full-stack API that:
- uses a `Cloud SQL` postgres instance
- uses `redis` as a task broker for `rq`. You mght use `celery` or another consumer as well in place of this, as well as being able to use a hosted redis like upstash or another broker like RabbitMQ or Kafka as well if those were part of your stack
- has a `celery` worker running as its own k8s deployment

Here's an example repo for this setup: [see the repo at github](https://github.com/coherenceplatformdemos/django-gke-cnc-demo-1).

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

You'll want to add allowed hosts, this can be complex in the cloud due to managed load balancers using their IP as their `host` header in many cases. There are a variety of solutions to this problem, for more info read this [post on SO](https://stackoverflow.com/questions/35858040/django-allowed-hosts-for-amazon-elb). For the purpose of this demo, we are going to have you set `ALLOWED_HOSTS` to `*` but in production we are sure you will find a better solution.

The repo has a `rq` worker in `tasks.py`. You will likely have a few similar processes, maybe using another similar library, and can modify the commands in `cnc.yml` as needed. Each worker will get its own independent deployment in k8s, with autoscaling and resource allocation able to be overridden as needed.

## cnc.yml

You add this to `cnc.yml`. Read more about the file format [here](../configuration/cnc.md).

```yaml
services:
  app:
    command: "python manage.py runserver 0.0.0.0:$PORT"
    x-cnc:
      type: backend
      workers:
      - name: default-queue-worker
        # REDIS_URL will be populated by the redis service below by CNC
        command: "rq worker --with-scheduler --url $REDIS_URL"
        system:
          cpu: 1
          memory: 1G
        replicas: 1
    build:
      context: .
  db:
    x-cnc:
      type: database
      version: 15
    image: postgres
  redis:
    x-cnc:
      type: cache
    image: redis
```

As you can see, for each worker you can set minimum replicas, `cpu` and `memory` which is useful if you've got different task resource requirements. 

If needed, you can also customize the `k8s` deployments for the worker and the api server. as much as you'd like, following the `AWS` example [here](../customization/aws_ecs.md) but using the `gke` flavor and appropriate filenames instead. You can add more yml objects into those templates as needed, if required.

## environments.yml

You add this to `environments.yml`. Read more about the file format [here](../configuration/environments.md).

```yaml
# name this whatever you want
name: django-app
provider: gcp
flavor: gke
version: 1

collections:
# eventually you would likely add a "prod" collection in another AWS account as well by adding another element here
- name: dev
  region: us-east-1
  base_domain: dev.api.mycoolapp.ai
  account_id: "theta-era-421317"
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
redis
rq
requests
```

## Provision your infra

- Run `cnc provision apply`. confirm with `yes` when requested by terraform, and then wait for the infra to provision.
- Run `cnc info environments` and set DNS for the `base_domain` above.
  - Get the `IP` by running `cnc info environments` and copying the `Load Balancer IP` into a `CNAME` in your DNS provider for `*.basedomain.com` where your `base_domain` in `environments.yml` is used.
  - Do this once per collection, and then add as many environments without touching DNS record settings again.
- Your SSL cert will usually work in 20 mins or so, but can take more time depending on DNS record propagaton. Read more [here at GCP](https://cloud.google.com/load-balancing/docs/ssl-certificates/troubleshooting).

## Deploy your app

- run `cnc update perform staging --service-tag app=v1`. you can set `v1` to whatever you want to use for the release tag, usually the `git` SHA is a good choice here, can get that with `git rev-parse --short HEAD`.
- the first deploy will take the longest, once this runs once locally building the images will be faster due to docker cache in subsequent runs.
    - 15 mins is normal for first time, 3ish mins after that
    - you can also run this step from CI/CD e.g. github actions once it works for you and you want to automate it

## visit the URL and test the worker

- run `cnc info environments` again, and visit the URL for your `staging` environment. you will see the index content.
- you can test the task worker with a command similar to: 
```
curl -X POST http://your_domain/count/ -H "Content-Type: application/json" -d '{"url": "http://example.com"}'
```

## customize your deploy script

See the docs for [deploy customization](../customization/deploy.md).

## Next steps

- add another environment
- customize your terraform or k8s templates
- add additional services
- explore the toolbox