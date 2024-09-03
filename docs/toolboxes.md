# CNC Toolboxes

A `toolbox` in CNC is a powerful feature that allows you to interact with your CNC-managed environments directly. It provides a way to run commands or start an interactive shell within the context of your application's environment, complete with all the necessary configurations and connections.

## What is a Toolbox?

A toolbox is a managed shell or command execution environment that:

1. Runs against a specific CNC-managed environment
2. Provides access to all environment variables and secrets configured for that environment
3. Sets up necessary network connections (e.g., VPC proxies) to access cloud resources
4. Uses the same container image as your deployed service

This makes it easy to perform tasks like running database migrations, starting a REPL, or executing maintenance scripts in an environment that closely mirrors your production setup.

## Using Toolboxes

### Starting a Toolbox

To start an interactive toolbox session:

```bash
cnc toolbox start <environment-name> [--service-name <service-name>]
```

For example:

```bash
cnc toolbox start dev --service-name backend
```

This will start an interactive shell in the container for the `backend` service in the `dev` environment.

### Running a Command

To run a specific command in a toolbox:

```bash
cnc toolbox run <environment-name> [--service-name <service-name>] -- <command>
```

For example:

```bash
cnc toolbox run dev --service-name backend -- python manage.py migrate
```

This will run the Django migration command in the `backend` service of the `dev` environment.

### Proxy-Only Mode

If you only need to set up port forwarding to cloud resources without starting a container:

```bash
cnc toolbox start <environment-name> --service-name <service-name> --proxy-only
```

This is useful when you want to connect to cloud resources from your local machine using local tools.

## Features

- **Environment Variables**: All environment variables defined for the service in the specified environment are automatically available in the toolbox.
- **Cloud Resource Access**: The toolbox sets up necessary VPC proxies or port forwarding to allow access to cloud resources like databases or caches.
- **Consistent Environment**: The toolbox uses the same container image as your deployed service, ensuring consistency between your toolbox environment and the actual deployed environment.
- **Cloud Provider Integration**: Uses cloud-specific tools (e.g., `gcloud ssh` for GCP, `aws ssm` for AWS) to set up secure connections.

## Use Cases

1. **Database Migrations**: Run database migration scripts in a controlled environment.
2. **REPL Sessions**: Start an interactive Python, Node.js, or other language REPL with full access to your application's environment.
3. **Debugging**: Investigate issues by running commands in an environment identical to your deployed services.
4. **Data Management**: Perform data import/export operations or run data manipulation scripts.
5. **Maintenance Tasks**: Execute periodic maintenance tasks or one-off scripts.

## Best Practices

1. Use toolboxes for temporary interactive access. For recurring tasks, consider using scheduled tasks in your CNC configuration.
2. Be cautious when running commands that modify data, especially in production environments.
3. Use the `--proxy-only` mode when you only need to access cloud resources and don't require the full application environment.
4. Remember that changes made in a toolbox session (except for persistent storage like databases) will not affect the actual deployed services.

## Limitations

- Toolbox sessions are temporary and do not persist. Any files or changes made within the container (outside of connected persistent storage) will be lost when the session ends.
- Resource limits for toolbox sessions may differ from your deployed services. Check your CNC configuration for specific limits.

By leveraging CNC toolboxes, you can significantly simplify your development and operations workflows, providing a consistent and secure way to interact with your cloud environments.