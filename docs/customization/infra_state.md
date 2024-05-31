# TF State Customization

By default, [terraform state](https://developer.hashicorp.com/terraform/language/state) will be stored in the `.terraform` directory wherever you run `cnc`. Usually this would be your project root. 

This is not optimal for a few reasons:
- If you lost the directory, you'd lose the state, and possibly lose track of cloud resources
- You cannot share the state with other members of your project with this configuration or run the `provision` step from CI/CD (you can always run `build` or `deploy` but variables that reference state will not resolve properly)

If you want to change the state location, it's easy to use any state backend, just like plain `terraform`.

# Customizing the state backend

As with other `provision` customizations, you add this to `environments.yml`:

```yaml
template_config:
  # from root, where do we look for custom templates?
  template_directory: custom
```

Put this in `main.tf.j2` in the `provision` folder in the `template_directory`.

```yaml
{% extends "base.tf.j2" %}

{% block state %}
terraform {
  backend "s3" {
    bucket  = "my-tf-state-bucket"
  }
}
{% endblock %}
```