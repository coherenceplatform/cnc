<p align="center">
<picture>
  <source srcset="/images/cnc_logo_white.svg" media="(prefers-color-scheme: dark)">
  <source srcset="/images/cnc_logo_black.svg" media="(prefers-color-scheme: light)">
  <img src="cnc_logo_black.svg" alt="cnc logo" width="200" height="auto">
</picture>
</p>

# CNC

## Introduction

`cnc` is a framework for precision cloud engineering. Rooted in the principles of Infrastructure as Code (IaC) using terraform, `cnc` translates high level service definitions into reference architecture based infrastructure across various environments — whether it’s for development, staging, production, or ephemeral environments. If you're looking to do "platform engineering" but hitting `curl` to a huge helm install (whether open-source or not) in an expensive k8s cluster has not solved your problems, `cnc` just might be something interesting to add to your stack. 

As a purely CLI-based and agentless tool with simple configuration and sane defaults, `cnc` can run everywhere from on your local machine to complex hosted CI/CD infra. Our philosophy is to be lightweight, powerful, and to function as a force multiplier for engineers who need to manage and perform deployments. 

`cnc` works by translating `docker-compose` into IaC files, artifact (docker/lambda/etc) build scripts, and deployments scripts. It has a set of smart script runners that allow you to use high-level environment configuration concepts in a sane way across all these environments seamlessly. You can view, edit, and debug the framework outputs easily. At [Coherence](withcoherence.com) we've spent years building this kind of software, and `cnc` represents our effort to make this more useful for both our customers and the community at large. Try it in 5 minutes below!

Core Lifecycle Events Managed by `cnc`:

<p align="center">
<picture>
  <source srcset="/images/cnc_diagram_light.png" media="(prefers-color-scheme: light)">
  <source srcset="/images/cnc_diagram_dark.png" media="(prefers-color-scheme: dark)">
  <img src="/images/cnc_diagram_light.png" alt="cnc diagram" width="auto" height="auto">
</picture>
</p>

- Provision: Uses terraform to create, manage, and dismantle cloud resources, ensuring each environment is crafted to fit its specific purpose.
- Build: Assembles the necessary deployment artifacts for each environment, from docker containers to static assets for web applications.
- Deploy: Seamlessly updates infrastructure to deploy new artifacts, such as modifying k8s manifests or updating ECS services.
- Toolbox: A `toolbox` is a managed shell against a `cnc`-managed environment, making it easy to get a REPL or run database migrations, for example

Getting Started with `cnc`:
- Experience `cnc` in just a few minutes: install and see for yourself the power of cnc in under 5 minutes without needing any cloud permissions or incurring any costs.
- Rapid Deployment: Have your first environment up and running in less than 15 minutes, demonstrating the straightforward power of cnc.

`cnc` is designed to be a powertool that empowers you to build and manage your infrastructure with the same attention to detail and creativity that you bring to your code. Just like web devs use frameworks to build better products, with `cnc`, you gain the freedom to implement your vision precisely as intended, making each project not only functional but finely tuned to your standards.

## Getting Started

### Prerequisites

Ensure that you have Docker installed, along with the `aws` or `gcloud` CLI tools, depending on your cloud provider.

Intall `cnc` from the [PyPI Python Package Index](https://pypi.org/project/cocnc/). For example, using `pip`:
```
pip install cocnc
```

### Annotate docker-compose.yml or add cnc.yml

Mark the services that CNC should manage by adding the following snippet to your `docker-compose.yml`. You can annotate a subset of your existing `docker-compose.yml`, `cnc` will ignore services without the `x-cnc` extension. The default filename `cnc` looks for is `cnc.yml` so if you use `docker-compose.yml`, append the `-f docker-compose.yml`

```yaml
x-cnc:
  type: backend
```

If you want a simple example just to see `cnc` in action below, you can use this, save as `cnc.yml`:

```yaml
services:
  app:
    command: "my command"
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

### Create environments.yml

Define your application environment and specify cloud settings in environments.yml:

```yaml
name: my-first-app
provider: gcp
flavor: run-lite
version: 1

collections:
- name: dev
  region: us-east1
  base_domain: mydevsite.com
  account_id: "foo-bar-123"
  environments:
  - name: dev
    environment_variables:
    - name: FOO
      value: bar
```

`cnc` has robust environment configuration options, including support for environment variables from cloud secrets, terraform outputs, or aliasing from other variables. Read more about configuration [here](./docs/README.md).


### See what CNC is doing

All this will do is manipulate text files in your `/tmp` directory and won't actually touch anything in your code or cloud. It's the best wayt to get to `Aha!` quickly before diving in deeper.

```
# print the terraform we would run, as generated from the 2 ymls above
# we do --no-cleanup here so you can inspect the files yourself in /tmp if you want to.
# You can leave this off to cleanup after the command runs automatically
cnc provision debug --no-cleanup

# look at the generated build script
# you can look at the files referenced, for example the build-functions scripts, by going to the /tmp path in your terminal
cnc build perform dev --debug --no-cleanup

# same for deploy
cnc deploy perform dev --debug --no-cleanup
```

Add a 2nd environment (e.g. `dev2`) to the `environments.yml` and run the commands again, see the power of the framework!

### Deploy your first environment

Authenticate with your cloud provider using the aws or gcloud CLI, then create your infrastructure with:

```
cnc provision apply
```

deploy your `dev` environment with:
```
cnc update dev --service-tags app=v1
```

This will do a `build` and a `deploy` under the hood.

For more details, see the step-by-step [Getting Started Guide](./docs/README.md).


# Documentation

Access full documentation and in-depth tutorials at [the CNC Documentation](./docs/README.md).

# Community & Support

- Issues: Report bugs or suggest features via GitHub Issues.
- Support: For direct support, contact our team at cnc@withcoherence.com.

# Contributing

Interested in contributing to CNC? Check out our Developers Getting Started guide for guidelines and project setup instructions.
