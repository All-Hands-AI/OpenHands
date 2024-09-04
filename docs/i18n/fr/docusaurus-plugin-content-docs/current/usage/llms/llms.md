---
sidebar_position: 2
---

# 🤖 Backends LLM

OpenHands peut fonctionner avec n'importe quel backend LLM.
Pour une liste complète des fournisseurs et des modèles LM disponibles, veuillez consulter la
[documentation litellm](https://docs.litellm.ai/docs/providers).

:::warning
OpenHands émettra de nombreuses invitations au LLM que vous configurez. La plupart de ces LLM coûtent de l'argent -- assurez-vous de définir des limites de dépenses et de surveiller l'utilisation.
:::

La variable d'environnement `LLM_MODEL` contrôle le modèle utilisé dans les interactions programmatiques.
Mais en utilisant l'interface utilisateur OpenHands, vous devrez choisir votre modèle dans la fenêtre des paramètres (la roue dentée en bas à gauche).

Les variables d'environnement suivantes peuvent être nécessaires pour certains LLM :

- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_API_VERSION`

Nous avons quelques guides pour exécuter OpenHands avec des fournisseurs de modèles spécifiques :

- [ollama](llms/local-llms)
- [Azure](llms/azure-llms)

Si vous utilisez un autre fournisseur, nous vous encourageons à ouvrir une PR pour partager votre configuration !

## Remarque sur les modèles alternatifs

Les meilleurs modèles sont GPT-4 et Claude 3. Les modèles locaux et open source actuels ne sont pas aussi puissants.
Lors de l'utilisation d'un modèle alternatif, vous pouvez constater des temps d'attente prolongés entre les messages,
des réponses de mauvaise qualité ou des erreurs sur des JSON mal formés. OpenHands
ne peut être aussi puissant que les modèles qui le pilotent -- heureusement, les membres de notre équipe travaillent activement à la construction de meilleurs modèles open source !

## Réessais d'API et limites de taux

Certains LLM ont des limites de taux et peuvent nécessiter des réessais. OpenHands réessaiera automatiquement les demandes s'il reçoit une erreur 429 ou une erreur de connexion API.
Vous pouvez définir les variables d'environnement `LLM_NUM_RETRIES`, `LLM_RETRY_MIN_WAIT`, `LLM_RETRY_MAX_WAIT` pour contrôler le nombre de réessais et le temps entre les réessais.
Par défaut, `LLM_NUM_RETRIES` est 8 et `LLM_RETRY_MIN_WAIT`, `LLM_RETRY_MAX_WAIT` sont respectivement de 15 secondes et 120 secondes.
