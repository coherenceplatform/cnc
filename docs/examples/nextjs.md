# Deploying NextJS to AWS using CNC

We are going to deploy a next app to ECS using the built-in `ecs` flavor. Read more about it [here](../flavors/aws/ecs.md).

Before starting, follow the steps at [Getting Started](../README.md). If you are using `aws sso` for your credentials locally, you'll need to set `AWS_PROFILE=PROFILE_NAME` in your environment.

## repo setup 

You've created a `Next` app with `create-next-app` e.g. see https://github.com/coherenceplatformdemos/nextjs-cnc-demo1

## cnc.yml

You add this to `cnc.yml`

```yaml
services:
  app:
    command: "my command"
    x-cnc:
      type: backend
    build:
      context: .
```

## environments.yml

You add this to `environments.yml`

```yaml
name: my-next-app
provider: aws
flavor: ecs
version: 1

collections:
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

## Provision your infra

- run `cnc provision apply`. confirm with `yes` when requested by terraform, and then wait for the infra to provision. should take just a few minutes. the only thing this will create is the NS records zone for your base domain. you only need to do this once per collection, and then can add as many environments as you like under that domain without waiting for this again or touching DNS settings again.
- run `cnc info environments` and grab the `NS` records to set for your DNS provider for the domain you set in `base_domain` above.
- after applying those NS records to your provider, run `cnc provision apply`. confirm with `yes` when requested by terraform, and then wait for the infra to provision, should take longer than the first time perhaps 10 mins or so.

## Deploy your app

- run `cnc update perform staging --service-tag app=v1`. you can set `v1` to whatever you want to use for the release tag, usually the `git` SHA is a good choice here, can get that with `git rev-parse --short HEAD`.
- the first deploy will take the longest, once this runs once locally building the images will be faster due to docker cache in subsequent runs.
    - you can also run this step from CI/CD e.g. github actions once it works for you and you want to automate it

## visit the URL

- run `cnc info environments` again, and visit the URL for your `staging` environment.

## Next steps

- add another environment
- customize your terraform
- add additional services
- explore the toolbox