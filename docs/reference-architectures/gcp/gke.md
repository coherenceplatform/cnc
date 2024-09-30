---
title: GKE Deep Dive
description: What does cnc deploy to my GCP cloud projects with the GKE flavor?
---

## Who is this flavor for

The `gke` flavor is designed to be the most robust and flexible deployment possible. It has best practices baked in throughout for security and reliablity. The lower bound for expected cost per collection for this deployment is approx $150 a month in GCP costs.

The `gke` flavor supports internal microservices that are not attached to a load balancer, using `is_internal` in the `x-cnc` yml for that service.

## Resources Used

### Networking

- A unique [VPC](https://cloud.google.com/vpc/docs) is configured for each application. Multiple services in one application share a VPC.
    - All workloads are configured to use only Private IPs by default, and all egress to the internet is via [Cloud NAT Gateway](https://cloud.google.com/nat/docs/overview)
- [Regional Load Balancing](https://cloud.google.com/load-balancing/docs/https) is used to route traffic to the right version and k8s service in your GKE cluster
    - Internal services with no load balancer access are also supported
- [Managed SSL Certificates](https://cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs) are used to secure connections to the application with no maintainence required.
    - For custom domains, all you need to do tell us the domain and point an `A` record in your DNS provider to the IP for your application (shown in the Coherence UI).
    - GCP support for custom domains with wildcard subdomains requires you to provide your own SSL certificate at this time, and upload it to the [SSL Certificates](https://cloud.google.com/load-balancing/docs/ssl-certificates) interface in the GCP console

### Build & Deploy

- Coherence spins up a [Google Cloud Storage](https://cloud.google.com/storage/docs) bucket for is created public assets fronted by CDN for each app, as a place to put non-repo resources (e.g. fonts, PDFs, images). Eventually you may want to augment this with a CMS like Contentful.
- [Cloud Build](https://cloud.google.com/build/docs) is used to build and deploy all the configured services. Build steps are parallelized as much as possible. Up to 10 concurrent test commands can be provided to `coherence.yml` and will be executed in parallel.

### Data Storage

Each environment in Coherence gets a distinct Cloud SQL instance. You also have the option to provide the name of an existing Cloud SQL instance and we will configure your app to use that instance. Supported resources include:

- [Cloud SQL](https://cloud.google.com/sql/docs) is used to provide database resources. Backups & high availability are not configured by default and the instance type is a `micro` - changing these in the UI or with the CLI will not be treated as drift.
- [Memorystore](https://cloud.google.com/memorystore/docs/redis) is used to provde hosted `redis` instances. Similar to Cloud SQL, backups and availability are confiigured for effeciency by default but changes to these configurations will not be overwriten by Coherence.
- [Google Cloud Storage](https://cloud.google.com/storage/docs) resources for object storage are also supported, the bucket information will be provided via environment varialbes to your application.

### Container Orchestration

- [Google Kubernetes Engine](https://cloud.google.com/run/docs) for both `frontend` and `backend`.
    - A k8s namespace is created for each environment
    - A k8s service is created in each environment for each `frontend` or `backend` service
    - A [managed zonal network endpoint group](https://cloud.google.com/kubernetes-engine/docs/how-to/standalone-neg) is created in gcp for each `cnc` service in each environment, with the corresponding load balancer configuration. Internal services skip this configuration.
- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/docs) is used for:
    - running async workers (like a celery/sidekiq queue worker)
    - running scheduled tasks (cron tasks) if those are configured.
    - the GKE control plane incurs a monthly cost in additon to deployed workloads.

### Observability & Monitoring
- [GCP Operations Suite](https://cloud.google.com/stackdriver/docs) (formerly Stackdriver) is configured to collect logs and metrics. You can adjust log filters and retention rules in the GCP console to control the cost of log ingestion and storage, if required as you scale.

### Security & Configuration

- [IAM](https://cloud.google.com/iam) Role and Policy are used for providing permissions to the services. Distinct identies are provisioned with minimum permissions for different app components, such as building, deploying, and executing the application.
- [Secrets Manager](https://cloud.google.com/secret-manager/docs) is used to store [Environment Variables](/docs/reference/environment-variables).
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) as well as dedicated Cloud Build Service Account integrations are used to assume app service accounts as needed without ever touching a key file. The `GKE` workloads will use the [identity federation](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) features provided by GCP for cloud access.
- [Compute Engine](https://cloud.google.com/compute/docs) is used to provide a bastion host so that external connectivity to resources in the VPC is possible, from either your local network or Coherence's [toolboxes](/docs/reference/toolbox).

### Default Labels

For convenience and auditability, Coherence adds default labels to all cloud resources where applicable:
```terraform
    default_labels = {
        environment = "YOUR-COLLECTION-NAME"
        managed_by = "coherence"
        application = "your-application-name"
    }
```


## Cloud Run vs GKE

- Google has a [comparison between Cloud Run and GKE](https://cloud.google.com/blog/products/containers-kubernetes/when-to-use-google-kubernetes-engine-vs-cloud-run-for-containers).  One important difference is Cloud Run autoscaling, which can scale to zero and use no resources if there are no requests.  [Scaling in GKE](https://cloud.google.com/kubernetes-engine/docs/how-to/scaling-apps) is controlled via replicas, which you can control with the `min_scale` attribute in the service definition