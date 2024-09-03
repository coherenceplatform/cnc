# Getting Started

## Introduction
This guide covers the installation of the CNC framework and the necessary cloud CLI tools. CNC simplifies deploying applications to the cloud by utilizing infrastructure as code principles.

### Prerequisites

- Access to a terminal
- Python 3.9-3.11 installed on your machine
- Cloud provider account (AWS `aws` or Google Cloud `gcloud`) and authenticated CLI
- `docker`
- `terraform`
- `jq`
- (MacOS-Only): The `setsid` shell command is required but not included in MacOS. Run `brew install util-linux`, and follow the instructions in the output to add the resulting commands to your shell PATH.

## Installation Steps

### Install CNC
```
pip install cocnc
```

### Docker

We also offer a `docker` image with all of this installed, `us-docker.pkg.dev/coherence-public/public/cnc:latest`. You'll need to handle authenticating the cloud CLI as well as mounting the local docker socket with `-v` to use it. Better instructions here coming soon!

### Install and authenticate cloud CLI:

This would be either the `aws` or `gcloud` CLI. Read more at [aws](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) or [gcp](https://cloud.google.com/sdk/docs/install).

For google:

You need to do both of these.

```
gcloud auth application-default login
gcloud auth login
```

For AWS:

Choose the appropriate one.

```
aws configure // aws sso configure
```

### Setup CNC configuration files

## cnc.yml

The CNC config is a superset of docker-compose that adds one required key, the `type` in `x-cnc`. See the full schema and options [here](). If you have an existing docker-compose file, you can add the `x-cnc` options to it and use the same file without renaming by passing the `--config-file` option to `cnc` when running commands.

Here's a simple example that will produce one container-running service in your cloud called `app` using a `Dockerfile` at the project root.

```
services:
  app:
    x-cnc:
      type: backend
    build:
      context: .
```

## environments.yml

The `environments.yml` file defines your environments and their configuration, including environment variables and URLs. You can define many `collections`, each of which can live in its own cloud account (making it easy to segregate different environment types). Read more about the different options and see a full example [here](./configuration/environments.md).

This example produces one environment at `dev.mydevsite.com` running in the GCP project `foo-bar-123` using the built-in infra as code and build/deploy scripts in the `run-light` flavor. Read more about CNC flavors [here](./flavors/README.md).

```
name: my-first-app
provider: gcp
region: us-east1
flavor: run-lite
version: 1
collections:
- name: dev
  account_id: "foo-bar-123"
  environments:
  - name: dev
    environment_variables:
    - name: FOO
      value: bar
    - name: MY_API_KEY
      # you add this secret directly to your cloud account directly
      secret_id: my-secret-123
```

If you use [Coherence](withcoherence.com) cloud, you don't need to manage the `environments.yml` file yourself, the SaaS protal will manage it for you.

The `run-light` flavor will be the cheapest and fastest way to get started with deploying a `cnc` application: it uses GCP Cloud Run for a serverless and [free](https://cloud.google.com/run/pricing) deployment that fits many common applications.

# Deploy your first environment

## Provision the infrastructure

If you are using `aws sso` for your credentials locally, you'll need to set `AWS_PROFILE=PROFILE_NAME` in your environment.

```
cnc provision plan
```

This will show you the terraform plan. You can view the raw terraform that was compliled with:
```
cnc provision debug
```

And then you can apply the changes with:

```
cnc provision apply
```

This will create the cloud resources for your environment. The `terraform` state for this infra will be stored in `.terraform` in your working directory, just as if you'd used `terraform` directly. You can customize the state location, along with the terraform `hcl` that is generates, read more [here](./customization/infra_state.md).

You can now run `cnc info environments` to see information about the configured infrastructure, including the URL of the service.

Now, set the DNS records as required by your `base_domain` setting. This does not apply to some flavors, e.g. can ignore for `run-lite`. See flavor docs [here](/flavors/overview/) for more. Run `cnc info app` and then:

- For GCP, copy the `Load Balancer IP` and set a `CNAME` in your DNS provider for `*.yourbasedomain.com` to that IP
- For AWS, copy the `NS` records and set on `*.yourbasedomain.com` in your DNS provider

Sometimes, you'll see errors that a service is not enabled or a quota was not available. If your cloud account is new, in most cases these errors will resolve in a few minutes and you can try again.

## Deploy the container

You can customize the scripts that run for build/deploy using a Jinja2 template, read more [here](/customization/overview/).

### Build the docker image

This will build the docker image locally and push it to the container registry created automatically.

```
# dev is the environment name in environment.yml
cnc build perform dev --service-tag app=v1
```

Subsequent builds will get faster as they re-use the docker cache.

### Deploy the docker image

This will render new runtime templates (e.g. Cloud Run/ECS/k8s.yml) and apply them to the right clusters/services.

```
# dev is the environment name in environment.yml
cnc deploy perform dev --service-tag app=v1
```

### Build & Deploy

There is an `update` command to make the build/deploy cycle easier.

```
# dev is the environment name in environment.yml
cnc update perform dev --service-tag app="$(date +%s)"
```

For `build`, `update` and `deploy` you can pass `--service-tag SERVICE_NAME=TAG` and `--service SERVICE_NAME`. git SHA is a great `TAG`, the default is `latest`. If you do not specify any `--service`, will perform for all services in the config. The `-t` flag is a shortcut for `--service-tag`.

### Get a shell in the environment

This will start a new container on the local machine, with the right environment variables a VPC proxy setup. It will use `gcloud ssh` or `aws ssm` under the hood to reverse proxy into your VPC.

```
# dev is the environment name in environment.yml
cnc toolbox start dev
```

You can now run your REPL or anything else you need to do! Read more at [toolboxes](./toolboxes.md)

### Cleaning Up an Environment

To delete the infrastrucuture managed by `cnc`, use the `provision` subcommand `cmd` to call `terraform destroy` on the collection.

- Destroy infrastructure:
      ```
      cnc provision cmd destroy --collection-name MYCOLLECTION
      ```