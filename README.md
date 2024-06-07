<p align="center">
<picture>
  <source srcset="https://cncframework.com/images/cnc_logo_white.svg" media="(prefers-color-scheme: dark)">
  <source srcset="https://cncframework.com/images/cnc_logo_black.svg" media="(prefers-color-scheme: light)">
  <img src="https://cncframework.com/images/cnc_logo_black.svg" alt="cnc logo" width="200" height="auto">
</picture>
</p>

# CNC

## Introduction

`cnc` is an open-source framework that equips developers with the right tools to deploy applications with precision. Rooted in the principles of Infrastructure as Code (IaC) using terraform, `cnc` translates high level service definitions into reference architecture based infrastructure across various environments — whether it’s for development, staging, production, or ephemeral environments. For those who have used AWS's Amplify CLI, think of `cnc` as a broader, adaptable framework that supports your unique deployment needs.

Core Lifecycle Events Managed by `cnc`:

- Provision: Uses terraform to create, manage, and dismantle cloud resources, ensuring each environment is crafted to fit its specific purpose.
- Build: Assembles the necessary deployment artifacts for each environment, from docker containers to static assets for web applications.
- Deploy: Seamlessly updates infrastructure to deploy new artifacts, such as modifying k8s manifests or updating ECS services.
- Toolbox: A `toolbox` is a managed shell against a `cnc`-managed environment, making it easy to get a REPL or run database migrations, for example

Getting Started with `cnc`:

- Experience `cnc` in just a few minutes: install and see for yourself the power of cnc in under 5 minutes without needing any cloud permissions or incurring any costs.
- Rapid Deployment: Have your first environment up and running in less than 15 minutes, demonstrating the straightforward power of cnc.

`cnc` is designed to be a powertool that empowers you to build and manage your infrastructure with the same attention to detail and creativity that you bring to your code. Just like web devs use frameworks to build better products, with `cnc`, you gain the freedom to implement your vision precisely as intended, making each project not only functional but finely tuned to your standards.

## Hello World

### Install CNC

Intall `cnc` from the [PyPI Python Package Index](https://pypi.org/project/cocnc/). For example, using `pip`:
```
pip install cocnc
```

### Save config files

You can make a new directory, nothing but the following 2 files is needed by `cnc`. Save as `cnc.yml`:

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

Save as environments.yml:

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

`cnc` has robust environment configuration options, including support for environment variables from cloud secrets, terraform outputs, or aliasing from other variables. Read more about configuration [here](https://cncframework.com/configuration/overview/).


### See CNC in action

All this will do is manipulate text files in your `/tmp` directory and won't actually touch anything in your code or cloud. It's the best way to get to `Aha!` quickly before diving in deeper.

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

# Documentation

Access full documentation and in-depth tutorials at [the CNC Documentation](https://cncframework.com).

# Community & Support

- Issues: Report bugs or suggest features via GitHub Issues.
- Support: For direct support, contact our team at cnc@withcoherence.com.

# Contributing

Interested in contributing to CNC? Check out our Developers Getting Started guide for guidelines and project setup instructions.
