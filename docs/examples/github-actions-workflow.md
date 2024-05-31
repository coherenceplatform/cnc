# Github Actions Workflow

Here, we will outline one possible common workflow for using CNC with Github Actions and AWS to deploy a `staging` and `production` environment. You can adapt it to different clouds, CI providers, as needed. There are many different workflows possible with CNC, and this is only one of them.

## Provisioning the environments

You've got someone who is most knowledgeable about cloud infra who is going to manage the infra as code for your team, and who is going to set up the deployment pipelines. They are going to follow one of the [examples](./examples/) to configure `cnc` for the team's app.

When they run `cnc provision apply` it will create the environments defined in their configuration. Here's an example `environments.yml` with the `staging` and `production` defined in 2 different AWS accounts.

```yaml
name: my-fastapi-app
provider: aws
flavor: ecs
version: 1

collections:
- name: staging
  region: us-east-1
  base_domain: dev.mynextsite.com
  account_id: "0123455789"
  environments:
  - name: staging
- name: production
  region: us-east-1
  base_domain: dev.mynextsite.com
  account_id: "0123455789"
  environments:
  - name: production
```

The customization that this user should think about is the storage of the `terraform` state. Read more [here](./customization/infra_state.md).

## Setting up a github actions deployment pipeline

Without any setup, this user can use `cnc update` to push a new version to each environment. However, the team does not want to have to run a command to update the environments, they want them to be based on branches in github. This is easy to accomplish using `cnc`. Here's an example github actions workflow that you can put in the `.github/workflows` folder in your repo to perform this on the desired branches.

```yaml
name: Run CNC Update on Branch Update

on:
  push:
    branches:
      - staging
      - production

jobs:
  update-cnc:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install CNC
      run: |
        python -m pip install --upgrade pip
        pip install cocnc

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: <your-aws-region>
    
    - name: Run CNC Update
      # ref is the branch name, which matches the collection & environment name in this case
      run: cnc update perform ${{ github.ref }} --collection-name ${{ github.ref }} --service-tags app=${{ github.sha }}
```

You'll need to set up the correct secrets for `AWS` authentication before this workflow will work properly.

## Infra state impacts

You can ignore this if you do not use infra outputs as environment variables. Even if you use those, if the infra state is stored in the cloud and the workflow can access it (e.g. the `AWS` auth step will have permission to the bucket where it lives), you can ignore the below.

Depending on where the infra state is stored, some functionality may not work as expected out of the box. You can specify `infrastructure_outputs` in `environments.yml` for each collection in the `data`, e.g.

```yaml
collections:
- name: staging
  region: us-east-1
  base_domain: dev.mysite.com
  account_id: "0123455789"

  # adding these here means cnc won't check infra state for outputs, cnc will just pull these from the yml directly
  data:
    infrastructure_outputs:
      db1-secrets: 
        value: "my_infra_output"

  environments:
  - name: staging
```

After adding this to the `environments.yml`, you can run `cnc update` in Github Actions without giving the Actions workflow access to the infra state directly or requiring `terraform`. To make this easy, `cnc` will automatically add these to your `environments.yml` if you run `cnc provision apply --update-environments` which you can then commit to your repo and share with your team. Check for sensitive outputs before committing!