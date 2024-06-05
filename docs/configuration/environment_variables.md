# Environment Variables Info

Variables are defined in `environments.yml`. Each environment defines its own variables. You can use [YAML Anchors](https://support.atlassian.com/bitbucket-cloud/docs/yaml-anchors/) to re-use the same variables across many environments.

## Types

- `standard` where the `value` is defined
- `secret` where the `secret_id` is provided. `cnc` will not create this secret, you create it in your cloud and `cnc` will populate appropriately in the app's lifecycle
- `output` where a `terraform` output value is referenced. See the bottom for useful info on output name templating.
- `alias` where a value references another variable's value. This can be useful if and application requires multiple values or when migrating between 2 values. It's especially useful for `cnc`-managed variables

## CNC Managed

Certain values such as environment name are automatically provided by `cnc`. These are:

- `CNC_APPLICATION_NAME`
- `CNC_ENVIRONMENT_NAME`
- `CNC_ENVIRONMENT_DOMAIN`

Additionally, if resources such as database are configured, you'll see variables:

- `DB_PASSWORD`
- `DATABASE_URL`
- `REDIS_URL`
- `...` more, check the code for now to see them all...

# Example

```yaml
  environments:
  - name: dev

    # cnc also adds "managed" variables e.g. domain/environment/resource info
    environment_variables:
    # see the environment variable docs for more
    - name: FOO
      value: bar

    # this will reference a secret ID in the cloud
    # cnc will not create this secret, you create it
    # see flavor docs for secret format
    - name: FOO_SECRET
      secret_id: bar123

    # reference any terraform output
    # see flavor docs for available outputs
    - name: FOO_OUTPUT_1
      output_name: bar123-a
    
    # alias another variable name add another copy with a new name
    # you can alias any variable type
    - name: FOO_OTHER_ALIAS_NAME
      alias: foo-standard
```


# Output Name Templating

You can use `environment.name` and `collection.name` in the output names you reference, for example:

```
    - name: foo-output
      output_name: "{{ environment.name }}-a"
```

For an environment named `dev` this will result in: `dev-a` as the `output` which `cnc` will pull from `terraform`.