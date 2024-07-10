# CNC Flavors

A flavor is a set of IaC, build scripts, and deploy scripts, that work together to create a working environment. `cnc` has included flavors. As discussed in [customization](../customization/README.md) you can also customize (in part or whole) these further in your own repo.

## Included Flavors

`run-lite` is the fastest and cheapest flavor to get started with. It is designed to be as low cost as possible and will often fall under "free forever" pricing from GCP.

### AWS

- [ecs](./aws/ecs.md)

### GCP

- [run](./gcp/run.md)
- [gke](./gcp/gke.md)
- [run-lite](./gcp/run-lite.md)


## Developing your own flavor

Please develop and contribute new flavors! Read more at [development](.github/DEVELOPERS.md).
