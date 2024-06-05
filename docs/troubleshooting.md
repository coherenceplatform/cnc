# Troubleshooting

## GCP

### "reason": "SERVICE_DISABLED"

This happens in new projects when `apply`ing provision the first time, the only answer is to wait a few minutes and try again, unfortunately.

### DRS permissions

- https://cloud.google.com/blog/topics/developers-practitioners/how-create-public-cloud-run-services-when-domain-restricted-sharing-enforced
- TLDR: change the "Domain Restricted Sharing" policy and remove the org-only access restriction policy, then run `cnc deploy` again 