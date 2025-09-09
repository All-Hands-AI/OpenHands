# GitHub Workflow to Publish Prerelease Images

- [ALL-3467](https://linear.app/all-hands-ai/issue/ALL-3467)
- [ALL-2610](https://linear.app/all-hands-ai/issue/ALL-2610)

## 1. Introduction

### 1.1 Problem Statement

Large banks, insurance companies, etc. often cannot use images from public
internet and must instead consume them from a local image repo where images are
quarantined before approval and use. When supporting such clients, we often need
to build custom images and share them via an s3 bucket with presigned url. Our
internal process for this is currently long multistep process that could easily
be automated.

### 1.2 Proposed Solution

Two scenarios:

**Regular SaaS Release** - A new job is added to the release workflow so that for
every SaaS release tarballs are pushed to S3. Presigned URLs need to be
published in a changelog accessible by our customers.

**Special Troubleshooting Builds** - Add GitHub a workflow to the `deploy` repo
which is manually triggered to build and push to S3 from a named feature branch.
The FDE would then make changes on the feature branch, run the special workflow
and copy and paste the URL from the GitHub action to share with the client.

## 2. Additional Context

### 2.1 Images

Three images are required for self-hosted, in early V1 from two repos:

   1. `enterprise-server` built from ([All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands))
   2. `runtime:{version}-nikolaik` built from ([All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands))
   3. `runtime-api` built from ([All-Hands-AI/runtime-api](https://github.com/All-Hands-AI/runtime-api))

We expect that eventually the runtime microservice will be deprecated but for
now it means that we will have workflows in these two repos for building the
complete image set.

### 2.2 Current Process

- In the `OpenHands` repository images are built for feature branches that have
  an associated PR. Images are tagged with feature branch name or or number:
  e.g. `pr-123`.
- In the `runtime-api` repository images are built on any feature branch.
- Production SaaS releases are kicked off when a tag using semver format is
  pushed to the OpenHands repo. Deployment of SaaS is delegated to workflows in
  the `deploy` repo.
- When a release includes changes to the `runtime-api` image, the `runtime-api`
  repo needs to be tagged with the release version as well.

## 3. Developer Experience

### 3.1 Future State Process - Typical Releases

S3 is now automatically updated when the image repos are on tagging of the
release. No process change for the release engineer or developer.

### 3.2 Future State Process - Troubleshooting Releases

Engineers will go to a new Github Workflow in `OpenHands` and/or `runtime-api`
to manually trigger a build supplying the target branch name. The image(s) are
built and published to S3. An S3 link in the build log may be shared with the
customer.

## 4. Solution Design

### 4.1 S3 Bucket Structure

Images in the S3 bucket will be namespaced by branch name and commit SHA. If
engineers use the same branch name across repos, images for a particular issue
can be stored together. Since multiple builds could be produced from the same
branch, the commit SHA is used within the branch folder to ensure uniqueness
and traceability to the exact code being built.

This approach aligns with the standard GHCR workflow which uses commit SHAs for
image tagging, ensuring consistency across our build processes.

To help clients identify the latest prerelease image from a feature branch, each
branch folder will include a `CHANGELOG.md` file that documents all builds for
that branch, with the most recent build listed first.

Example:

```plaintext
s3://prerelease-bucket/
├── jps/publish-prerelease-images/
│   ├── CHANGELOG.md  # Documents all builds
│   ├── abc1234/
│   │   ├── openhands:latest.tar
│   │   ├── openhands:main-abc1234.tar
│   │   ├── enterprise:latest.tar
│   │   ├── enterprise:main-abc1234.tar
│   │   ├── runtime-api:latest.tar
│   │   └── runtime-api:main-abc1234.tar
│   └── def5678/
│       ├── openhands:latest.tar
│       ├── enterprise:latest.tar
│       └── runtime-api:latest.tar
└── mj/security-patch-123/
    ├── CHANGELOG.md
    └── ghi9012/
        ├── openhands:hotfix-security.tar
        └── enterprise:hotfix-security.tar
```

## 5. Open Questions

### 5.1 Where does the push to S3 live?

- Delegate to `deploy` repo GitHub action or do S3 push directly from OpenHands repo?

### 5.2 Secrets

- How do we secure AWS S3 secret? In OpenHands repo GitHub Actions Secrets or
  via another mechanism?

### 5.3 White List

- How do we secure who can trigger these builds?

### 5.4 Change Log

Ideally this process should be self-documenting and leave a clear trail of what
was released to the customer and why. The `CHANGELOG.md` file serves multiple purposes:

1. **Build Documentation**: Documents all builds for a feature branch with timestamps,
   commit SHAs, and descriptions of changes
2. **Latest Build Identification**: Clients can identify the latest build by reading
   the first entry in the changelog
3. **Release Trail**: Provides a clear audit trail of what was delivered to customers

The changelog will be automatically generated/updated by the build process and should
include:

- Build timestamp
- Commit SHA and short description
- List of images built
- Any custom notes from the `.doc/branch-name/CHANGELOG.md` file
- Links to the specific commit builds

Example changelog entry:

```markdown
## Build History

### 2024-01-16 09:15:42Z - def5678
**Commit**: `def5678` - Fix authentication bug in enterprise mode
**Images**: openhands, enterprise, runtime-api
**Notes**: Critical security fix for enterprise customers

### 2024-01-15 14:30:25Z - abc1234
**Commit**: `abc1234` - Initial feature implementation
**Images**: openhands, enterprise, runtime-api
**Notes**: First prerelease build for client testing
```

## 5. Appendix

### 5.1 Existing Jobs

- [.github/workflows/ghcr-build.yml](https://github.com/All-Hands-AI/OpenHands/blob/main/.github/workflows/ghcr-build.yml#L169)

And the runtime build job (not to be confused with runtime-api, a different
component)

- [.github/workflows/ghcr-build.yml](https://github.com/All-Hands-AI/OpenHands/blob/main/.github/workflows/ghcr-build.yml#L89)

Runtime image builds in two flavors, Nikolaik (based on debian) and Ubuntu.
Probably we should publish both for your purposes. The Ubuntu flavor was created
for a partner (maybe Modern health, not sure), in order to get CVEs down.

It's thought that in the future more flavors will be desired but there are
various difficulties with doing that (can of worms omitted for now).
