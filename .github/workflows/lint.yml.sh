#just the commands of lint.yml for easier comparision.

# Frontend lint commands
cd frontend
npm install --frozen-lockfile
npm run lint
npm run make-i18n #&& tsc
npm run typecheck
npm run check-translation-completeness
cd ..

# Python lint commands
#pip install pre-commit==3.7.0
#pre-commit run --all-files --show-diff-on-failure --config ./dev_config/python/.pre-commit-config.yaml
poetry run pre-commit run --all-files --show-diff-on-failure --config ./dev_config/python/.pre-commit-config.yaml

# Version consistency check
.github/scripts/check_version_consistency.py
