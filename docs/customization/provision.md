# Customizing provision in your repo

Let's say that you're using the AWS ECS flavor, and in addition to the default ECS resources added to each environment, you also want to add a DynamoDB instance:

## environment.yml custom templates config 

Add this to `environments.yml`:

```yaml
template_config:
  # from root, where do we look for custom templates?
  template_directory: custom
```

## custom template creation

Add your custom `main.tf.j2` (you can also set a different filename) into the `provision` folder in the directory you set as the `template_directoy` in your project.

```
{% extends "base.tf.j2" %}

{% block environment_resources %}

# this is a jinja function that calls the block you're inheriting from
# you can leave this out if you don't want to default resources for this block
{{ super() }}

resource "aws_dynamodb_table" "{{ environment.instance_name }}-basic-dynamodb-table" {
  name           = "{{ environment.instance_name }}-GameTitle"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "UserId"
  range_key      = "GameTitle"

  attribute {
    name = "UserId"
    type = "S"
  }

  attribute {
    name = "GameTitle"
    type = "S"
  }

  attribute {
    name = "TopScore"
    type = "N"
  }

  ttl {
    attribute_name = "TimeToExist"
    enabled        = false
  }

  global_secondary_index {
    name               = "GameTitleIndex"
    hash_key           = "GameTitle"
    range_key          = "TopScore"
    write_capacity     = 10
    read_capacity      = 10
    projection_type    = "INCLUDE"
    non_key_attributes = ["UserId"]
  }
}

output "dynamo-{{ environment.instance_name }}-address" {
  value = aws_dynamodb_table.{{ environment.instance_name }}.address
}

{% endblock environment_resources %}

```

- Note that default tagging is enabled automatically just like managed resources.
- You can now add an environment variable to your coherence app called "dynamo-{{ environment.instance_name }}-address" and reference this value from your app code.

The block in the example above runs for each environment. These are the default blocks (this is the content of a default`main.tf.j2`). Your own template can have its own blocks and partials as well as content outside blocks entirely:

```yaml
{% extends "base.tf.j2" %}

{# All Available Blocks #}

{# Env collection level resource #}
{# {% block application %} #}
{# {% endblock application %} #}

{# Per active environment #}
{# {% block environment_resources %} #}
{# {% endblock environment_resources %} #}

{# Per active service #}
{# {% block service_resources %} #}
{# {% endblock service_resources %} #}

{# Per active|paused environment #}
{# {% block active_and_paused_envs %} #}
{# {% endblock active_and_paused_envs %} #}

{# Custom tf #}
{# {% block custom %} #}
{# {% endblock custom %} #}
```

# Test your changes

Run `cnc provision debug` or `cnc provision plan` and see your new resources in action!