# Developing your own flavor

We welcome new flavors to the `cnc` project. Here's how we suggest you develop them.

## Plan your flavor

Make sure that it makes sense to be adding a flavor vs. modifying the exsting ones or customizing in your own project.

A flavor should be a holistic reference architecture that uses a set of cloud services in convert to achieve a certain set of trade-offs between: cost, comliance, secutiry, complexity. For example, here are different flavors on AWS:

- VPC / ECS / RDS / ALB
- VPC / k8s / RDS / ALB
- VPC / lambda / dynamodb
- App Runner / RDS

Within these flavors, you might want to change RDS settings to use cluster/HA or not, or to configure connection security. These would be good use cases for options added to the `x-cnc` configuration for that flavor, or for customization in your own project, depending on if you see value for others in what you are doing.

## The development loop

The right way to develop a `cnc` flavor is to:

- Copy the directory for an existing one in the same cloud provider and rename it to your new flavor name
- Add partials to overwrite the shared ones as needed, and remove/replace the flavor-specific parts as needed
- Add a simple `environments.yml` and `cnc.yml` that use the service types you're developing. The focus here is on MVP amount of config to test your flavor, not actually usable configs. Use `cnc provision debug`, `cnc build perform --debug`, `cnc deploy perform --debug` to view the configs your flavor is generating, or to see any errors in your templates
- When the IaC, build, and deploy scripts all look good, can test deploing them to a test project in your cloud (remove the `--debug`)
- Add tests to `cnc` for any new service types or cases you add to the code, if you change any app code (outside the `flavors` directory)
- For the repo to create a branch, and then submit a PR to this repo
