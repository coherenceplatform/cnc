# Customizing CNC 

CNC ships with sever included "flavors." A flavor is a deployable reference architure with a combination of 3 types of files:
- Infra as Code for provisioning and managing cloud infrastructure. These use `terraform`
- `bash` scripts for building 
- `bash` scripts for deploying

If the included flavors are a fit for your application, the good news is that you can use them as-is and don't need to do any work.

If you want to change or customize the files above, you have several options.
- Add customizations to your repo and use the template inheritence system to change parts of the included files
- Completely override the included files with your own templates in your repo
- Contribute a new flavor or edit a flavor by modifying the open-source `cnc` codebase

CNC uses `jinja` templates. See the docs [here](https://jinja.palletsprojects.com/en/3.1.x/).

By providing useful context for each service/environment as well as built-in base templates that implement a variety of options for your deployment, `cnc` gives you the building blocks to create your own deployments, whatever they look like. By building on top of the `cnc` framework, you get the power of well-proven and well-documented abstractions that let you deliver better environments to your team.

Each flavor has 

# Customizing in project

The custom templates directory mirrors a CNC flavor in its folder structure. There is one directory for each phase.

```
- custom folder
    - provision
    - build
    - deploy
```

# Customizing your own flavor in repo

You can create template for provision/build/deploy that do not inherit from the default templates, and thus no default code will be included. You can define any version you like while using the powerful environment/collection abstraction provided by the `cnc` models and the `jinja` template engine, as well as the `cnc` interface.

# Adding your own flavor to CNC

Customize your own flavor in project, give it a name, polish it up, and make a PR to CNC with the code! We'd love to have options for all kinds of different deployments built into CNC.

# Template Context

Each template being rendered gets useful context. 

## Provision

Context in template rendering will look like this, replaced with your values. All environment items including `cnc`-managed ones and all types (`secret`/`output`/`'alias` included) will be present in plain text.

```json
{
    "app": {"name": "appname"},
    "config_renderer": {"environment_items": {"MYVAR1": "foo123"}},
    "env_collection": {"name": "foo123", "cloud_resource_namespace": "23rffw-collection-name", "environments": []}
}
```

## Build & Deploy

Will be called once per service, excluding resource types.

Will be the same, except for the `stage`. e.g.

```
"stage": {"name": "build"}
```

Here's the full context for these templates:

```json
{
    "builder": {"environment_items": {"MYVAR1": "foo123"}},
    "environment": {"name": "foo123", "instance_name": "134fsas-foo123"},
    "service": {
        "type": "backend",
        "is_backend": True,
        "is_frontend": False,
        "deploy": {
            "resources": {
                # these will be formatted based on cloud provider by cnc
                "limits": {"cpu": 2, "memory": "4G"}}},

        # generally you should use this name, will be unique per collection/env/service
        "instance_name": "134fsas-foo123",
        "name": "backend",
        "port": 8080,

        # these will both be present regardless of which format you provide
        "command": ["npm", "start"],
        "joined_command": "npm start",
    },
    "stage": {"name": "build"}
}
```

# `render_template` macro

`cnc` adds a powerful macros that can add new files alongside the one being rendered, e.g.

```
{{ render_template("mytemplate.yml.j2", "outputname.yml") }}
```

Which will add the file `outputname.yml` to the execution context of you script. For example, after rendering, can then call `kubectl apply -f outputname.yml`. The context will be the same as the `main` template being rendered for that command, e.g. `build` or `deploy`.