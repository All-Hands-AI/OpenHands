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

Add GitHub workflow in each repo (OpenHands, runtime-api, deploy) that can be
manually triggered which takes feature branch name, builds images and pushes
them to S3, producing presigned URLs and spitting them out into GitHub logs. The
FDE would then make changes on the feature branch, run the special workflow and
copy and paste the URL to share with the client.

### 1.3 Difference from Typical Workflow

For clients who can directly pull images from our docker repository, this
process is not required. Instead the existing build automatically creates images
when a PR is opened and pushes them to GitHub Container Registry (GHCR). The
typical workflow works as follows:

1. **Automatic Image Building**: When a PR is opened, the `ghcr-build.yml` workflow
   automatically builds three types of images:
   - **OpenHands app image** (`ghcr.io/all-hands-ai/openhands`) - the main application
   - **Runtime image** (`ghcr.io/all-hands-ai/runtime`) - in both Nikolaik and Ubuntu flavors
   - **Enterprise image** (`ghcr.io/all-hands-ai/enterprise-server`) - for enterprise features

2. **Image Tagging**: Images are tagged with:
   - The PR number (e.g., `pr-123`)
   - The commit SHA (e.g., `abc1234`)
   - Branch name for main branch pushes
   - Semantic version tags for releases

3. **PR Description Updates**: The workflow automatically updates PR descriptions
   with Docker commands that customers can use to test the changes:

   ```bash
   docker run -it --rm \
     -p 3000:3000 \
     -v /var/run/docker.sock:/var/run/docker.sock \
     --add-host host.docker.internal:host-gateway \
     -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:${SHORT_SHA}-nikolaik \
     --name openhands-app-${SHORT_SHA} \
     docker.all-hands.dev/all-hands-ai/openhands:${SHORT_SHA}
   ```

4. **Enterprise Preview Deployments**: For PRs labeled with "deploy", the workflow
   triggers a preview deployment to a feature environment using the enterprise image.

5. **Customer Access**: Customers can then update their Helm values file to point
   to these new image versions directly from GHCR, or use the provided Docker
   commands to test changes locally.

## 2. Developer Experience

### 2.1 The Workflow will Exist in Two Repos

Three images are required for self-hosted, in early V1 from two repos:

   1. OpenHands open source ([All-Hands-AI/OpenHands](http://github.com/All-Hands-AI/OpenHands/))
   2. enterprise ([All-Hands-AI/OpenHands](http://github.com/All-Hands-AI/OpenHands/))
   3. runtime-api ([All-Hands-AI/runtime-api](https://github.com/All-Hands-AI/runtime-api))

We expect that eventually the runtime microservice will be deprecated but for
now it means that we will have workflows in these two repos for building the
complete image set.

### 2.2 Triggered on Demand

The workflow will be triggered only on demand. Engineers will go to the Github
Workflow to manually trigger and enter the branch name to kick-off the build.

### 2.3 OpenHands Repo Workflow Builds Selected Images

The manual trigger for building workflows also prompts user with checklist of
images to build.

## 3. Solution Design

### 3.1 S3 Bucket Structure

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

## 4. Open Questions

### 4.1 Do we want to require PR mirroring the current process

An alternative to the proposed manual trigger is that we always require PR for
feature branch image builds like we do today and when the PR is tagged with S3
every build is automatically released to S3 as well. Additionally an automated
comment to the S3 bucket could provide the S3 bucket image links.

### 4.2 Secrets

- We will need secrets for the S3 bucket where images are published. While we
  might otherwise store these in GitHub secrets, this would allow maintainers
  who are not All Hands employees write access to S3 storage which given our
  highly regulated clients, is probably not acceptable.

### 4.3 White List

- We will need secure who can trigger these builds.

### 4.4 Change Log

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
