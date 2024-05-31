# Using an existing VPC
N.B. This is strictly for AWS

## Configuration

**via "environments.yml"**
```yml
name: my-backend-test-app
provider: aws
region: us-east-1
flavor: ecs
version: 1

collections:
- name: preview
  base_domain: my-backend-test-app.testnewsite.cncdev.com
  account_id: "foo-bar-123"
  existing_resources:
    db1:
      instance_name: foobar
      secret_id: foo123-1
    vpc:
      instance_name: vpc-00c97e7e48477356a
      public_subnet_cidrs:
        - "10.0.1.0/24"
        - "10.0.2.0/24"
      private_subnet_cidrs:
        - "10.0.10.0/24"
        - "10.0.20.0/24"
      public_subnet_ids:
        - "subnet-02e772928102604dc"
        - "subnet-02e772928102604dc"
      private_subnet_ids:
        - "subnet-02e772928102604dc"
        - "subnet-02e772928102604dc"
  environments:
  - name: main
    environment_variables:
    - name: foo
      value: bar
```

### collections[*].existing_resources.vpc
Your VPC configuration goes in this reserved existing resource (_must be named `vpc`, no other name will work_):

| Attribute | Required | Type | Description |
|-----------|----------|------|-------------|
|`instance_name`|Yes|String|The VPC ID of the existing VPC you want to use (e.g. "vpc-00c97e7e79377356a")|
|`public_subnet_cidrs`|No|Array[String]|This is a list of CIDR blocks (e.g. "10.0.1.0/24"). If specified, cnc will attempt to create public subnets using the provided CIDRs. This should not be set if `public_subnet_ids` are present. |
|`private_subnet_cidrs`|No|Array[String]|This is a list of CIDR blocks (e.g. "10.0.1.0/24"). If specified, cnc will attempt to create private subnets using the provided CIDRs. This should not be set if `private_subnet_ids` are present. |
|`public_subnet_ids`|No|Array[String]|Subnet IDs for existing public subnets within the VPC. (e.g. "subnet-02e772928102604dc") If specified, cnc will expect the public subnets to already be configured for public internet access (e.g. route tables, internet gateway, etc.)|
|`private_subnet_ids`|No|Array[String]|Subnet IDs for existing private subnets within the VPC. (e.g. "subnet-02e772928102604dc") If specified, cnc will expect the private subnets to already be configured for outbound internet access (e.g. route tables, nat gateway, etc.)|

#### Things to consider when using an existing vpc
- **IMPORTANT** It's highly recommended that you provide valid cidr blocks or existing subnet ids for both public and private subnets. If none are provided, CIDR blocks will be auto-generated. That may "just work" but if there are any conflicts with existing subnets, then CIDR blocks or subnet ids will need to be provided.
- In the default configuration 4 subnets of each type are created. When CIDR blocks or subnet ids are provided, those dictate the configuration (e.g. if 10 public_subnet_cidrs are provided, 10 subnets will be created)
- When providing public/private subnet cidrs be wary of how many IPs will be available within that block, and how many environments you'll have sharing the VPC. For example, a CIDR block with a "/28" netmask (e.g. "10.0.40.0/28") only has 16 IPs (2 ** (32 - netmask)).
