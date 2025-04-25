# Static Files for OpenHands Documentation

This directory contains static files that are copied directly to the build output of the Docusaurus documentation.

## OpenAPI Specification

The `openapi.json` file in this directory is the OpenAPI specification for the OpenHands API. It is copied to the build output and is accessible at `/openapi.json` in the deployed site.

This file is used by the Swagger UI interface, which is accessible at `/swagger-ui/` in the deployed site.

## Why is the OpenAPI spec in the static directory?

The OpenAPI specification is placed in the static directory so that it's accessible at a predictable URL in the deployed site. This allows the Swagger UI to reference it directly.

We only need one copy of the OpenAPI spec file, which is this one in the static directory.
