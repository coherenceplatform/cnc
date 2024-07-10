---
title: Cloud Run
description: What does Coherence deploy to my GCP cloud projects?
---

What does Coherence do in my GCP cloud account?

- Depending on the `coherence.yml` provided, various resources will be deployed into your GCP account.
- You always have the option to delete the entire infrastructure with one click in your Coherence app's settings page.
- The estimated cost for resources is described [here](/docs/overview/pricing).

By default, we will deploy your application in `us-east1` but you can select a different region during the onboarding process for your app.

Coherence deploys your production environment into a separate GCP account, so you will have a second set of many of the resources below if you configure a production environment in your application.

## Resources Used

### Networking
- A unique [VPC](https://cloud.google.com/vpc/docs) is configured for each application. Multiple services in one application share a VPC.
    - All workloads are configured to use only Private IPs by default, and all egress to the internet is via [Cloud NAT Gateway](https://cloud.google.com/nat/docs/overview)
    - Cloud Run workloads are peered into the VPC using [Serverless VPC Connector](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access).
- [Regional Load Balancing](https://cloud.google.com/load-balancing/docs/https) is used to route traffic to the right verion and service in your VPC
- [Managed SSL Certificates](https://cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs) are used to secure connections to the application with no maintainence required.
    - For custom domains, all you need to do tell us the domain and point an `A` record in your DNS provider to the IP for your application (shown in the Coherence UI).
    - GCP support for custom domains with wildcard subdomains requires you to provide your own SSL certificate at this time, and upload it to the [SSL Certificates](https://cloud.google.com/load-balancing/docs/ssl-certificates) interface in the GCP console

### Build & Deploy
- Coherence spins up a [Google Cloud Storage](https://cloud.google.com/storage/docs) bucket for is created public assets fronted by CDN for each app, as a place to put non-repo resources (e.g. fonts, PDFs, images). Eventually you may want to augment this with a CMS like Contentful.
- [Cloud Build](https://cloud.google.com/build/docs) is used to build and deploy all the configured services. Build steps are parallelized as much as possible. Up to 10 concurrent test commands can be provided to `coherence.yml` and will be executed in parallel.

### Data Storage

Each environment in Coherence gets a database on a shared instance (for review apps). It gets its own memorystore instance. For production, a distinct instance will be used - you also have the option to provide the name of an existing Cloud SQL instance and we will configure your app to use that instance. Generally we recommend this as a best practice. See the [coherence.yml docs](docs/configuration/coherenceyml#use-existing-databases) for more details.

- [Cloud SQL](https://cloud.google.com/sql/docs) is used to provide database resources. Backups & high availability are not configured by default and the instance type is a `micro` - changing these in the UI or with the CLI will not be treated as drift.
- [Memorystore](https://cloud.google.com/memorystore/docs/redis) is used to provde hosted `redis` instances. Similar to Cloud SQL, backups and availability are confiigured for effeciency by default but changes to these configurations will not be overwriten by Coherence.
- [Google Cloud Storage](https://cloud.google.com/storage/docs) resources for object storage are also supported, the bucket information will be provided via environment varialbes to your application.

### Container Orchestration

GCP's Cloud Run is unique when compared to `ECS` in AWS because it offers scale-to-0 autoscaling. This can keep costs very low, it's a true "serverless" container orchestration layer. However, it has some limitations when it comes to long-running jobs. So, we integrate it seamlessly with GKE to provide you with the best experience possible across best-in-class tools on GCP, each for their own purpose.

- [Cloud Run](https://cloud.google.com/run/docs) for both frontend and backend. We configure GCP's [CDN](https://cloud.google.com/cdn/docs) in front of the frontend service type.
    - The reason to use Cloud Run for the frontend vs Google Cloud Storage is due to the need for redirects based on 404 so you can do proper client-side routing in a Single Page App. We deploy `nginx` in Cloud Run (all configured and managed for you) for this purpose.
    - GCP’s solution is Firebase sites which has its own separate integration into other GCP services, see [Reddit](https://www.reddit.com/r/googlecloud/comments/rvhki2/hosting_a_single_page_app_on_gcs_and_an_https/) or [Stack Overlow](https://stackoverflow.com/questions/63006272/how-to-correctly-rewrite-urls-for-single-page-app-in-gcp-static-deployment)
- [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/docs) is used for running async workers (like a celery/sidekiq queue worker) and for running scheduled tasks (cron tasks) if those are configured. The GKE control plane incurs a monthly cost in additon to deployed workloads.

### Observability & Monitoring
- [GCP Operations Suite](https://cloud.google.com/stackdriver/docs) (formerly Stackdriver) is configured to collect logs and metrics. You can adjust log filters and retention rules in the GCP console to control the cost of log ingestion and storage, if required as you scale.

### Security & Configuration
- [IAM](https://cloud.google.com/iam) Role and Policy are used for providing permissions to the services. Distinct identies are provisioned with minimum permissions for different app components, such as building, deploying, and executing the application.
- [Secrets Manager](https://cloud.google.com/secret-manager/docs) is used to store [Environment Variables](/docs/reference/environment-variables).
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) as well as Cloud Run and Cloud Build Service Account integrations are used to assume app service accounts as needed without ever touching a key file.
- [Compute Engine](https://cloud.google.com/compute/docs) is used to provide a bastion host so that external connectivity to resources in the VPC is possible, from either your local network or Coherence's [toolboxes](/docs/reference/toolbox).

### Default Labels

For convenience and auditability, Coherence adds default labels to all cloud resources where applicable:
```terraform
    default_labels = {
        environment = "production|review"
        managed_by = "coherence"
        application = "your-application-name"
    }
```

### Google Kubernetes Engine (GKE) (beta)

- [GKE](https://cloud.google.com/kubernetes-engine?hl=en) Your application can be deployed using Google Kubernetes Engine instead of Google Cloud Run.  This is an application level setting that applies to all services.
    - A service in coherence.yml will correspond to a [Service](https://cloud.google.com/kubernetes-engine/docs/concepts/service) in GKE.
    - Each Coherence environment will have it's own Kubernetes Namespace
    - You can include custom Helm Charts to create Kubernetes Deployments by setting the `helm_path` as a top level key in your service definition yaml. The value for `helm_path` should be a file path in your repo to a Kubernetes Deployment file that can be rendered with Helm.  If no `helm_path` is specified, Coherence will create one to run your service.
    - Your Coherence environment variables will be added to your Kubernetes cluster as secrets and can be accessed in your Helm Chart.
    - Coherence will deploy your GKE application in the `{your-app-name}-jobs` cluster that is also used for running scheduled tasks and workers.  For each Coherence environment Coherence will create a new namespace `{your-environment-name}-deploy`

#### Cloud Run vs GKE

- Google has a [comparison between Cloud Run and GKE](https://cloud.google.com/blog/products/containers-kubernetes/when-to-use-google-kubernetes-engine-vs-cloud-run-for-containers).  One important difference is Cloud Run autoscaling, which can scale to zero and use no resources if there are no requests.  [Scaling in GKE](https://cloud.google.com/kubernetes-engine/docs/how-to/scaling-apps) is controlled via replicas, which you can control with the `min_scale` attribute in the service definition of your coherence.yml
