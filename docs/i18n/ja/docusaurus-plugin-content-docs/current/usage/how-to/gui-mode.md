

# Mode Interface Graphique

## Introduction

OpenHands fournit un mode Interface Graphique (GUI) convivial pour interagir avec l'assistant IA. Ce mode offre une façon intuitive de configurer l'environnement, gérer les paramètres et communiquer avec l'IA.

## Installation et Configuration

1. Suivez les instructions du guide [Installation](../installation) pour installer OpenHands.

2. Après avoir exécuté la commande, accédez à OpenHands à l'adresse [http://localhost:3000](http://localhost:3000).

## Interagir avec l'Interface Graphique

### Configuration Initiale

1. Lors du premier lancement, vous verrez une fenêtre modale de paramètres.
2. Sélectionnez un `Fournisseur LLM` et un `Modèle LLM` dans les menus déroulants.
3. Entrez la `Clé API` correspondante pour le fournisseur choisi.
4. Cliquez sur "Enregistrer" pour appliquer les paramètres.

### Configuration du Jeton GitHub

OpenHands exporte automatiquement un `GITHUB_TOKEN` vers l'environnement shell s'il est disponible. Cela peut se produire de deux manières :

1. **Localement (OSS)** : L'utilisateur saisit directement son jeton GitHub
2. **En ligne (SaaS)** : Le jeton est obtenu via l'authentification OAuth GitHub

#### Configuration d'un Jeton GitHub Local

1. **Générer un Personal Access Token (PAT)** :
   - Allez dans Paramètres GitHub > Paramètres développeur > Personal Access Tokens > Tokens (classique)
   - Cliquez sur "Générer un nouveau jeton (classique)"
   - Portées requises :
     - `repo` (Contrôle total des dépôts privés)
     - `workflow` (Mettre à jour les workflows GitHub Action)
     - `read:org` (Lire les données de l'organisation)

2. **Entrer le Jeton dans OpenHands** :
   - Cliquez sur le bouton Paramètres (icône d'engrenage) en haut à droite
   - Accédez à la section "GitHub"
   - Collez votre jeton dans le champ "Jeton GitHub"
   - Cliquez sur "Enregistrer" pour appliquer les modifications

#### Politiques de Jetons Organisationnels

Si vous travaillez avec des dépôts organisationnels, une configuration supplémentaire peut être nécessaire :

1. **Vérifier les Exigences de l'Organisation** :
   - Les administrateurs de l'organisation peuvent appliquer des politiques de jetons spécifiques
   - Certaines organisations exigent que les jetons soient créés avec SSO activé
   - Consultez les [paramètres de politique de jetons](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization) de votre organisation

2. **Vérifier l'Accès à l'Organisation** :
   - Allez dans les paramètres de votre jeton sur GitHub
   - Recherchez l'organisation sous "Accès à l'organisation"
   - Si nécessaire, cliquez sur "Activer SSO" à côté de votre organisation
   - Terminez le processus d'autorisation SSO

#### Authentification OAuth (Mode En Ligne)

Lorsque vous utilisez OpenHands en mode en ligne, le flux OAuth GitHub :

1. Demande les autorisations suivantes :
   - Accès au dépôt (lecture/écriture)
   - Gestion des workflows
   - Accès en lecture à l'organisation

2. Étapes d'authentification :
   - Cliquez sur "Se connecter avec GitHub" lorsque vous y êtes invité
   - Examinez les autorisations demandées
   - Autorisez OpenHands à accéder à votre compte GitHub
   - Si vous utilisez une organisation, autorisez l'accès à l'organisation si vous y êtes invité

#### Dépannage

Problèmes courants et solutions :

1. **Jeton Non Reconnu** :
   - Assurez-vous que le jeton est correctement enregistré dans les paramètres
   - Vérifiez que le jeton n'a pas expiré
   - Vérifiez que le jeton a les portées requises
   - Essayez de régénérer le jeton

2. **Accès à l'Organisation Refusé** :
   - Vérifiez si SSO est requis mais non activé
   - Vérifiez l'appartenance à l'organisation
   - Contactez l'administrateur de l'organisation si les politiques de jetons bloquent l'accès

3. **Vérifier que le Jeton Fonctionne** :
   - L'application affichera une coche verte si le jeton est valide
   - Essayez d'accéder à un dépôt pour confirmer les autorisations
   - Vérifiez la console du navigateur pour tout message d'erreur
   - Utilisez le bouton "Tester la connexion" dans les paramètres s'il est disponible

### Paramètres Avancés

1. Basculez sur `Options Avancées` pour accéder aux paramètres supplémentaires.
2. Utilisez la zone de texte `Modèle Personnalisé` pour saisir manuellement un modèle s'il ne figure pas dans la liste.
3. Spécifiez une `URL de Base` si requis par votre fournisseur LLM.

### Interface Principale

L'interface principale se compose de plusieurs composants clés :

1. **Fenêtre de Chat** : La zone centrale où vous pouvez voir l'historique de conversation avec l'assistant IA.
2. **Zone de Saisie** : Située en bas de l'écran, utilisez-la pour taper vos messages ou commandes à l'IA.
3. **Bouton Envoyer** : Cliquez dessus pour envoyer votre message à l'IA.
4. **Bouton Paramètres** : Une icône d'engrenage qui ouvre la fenêtre modale des paramètres, vous permettant d'ajuster votre configuration à tout moment.
5. **Panneau Espace de Travail** : Affiche les fichiers et dossiers de votre espace de travail, vous permettant de naviguer et de visualiser les fichiers, ou les commandes passées de l'agent ou l'historique de navigation web.

### Interagir avec l'IA

1. Tapez votre question, demande ou description de tâche dans la zone de saisie.
2. Cliquez sur le bouton d'envoi ou appuyez sur Entrée pour soumettre votre message.
3. L'IA traitera votre saisie et fournira une réponse dans la fenêtre de chat.
4. Vous pouvez poursuivre la conversation en posant des questions de suivi ou en fournissant des informations supplémentaires.

## Conseils pour une Utilisation Efficace

1. Soyez précis dans vos demandes pour obtenir les réponses les plus précises et utiles, comme décrit dans les [meilleures pratiques d'incitation](../prompting/prompting-best-practices).
2. Utilisez le panneau d'espace de travail pour explorer la structure de votre projet.
3. Utilisez l'un des modèles recommandés, comme décrit dans la section [LLMs](usage/llms/llms.md).

N'oubliez pas que le mode Interface Graphique d'OpenHands est conçu pour rendre votre interaction avec l'assistant IA aussi fluide et intuitive que possible. N'hésitez pas à explorer ses fonctionnalités pour maximiser votre productivité.
