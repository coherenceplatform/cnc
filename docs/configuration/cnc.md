
# The CNC configuration file

`cnc` uses a superset of [docker-compose](https://docs.docker.com/compose/compose-file/) for configuration. Following the [conventions](https://docs.docker.com/compose/compose-file/11-extension/) set by `docker-compose`, `cnc` adds two key `x-cnc` extension locations.
- One extension is at the root of the document (sibling to `services`) and is used for app-wide configuration such as build machine type.
- The other is in each `service` itself. The `type` key is the most important one. Supported types depend on the included flavor but the two most common are `frontend` for static site and `backend` for a container.

The goal of this document is to provide:
- A comprehensive example with comments on each line to help understand the possible configuration.
- Instructions on how to see the JSON Schema of all the allowed configuration options, which is auto-generated and can be used for tooling and validation as well as understanding.

# Example

This is an example of a monorepo (cnc does not actually know or care if in a repo or not, but most code is!) with 2 services, one `frontend` and one `backend`, in directories with the same names. `cnc` is run from the repo root for this example.

```yaml
x-cnc:
  build_settings:
    platform_settings:
      # see the cloud provider docs for valid types 
      machine_type: "E2_HIGHCPU_8"
  resources:
  # resources can be defined here or as services, interchangably
  # some resources e.g. message queue or bucket don't always have a server in dev
  # for valid types and options, see flavor docs
  - name: bucket1
    type: object_storage

services:
  # this will become the service name in CNC
  frontend:
    x-cnc:
      # this is required
      type: frontend
      # within this container, where doe built assets end up?
      # we need to know to copy them to the CDN
      assets_path: dist
      # what command do you run in the container to build the assets
      # this is often different than the docker-compose command to run
      # the dev server
      build: ["yarn", "build"]
      # you can define custom headers for your site
      custom_headers:
      - name: x-frame-options
        value: SAMEORIGIN

    build:
      # for this container, where is the Dockerfile
      # if you don't have one defined, the default is 
      # "Dockerfile" in the current working directory
      # if the dockerfile does not exist, included flavors
      # will use nixpacks for the build step to produce a container
      dockerfile: frontend/Dockerfile
      # this can be used to set the docker build context
      context: frontend

  backend:
    command: ["npm start"]

    ports:
    # these are ignored by CNC, your app is expected to listen on $PORT
    # unless you customize the IaC or runtime templates to change behavior
    - "8080:8080"

    deploy:
      # control the resources deployed
      # can also specify different environment type specs e.g. preview or production
      # see worker below for an example
      resources:
        limits:
          memory: 2g
          cpu: 2

    build:
      # see comments in frontend above
      context: backend
      dockerfile: "backend/Dockerfile"

    x-cnc:
      type: backend
      # need to define the url path to route to the service
      # unless you customize IaC to subdomain routing
      url_path: /api
      # for DB migrations, what command to run?
      # runs in the container
      migrate: ["prisma", "migrate"]
      # for DB seeding, what command to run?
      # MUST be idempotent!!
      # runs in the container
      seed: ["prisma", "seed"]

      workers:
      # will run a daemon without LB connection
      - name: default queue
        # what command to run? will run in same container as the service
        command: ["node", "worker.js", "default"]
        # define resources (will default to service if not defined)
        system:
          cpu: 2
          memory: 4g
          x-cnc:
            preview:
              memory: 4g
              cpu: 2

      scheduled_tasks:
      # CRON jobs go here
      - name: check task statuses
        command: ["node", "statuscheck.js"]
        # use k8s syntax for all providers/flavors
        # this is every 2 mins (can be expensive)
        schedule: "*/2 * * * *"

  redis:
    x-cnc:
      # will be merged into resources for the whole app in each environment
      type: cache
    
    # cnc will ignore this and use cloud service e.g. Elasticache
    image: redis
    restart: always

  db1:
    x-cnc:
      name: db1
      type: database
      # any version supported by cloud e.g. RDS on AWS
      version: 13
      # can override protocol in DATABASE_URL here for cnc-managed vars
      adapter: postgresql

    # cnc will ignore this and use cloud service e.g. Elasticache
    image: postgres:13
    restart: always

```