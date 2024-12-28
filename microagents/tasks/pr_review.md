---
name: pr_review
version: 1.0.0
author: openhands
agent: CodeActAgent
category: development
task_type: workflow
inputs:
  - name: PR_URL
    description: "URL of the pull request"
    type: string
    required: true
    validation:
      pattern: "^https://github.com/.+/.+/pull/[0-9]+$"
  - name: QUALITY_FOCUS
    description: "Specific code quality areas to focus on"
    type: string
    required: false
    default: "Focus on maintainability and readability"
  - name: TEST_FOCUS
    description: "Specific testing areas to focus on"
    type: string
    required: false
  - name: DOC_FOCUS
    description: "Specific documentation areas to focus on"
    type: string
    required: false
---

# Pull Request Review Workflow

I'll help you review PR ${PR_URL} with these steps:

## 1. Code Quality
- Style consistency
- Best practices
- Performance considerations
${QUALITY_FOCUS}

## 2. Testing
- Test coverage
- Edge cases
- Integration tests
${TEST_FOCUS}

## 3. Documentation
- API documentation
- Usage examples
- Changelog updates
${DOC_FOCUS}

## Example Usage
```yaml
inputs:
  PR_URL: "https://github.com/org/repo/pull/123"
  QUALITY_FOCUS: "Check TypeScript types and error handling"
```
