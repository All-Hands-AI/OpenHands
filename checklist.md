# Azure DevOps Implementation Checklist (Based on Bitbucket PR #9021)

## Files that should be modified for Azure DevOps (analogous to Bitbucket changes):

### Frontend Tests
- [ ] `frontend/__tests__/routes/git-settings.test.tsx` - Add Azure DevOps token input tests
- [ ] Update test expectations to include Azure DevOps

### Frontend Assets
- [x] `frontend/src/assets/branding/azure-devops-logo.svg` - Azure DevOps logo (DONE)

### Frontend Components - Chat
- [ ] `frontend/src/components/features/chat/action-suggestions.tsx` - Add Azure DevOps provider support

### Frontend Components - Home
- [ ] `frontend/src/components/features/home/tasks/task-card.tsx` - Add Azure DevOps task card support

### Frontend Components - Settings
- [x] `frontend/src/components/features/settings/git-settings/azure-devops-token-help-anchor.tsx` - Help component (DONE)
- [x] `frontend/src/components/features/settings/git-settings/azure-devops-token-input.tsx` - Token input component (DONE)

### Frontend Components - Auth
- [x] `frontend/src/components/features/waitlist/auth-modal.tsx` - Add Azure DevOps auth button (DONE)

### Frontend Hooks
- [x] `frontend/src/hooks/use-auto-login.ts` - Add Azure DevOps auto-login support (DONE)

### Frontend i18n
- [x] `frontend/src/i18n/declaration.ts` - Add Azure DevOps translation keys (DONE)
- [x] `frontend/src/i18n/translation.json` - Add Azure DevOps translations (DONE)

### Frontend Routes
- [x] `frontend/src/routes/git-settings.tsx` - Add Azure DevOps settings (DONE)

### Frontend Utils
- [x] `frontend/src/utils/local-storage.ts` - Add Azure DevOps to LoginMethod enum (DONE)

### Backend Integration
- [x] `openhands/integrations/azure_devops/azure_devops_service.py` - Azure DevOps service implementation (DONE)
- [x] `openhands/integrations/provider.py` - Add Azure DevOps to provider mapping (DONE)
- [x] `openhands/integrations/service_types.py` - Add Azure DevOps provider type and terms (DONE)
- [ ] `openhands/integrations/utils.py` - Add Azure DevOps token validation

### Backend Resolver
- [ ] `openhands/resolver/README.md` - Update documentation to include Azure DevOps
- [x] `openhands/resolver/interfaces/azure_devops.py` - Azure DevOps resolver interface (DONE)
- [ ] `openhands/resolver/send_pull_request.py` - Add Azure DevOps PR support
- [ ] `openhands/resolver/utils.py` - Add Azure DevOps token identification

### Backend Runtime
- [ ] `openhands/runtime/base.py` - Add Azure DevOps authentication support

## Files that should NOT be modified (Bitbucket-specific):
- Any file with "bitbucket" in the name or content
- Bitbucket CI/CD specific configurations
- Bitbucket-specific API implementations

## Status:
- ✅ DONE: Basic Azure DevOps integration exists
- ✅ DONE: Frontend auth modal and settings
- ✅ DONE: i18n translations
- ❌ MISSING: Several frontend and backend files need Azure DevOps support