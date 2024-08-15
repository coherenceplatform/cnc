# ECS Customization

For the `ecs` flavor of `cnc`, ultimately one or more ECS Fargate tasks is created in each environment for each service.

You can customize the task definition (you can also do the same thing for any other file in the repo...). For example, here's the default ECS task JSON Jinja template (lives in the repo at `provision/ecs_web_task.json.j2` in the flavor):

```json
{
    "family": "{{ task_name }}",
    "cpu": "{{ service.deploy.resources.limits.cpu }}",
    "memory": "{{ service.deploy.resources.limits.memory }}",
    "requiresCompatibilities": ["FARGATE"],
    "networkMode": "awsvpc",
    "taskRoleArn": "{{ environment.collection.task_execution_role_arn }}",
    "executionRoleArn": "{{ environment.collection.task_execution_role_arn }}",
    "containerDefinitions": [
        {
            "name": "{{ service.instance_name }}",
            "image": "{{ service.image_for_tag(deployer.tag_for_service(service.name) or 'latest') }}",
            "ulimits": [
                {
                    "name": "nofile",
                    "hardLimit": 65535,
                    "softLimit": 65535
                }
            ],
            {% if command %}
            "entryPoint": ["sh"],
            "command": [
                "-c",
                "{{ command }}"
            ],
            {% endif %}
            {% if expose_ports %}
            "portMappings": [
                {
                    "containerPort": 8080,
                    "hostPort": 8080
                }
            ],
            {% endif %}
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "{{ service.instance_name }}",
                    "awslogs-region": "{{ environment.collection.region }}",
                    "awslogs-stream-prefix": "{{ service.log_stream_prefix('web') }}"
                }
            },
            "secrets": [
                {% for item in service.environment_secrets %}
                {
                    "name": "{{ item.name }}",
                    "valueFrom": "arn:aws:secretsmanager:{{ environment.collection.region }}:{{ environment.collection.account_id }}:secret:{{ item.secret_id }}"
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ],
            "environment": [
                {
                    "name": "PORT",
                    "value": "8080"
                }{% if service.environment_variables %},{% endif %}
                {% for item in service.insecure_environment_items %}
                {
                    "name": "{{ item.name }}",
                    "value": {{ item.value | tojson }}
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ]
        }
    ]
}
```

# Adding Datadog Sidecar

One common use would be adding APM sidecars. You coulod do similar for any other provider or OSS project. What you would do is:

Add this to `environments.yml`:

```yaml
template_config:
  # from root, where do we look for custom templates?
  template_directory: custom
```

Add this in `provision/ecs_web_task.json.j2` in the `custom` directory. This will overwrite the flavor default that you can see above.

```json
{
    "family": "{{ task_name }}",
    "cpu": "{{ service.deploy.resources.limits.cpu }}",
    "memory": "{{ service.deploy.resources.limits.memory }}",
    "requiresCompatibilities": ["FARGATE"],
    "networkMode": "awsvpc",
    "taskRoleArn": "{{ environment.collection.task_execution_role_arn }}",
    "executionRoleArn": "{{ environment.collection.task_execution_role_arn }}",
    "containerDefinitions": [
        {
            "name": "{{ service.instance_name }}",
            "image": "{{ service.image_for_tag(deployer.tag_for_service(service.name) or 'latest') }}",
            "ulimits": [
                {
                    "name": "nofile",
                    "hardLimit": 65535,
                    "softLimit": 65535
                }
            ],
            {% if command %}
            "entryPoint": ["sh"],
            "command": [
                "-c",
                "{{ command }}"
            ],
            {% endif %}
            {% if expose_ports %}
            "portMappings": [
                {
                    "containerPort": 8080,
                    "hostPort": 8080
                }
            ],
            {% endif %}
            "logConfiguration": {
                "logDriver": "awsfirelens",
                "options": {
                    "Name": "datadog",
                    // you set this as a variable or secret in cnc environments.yml
                    "apikey": "{{ environment_items.MY_DD_API_KEY_VAR }}",
                    // change this to yours in dd dashboard
                    "Host": "http-intake.logs.us.datadog.com",
                    "dd_service": "{{ service.instance_name }}",
                    "dd_source": "{{ service.log_stream_prefix('web') }}",
                    "dd_message_key": "log",
                    "dd_tags": "project:fluentbit,env:{{ environment.name }},version:{{ deployer.tag_for_service(service.name) or 'latest' }}",
                    "TLS": "on",
                    "provider": "ecs"
                }
            },
            "secrets": [
                {% for item in service.environment_secrets %}
                {
                    "name": "{{ item.name }}",
                    "valueFrom": "arn:aws:secretsmanager:{{ environment.collection.region }}:{{ environment.collection.account_id }}:secret:{{ item.secret_id }}"
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ],
            "environment": [
                {
                    "name": "DD_VERSION",
                    "value": "{{ deployer.tag_for_service(service.name) or 'latest' }}"
                },
                {
                    "name": "DD_ENV",
                    "value": "{{ environment.name }}"
                },
                {
                    "name": "PORT",
                    "value": "8080"
                }{% if service.environment_variables %},{% endif %}
                {% for item in service.insecure_environment_items %}
                {
                    "name": "{{ item.name }}",
                    "value": {{ item.value | tojson }}
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ]
        },
        {
            "name": "datadog-agent",
            "image": "public.ecr.aws/datadog/agent:latest",
            // add vars or secrets as needed
            "portMappings": [
                {
                    "hostPort": 8125,
                    "protocol": "udp",
                    "containerPort": 8125
                },
                {
                    "hostPort": 8126,
                    "protocol": "tcp",
                    "containerPort": 8126
                }
            ],
            "environment": [
                {
                    "name": "ECS_FARGATE",
                    "value": "true"
                },
                {% for item in service.filtered_environment_items(pattern="^DD_", variable_type="standard") %}
                {
                    "name": "{{ item.name }}",
                    "value": "{{ item.value }}"
                },
                {% endfor %}
                {% if not service.filtered_environment_items(pattern="^DD_VERSION$") %}
                {
                    "name": "DD_VERSION",
                    "value": "{{ environment.config_commit_sha }}"
                },
                {% endif %}
                {% if not service.filtered_environment_items(pattern="^DD_ENV$") %}
                {
                    "name": "DD_ENV",
                    "value": "{{ environment.name }}"
                },
                {% endif %}
                {
                    "name": "DD_DOGSTATSD_NON_LOCAL_TRAFFIC",
                    "value": "true"
                },
                {
                    "name": "DD_APM_ENABLED",
                    "value": "true"
                },
                {
                    "name": "DD_APM_NON_LOCAL_TRAFFIC",
                    "value": "true"
                }
            ]
        },
        {
            "name": "log_router",
            "image": "amazon/aws-for-fluent-bit:stable",
            "firelensConfiguration": {
                "type": "fluentbit",
                "options": { "enable-ecs-log-metadata": "true" }
            }
        }
    ]
}
```

If you haven't installed it already, there are instructions for setting up the datadog <=> aws integration [here](https://docs.datadoghq.com/getting_started/integrations/aws/#setup). The integration allows datadog to pull metrics from aws and enables various additional features.
