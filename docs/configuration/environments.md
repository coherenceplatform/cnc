# The CNC environments file

`cnc` uses a `yml` file to define environments that it should provision, build, and deploy. Here's a commented example:

```yaml
# name of your app
name: my-first-app

# which cloud provider? gcp or aws
provider: gcp

# OPTIONAL, can define on each collection instead
region: us-east1

# which flavor
# see the flavors docs
# you can add your own flavor in your repo as well
flavor: run-light

# version of the flavor
version: 1

# OPTIONAL: used if customizing
# see customization docs for more info
template_config:
  # from root, where do we look for custom templates?
  template_directory: custom
  # OPTIONAL, defaults to main.tf.j2
  provision_filename: "mymaintf.tf.j2"
  # OPTIONAL, defaults to main.sh.j2
  deploy_filename: "mydeployscript.sh.j2"
  # OPTIONAL, defaults to main.sh.j2
  build_filename: "mybuildscript.sh.j2"

# you can have many collections
collections:
# name of the collection
- name: dev
  # each environment in the collection will get a subdomain of this base_domain
  # OPTIONAL: will default to cloud-provided URL if not defined
  base_domain: mydevsite.com

  # OPTIONAL, uses app default if not provided
  region: us-east1

  # each collection can live in a different cloud account
  # 
  account_id: "foo-bar-123"
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
    - name: foo-secret
      secret_id: bar123

    # reference any terraform output
    # see flavor docs for available outputs
    - name: foo-output
      output_name: bar123-a
    
    # alias another variable name add another copy with a new name
    # you can alias any variable type
    - name: foo-standard-alias
      alias: foo-standard
```