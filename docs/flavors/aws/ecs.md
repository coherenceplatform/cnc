---
title: ECS Deep Dive
description: What does Coherence deploy to my AWS cloud account?
---

## Resources Used

### Networking
- A unique [VPC](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) is configured for each application. Multiple services in one application share a VPC.
    - Each VPC has both a public and private subnet. ECS nodes are provisioned on the private subnet and use a [NAT Gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html) to route traffic to the rest of the network or to the internet.
- [Route53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html) is used for DNS.
    - By default, a subdomain of `coherencesites.com` is allocated to each application, and we point the NS records for that subdomain in our DNS provider at the NS records for the Route53 Zone in your account.
    - Custom domains (per-environment) are also supported, in which case you will designate NS records to Route53 directly from your own DNS provider.
- [ACM Certificates](https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html) are used for secure HTTPS connections.
- [ALB and ALB Listener](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) are used for routing traffic to the backend services deployed on ECS. ALB Target Group is used to map to ECS services and manage health checks.
- [CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html) distributions are used for content delivery of frontend services hosted on S3. They are also used for traffic routing in backend services, but CDN functionality is not enabled by default for backend service types.
    - If you have at least one backend service as well as a frontend service in your app, a [Lambda@Edge](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html) is added to each environment's CloudFront distribution. This is because any non-200 response in CloudFront returns the distributions default error response, which means backend errors will be swallowed! Read more about this issue in Adam's blog post about the issue [here](https://www.withcoherence.com/post/aws-spa-routing-the-bad-the-ugly-and-the-uglier).

{% callout type="note" title="NAT Gateway Costs" %}
NAT gateway charges for all transit to the internet. Usage of the NAT gateway means that pulling docker impages into ECS tasks will incur transit costs (see AWS [here](https://aws.amazon.com/vpc/pricing/)). These can get expensive if frequent crons are used and especially if docker images are large. 

Get in touch to talk about alternatives (we have some!) if this describes your use case
{% /callout %}

### Build & Deploy
- [CodeBuild](https://docs.aws.amazon.com/codebuild/index.html) is used for building container images, running build steps such as asset compiling and testing the backend and frontend services, and is also used to manage ECS tasks spawned from the build to execute jobs like seeding or database migration.
- [CodePipeline](https://docs.aws.amazon.com/codepipeline/latest/userguide/welcome.html) is used for continuous integration and deployment of the services.

### Data Storage

Each AWS environment in Coherence gets a unique RDS instance. It also gets its own memorystore instance. For production, you also have the option to provide the name of an existing RDS instance and we will configure your app to use that instance. Generally we recommend this as a best practice. See the [coherence.yml docs](docs/configuration/coherenceyml#use-existing-databases) for more details.

- [S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) is used in 2 ways.
    - Storing the enriched source code that coherence uploads to AWS each time you push to an environment (A shallow clone of your repo plus our generated configuration files).
    - When you configure an object storage resource type in `coherence.yml` for a service. In this case, we also add appropriate IAM permissions to the service's IAM role and inject the bucket name via environment variables.
    - Coherence configures AWS-managed KMS key for encryption by default. You can read more about S3 bucket encryption [here](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html).
- [RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html) DB Instance is used for the database of the application. RDS Proxy is used for supported Postgres versions in order to pool connections. Backups & high availability are not configured by default and the instance type is a `micro` - changing these in the UI or with the CLI will not be treated as drift.
    - You can use a clustered RDS setup for your production database with the `use_existing` [configuration](/docs/configuration/services#resources) in your `coherence.yml`. This includes using an Aurora cluster. Aurora and HA clusters are not supported for preview environments at this time.
    - Coherence configures AWS-managed KMS key for encryption by default. You can view the encryption settings for your RDS instance following the AWS docs [here](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html#Overview.Encryption.Determining).
- [ElastiCache](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/WhatIs.html) is used to provide managed redis instances to the application.

### Container Orchestration
- [ECS](https://docs.aws.amazon.com/AmazonECS/latest/userguide/what-is-fargate.html) Fargate Cluster and Task Definitions are used for running the backend services, including scheduled tasks (cron) and private workers. Spot instances are automatically used for PR preview environments.
- [App Autoscaling Policy and Target](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-auto-scaling.html) are used for automatic scaling of backend services on ECS.

### Observability & Monitoring
- [CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html) Log Group and Metric Alarm are used for monitoring and logging of the backend services. Metric alarms are used for ECS autoscaling rules.

### Security & Configuration

Please note that Coherence enforces best practices around the usage of the root account in AWS. Read more about AWS best practice guidance [here](https://docs.aws.amazon.com/SetUp/latest/UserGuide/best-practices-root-user.html).

- [Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html) is used to store [Environment Variables](/docs/reference/environment-variables).
- [IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) Role and Policy are used for providing permissions to the services. Distinct roles are provisioned with minimum permissions for different app components, such as building, deploying, and executing the application. You can [customize](/docs/how-to/modify-iam-roles) these roles if needed.
- [Workload Identities](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/workload-identities.html) are used to assume app service accounts as needed without ever touching a key file.
- [EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html) is used to provide a bastion host so that external connectivity to resources in the VPC is possible, from either your local network or Coherence's [toolboxes](/docs/reference/toolbox).

### Default Tags

For convenience and auditability, Coherence adds default tags to all cloud resources where applicable:
```terraform
    tags = {
        Environment = "production|review"
        ManagedBy = "coherence"
        Application = "your-application-name"
    }
```

## Diagram

![AWS Infra Diagram](./docs/images/aws-infra.png)