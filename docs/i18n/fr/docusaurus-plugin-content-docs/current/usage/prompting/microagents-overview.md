# Aperçu des Microagents

Les microagents sont des prompts spécialisés qui améliorent OpenHands avec des connaissances spécifiques à un domaine.
Ils fournissent des conseils d'experts, automatisent les tâches courantes et assurent des pratiques cohérentes dans les projets.

## Types de Microagents

Actuellement, OpenHands prend en charge les types de microagents suivants :

- [Microagents Généraux de Dépôt](./microagents-repo) : Directives générales pour OpenHands concernant le dépôt.
- [Microagents Déclenchés par Mots-clés](./microagents-keyword) : Directives activées par des mots-clés spécifiques dans les prompts.

Pour personnaliser le comportement d'OpenHands, créez un répertoire .openhands/microagents/ à la racine de votre dépôt et
ajoutez des fichiers `<microagent_name>.md` à l'intérieur.

:::note
Les microagents chargés occupent de l'espace dans la fenêtre de contexte.
Ces microagents, ainsi que les messages des utilisateurs, informent OpenHands sur la tâche et l'environnement.
:::

Exemple de structure de dépôt :

```
some-repository/
└── .openhands/
    └── microagents/
        └── repo.md            # Directives générales du dépôt
        └── trigger_this.md    # Microagent déclenché par des mots-clés spécifiques
        └── trigger_that.md    # Microagent déclenché par des mots-clés spécifiques
```

## Exigences de Frontmatter pour les Microagents

Chaque fichier de microagent peut inclure un frontmatter qui fournit des informations supplémentaires. Dans certains cas, ce frontmatter
est requis :

| Type de Microagent                     | Requis  |
|----------------------------------------|---------|
| `Microagents Généraux de Dépôt`        | Non     |
| `Microagents Déclenchés par Mots-clés` | Oui     |
