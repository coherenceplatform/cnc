---
title: GCP Run Lite Overview
description: What does cnc deploy to my GCP cloud projects with the GKE flavor?
---

The `run-lite` flavor is designed to be as free-friendly as possible and still be a robust choice for hosting many applications. 

If you're building a bootstraped side-project or hobby full-stack web app, this flavor is made for you! It will often be free, but usage of optionla services such as [Cloud SQL](https://cloud.google.com/sql/docs) or [Secret Manager](https://cloud.google.com/secret-manager/docs) might incur some usage costs. These are also often eligible for credits or free use tiers, depending on your GCP billing account.

## Resources Used

[Cloud Run](https://cloud.google.com/cloud-run/docs) is the most important services in this flavor. For each service in each environment (only `backend` is supported), `cnc` will:

- create a cloud run service (get the URL from the GCP Cloud Console)
- create a [cloud run job](https://cloud.google.com/run/docs/create-jobs) version
- use a GCP SDK in your code to submit jobs with the `CNC_INSTANCE_NAME` as the job name, and you have an autoscaling async work queue
- if defined, resources like `Cloud SQL` and `Cloud Storage` are also supported and will be configured including environment vars for service discovery

### Networking

Cloud run operates in a GCP-controlled network with access limited to the URLs provided by the Cloud Run service.

### Data Storage

Each environment in Coherence gets a database on a shared instance (for review apps). It gets its own memorystore instance. For production, a distinct instance will be used - you also have the option to provide the name of an existing Cloud SQL instance and we will configure your app to use that instance. Generally we recommend this as a best practice. See the [coherence.yml docs](docs/configuration/coherenceyml#use-existing-databases) for more details.

- [Cloud SQL](https://cloud.google.com/sql/docs) is used to provide database resources. Backups & high availability are not configured by default and the instance type is a `micro` - changing these in the UI or with the CLI will not be treated as drift.
    - To avoid incurring GCP platform costs, using 3rd party databases such as [neon]() or [supabase]() is also possible
- [Google Cloud Storage](https://cloud.google.com/storage/docs) resources for object storage are also supported, the bucket information will be provided via environment varialbes to your application.

### Security & Configuration
- [IAM](https://cloud.google.com/iam) Role and Policy are used for providing permissions to the services. Distinct identies are provisioned with minimum permissions for different app components, such as building, deploying, and executing the application.
- [Secrets Manager](https://cloud.google.com/secret-manager/docs) is used to store [Environment Variables](/docs/reference/environment-variables) defined as secrets
    - To avoid incurring any cloud costs, using plain variables in your `environments.yml` in `cnc` is alos possible
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) as well as Cloud Run and Cloud Build Service Account integrations are used to assume app service accounts as needed without ever touching a key file.

### Default Labels

For convenience and auditability, `cnc` adds default labels to all cloud resources where applicable:
```terraform
    default_labels = {
        environment = "your-collection-name"
        managed_by = "cnc"
        application = "your-application-name"
    }
```
