# Customizing provision in your repo

Let's say that in addition to the default ECS resources added to each environment, you also want to add a DynamoDB instance:

## environment.yml custom templates config 

Add this to `environments.yml`:

```yaml
template_config:
  # from root, where do we look for custom templates?
  template_directory: custom
```

## custom template creation

Let's say you want to add a command to run after your docker build and push steps included in the default.

Add `main.sh.j2` into the `deploy` folder in the directory you set as the `template_directoy` in your project.

```sh
{% extends "base.sh.j2" %}

{% block build_commands %}
# this is a jinja function that calls the block you're inheriting from
# you can leave this out if you don't want to default resources for this block
{{ super() }}
echo "hello {{ environment.name }}"
{% endblock %}
```

You could also replace the build entirely and use alternative builders like `depot` if you wanted to.

## block options

This is the default `main.sh.j2` with the available blocks.

```sh
{% extends "base.sh.j2" %}

{# All Available Blocks #}

{# before deploy #}
{# {% block install_commands %} #}
{# {% endblock install_commands %} #}

{# deploy body #}
{# {% block build_commands %} #}
{# {% endblock %} #}

{# post deploy #}
{# {% block finally_build_commands %} #}
{# {% endblock %} #}
```

# Test your changes

Run `cnc deploy perform --debug` and see your new commands in action!