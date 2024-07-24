# CNC Reference Architectures

A `flavor` is a reference architecture built into `cnc`. It's a set of IaC (`provision`), build scripts, and deploy scripts, that work together to create a working environment. As discussed in [customization](/customization/overview/) you can also customize (in part or whole) these architectures further in your own repo, up to fully writing your own architecture that uses none of the included parts.

You specify the app's flavor in `environments.yml`, e.g.

```yaml
# name of your app
name: my-first-app
provider: gcp
region: us-east1
flavor: run-light
```

## Included Architectures

`run-lite` is the fastest and cheapest flavor to get started with. It is designed to be as low cost as possible and will often fall under "free forever" pricing from GCP.

### AWS

- [ecs](./aws/ecs.md)

### GCP

- [run](./gcp/run.md)
- [gke](./gcp/gke.md)
- [run-lite](./gcp/run-lite.md)


## Developing your own flavor

You can customize `cnc` limitlessly. See [Customizing CNC](/customization/overview/) for more.
