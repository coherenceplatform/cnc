# CNC Command Line Interface (CLI)

## Installation
```
pip install cocnc
```

## Global Options
- `--config-file-path, -f`: Specify CNC config file path
- `--environments-file-path, -e`: Specify environments data file path

## Commands Overview

- provision
- build
- deploy
- update
- info
- shell
- toolbox
- inspector

## Detailed Command Usage

### provision
Manage infrastructure provisioning.

#### Arguments

- `collection_name`: the name of the collection to target

#### Subcommands:
- `plan`: Generate an infrastructure plan
  ```
  cnc provision plan [--cleanup] [--generate]
  ```
- `apply`: Apply an infrastructure plan
  ```
  cnc provision apply [--cleanup] [--generate] [--update-environments]
  ```
- `debug`: Debug an infrastructure plan. Usually you would run this and inspect the output `.tf` files.
  ```
  cnc provision debug [--cleanup] [--generate]
  ```
- `cmd`: Run an infrastructure command in the CLI
  ```
  cnc provision cmd <tf_cmd>...
  ```

    This subcommand allows you to run any Terraform command directly through the CNC CLI. Here are some examples:

    - Destroy infrastructure:
      ```
      cnc provision cmd destroy
      ```
    - Run Terraform commands with flags:
      ```
      cnc provision cmd -- destroy --target some_resource.resource_name
      ```
    - Import existing resources:
      ```
      cnc provision cmd import aws_vpc.main vpc-1234567890abcdef0
      ```

  You can use `cnc provision cmd` to run any Terraform commands you'd like, giving you full flexibility in managing your infrastructure. Note: Use `--` before passing any flags to Terraform.

### build
Build containers for config-defined services.

```
cnc build perform <environment_name> [--service-tag <service>=<tag>]... [--default-tag <tag>] [--collection-name <name>] [--cleanup] [--debug] [--generate] [--webhook-url <url>] [--webhook-token <token>] [--parallel]
```

### deploy
Deploy built containers to the specified environment.

```
cnc deploy perform <environment_name> [--service-tag <service>=<tag>]... [--default-tag <tag>] [--collection-name <name>] [--cleanup] [--debug] [--generate] [--webhook-url <url>] [--webhook-token <token>]
```

### update
Perform both build and deploy operations.

```
cnc update perform <environment_name> [--service-tag <service>=<tag>]... [--default-tag <tag>] [--collection-name <name>] [--cleanup] [--debug] [--generate]
```

### info
Display information about the CNC configuration.

#### Subcommands:
- `version`: Show CNC version
  ```
  cnc info version
  ```
- `app`: Show application info
  ```
  cnc info app
  ```
- `environments`: List environments
  ```
  cnc info environments [--collection-name <name>]
  ```
- `services`: List services for an environment
  ```
  cnc info services <environment_name> [--collection-name <name>]
  ```

### shell
Start an interactive Python shell with CNC context.

```
cnc shell start
```

### toolbox
Manage development toolboxes for environments.

#### Subcommands:
- `start`: Start a toolbox session
  ```
  cnc toolbox start <environment_name> [--service-name <name>] [--tag <tag>] [--proxy-only]
  ```
- `run`: Run a command in a toolbox
  ```
  cnc toolbox run <environment_name> [--service-name <name>] [--tag <tag>] -- <command>...
  ```

### inspector
Inspect and analyze CNC templates.

```
cnc inspector list <template_path> [--collection-name <name>] [--template-type <type>]
```

## Environment Variables
- `CNC_CONFIG_PATH`: Path to the CNC config file
- `CNC_ENVIRONMENTS_PATH`: Path to the environments data file
- `CNC_DEFAULT_TAG`: Default tag for services
- `AWS_PROFILE`: AWS profile to use (if using AWS provider)

## Examples

Provision infrastructure:
```
cnc provision apply
```

Build and deploy a specific service:
```
cnc update perform dev --service-tag backend=v1.2.3
```

Start a toolbox session:
```
cnc toolbox start staging --service api
```

Run a migration in a toolbox:
```
cnc toolbox run prod --service db -- python manage.py migrate
```

View environment information:
```
cnc info environments
```

## Working with Existing Resources

CNC provides flexibility in working with both new and existing infrastructure:

1. For supported resources like AWS VPC, CNC uses Terraform data resources to reference existing infrastructure without managing it directly.

2. For resources not yet supported by CNC, you can:
   - Add custom Terraform templates in a [custom directory](/customization/provision/)
   - Import existing resources using `cnc provision cmd import...`

3. You can further customize your Terraform configurations to dynamically create resources per environment or per service.

This approach allows you to integrate existing infrastructure with CNC-managed resources and provides a path for customization as needed.