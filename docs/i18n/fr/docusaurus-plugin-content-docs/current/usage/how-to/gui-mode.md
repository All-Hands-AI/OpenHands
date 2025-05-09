# Mode GUI

OpenHands fournit un mode d'Interface Graphique Utilisateur (GUI) pour interagir avec l'assistant IA.

## Installation et Configuration

1. Suivez les instructions d'installation pour installer OpenHands.
2. Après avoir exécuté la commande, accédez à OpenHands à [http://localhost:3000](http://localhost:3000).

## Interagir avec l'interface graphique

### Configuration initiale

1. Lors du premier lancement, vous verrez une fenêtre de paramètres.
2. Sélectionnez un `Fournisseur LLM` et un `Modèle LLM` dans les menus déroulants. Si le modèle requis n'existe pas dans la liste,
   sélectionnez `voir les paramètres avancés`. Ensuite, activez les options `Avancées` et saisissez-le avec le préfixe correct dans la
   zone de texte `Modèle personnalisé`.
3. Entrez la `Clé API` correspondante pour le fournisseur choisi.
4. Cliquez sur `Enregistrer les modifications` pour appliquer les paramètres.

### Jetons de contrôle de version

OpenHands prend en charge plusieurs fournisseurs de contrôle de version. Vous pouvez configurer des jetons pour plusieurs fournisseurs simultanément.

#### Configuration du jeton GitHub

OpenHands exporte automatiquement un `GITHUB_TOKEN` vers l'environnement shell s'il est fourni :

<details>
  <summary>Configuration d'un jeton GitHub</summary>

  1. **Générer un jeton d'accès personnel (PAT)** :
   - Sur GitHub, allez dans Paramètres > Paramètres développeur > Jetons d'accès personnels > Jetons (classique).
   - **Nouveau jeton (classique)**
     - Portées requises :
     - `repo` (Contrôle complet des dépôts privés)
   - **Jetons à portée précise**
     - Tous les dépôts (Vous pouvez sélectionner des dépôts spécifiques, mais cela affectera les résultats de recherche)
     - Autorisations minimales (Sélectionnez `Meta Data = Lecture seule` pour la recherche, `Pull Requests = Lecture et écriture` et `Content = Lecture et écriture` pour la création de branches)
  2. **Entrer le jeton dans OpenHands** :
   - Cliquez sur le bouton Paramètres (icône d'engrenage).
   - Collez votre jeton dans le champ `Jeton GitHub`.
   - Cliquez sur `Enregistrer` pour appliquer les modifications.
</details>

<details>
  <summary>Politiques de jetons organisationnels</summary>

  Si vous travaillez avec des dépôts organisationnels, une configuration supplémentaire peut être nécessaire :

  1. **Vérifier les exigences de l'organisation** :
   - Les administrateurs de l'organisation peuvent imposer des politiques de jetons spécifiques.
   - Certaines organisations exigent que les jetons soient créés avec SSO activé.
   - Consultez les [paramètres de politique de jetons](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization) de votre organisation.
  2. **Vérifier l'accès à l'organisation** :
   - Accédez à vos paramètres de jeton sur GitHub.
   - Recherchez l'organisation sous `Accès à l'organisation`.
   - Si nécessaire, cliquez sur `Activer SSO` à côté de votre organisation.
   - Complétez le processus d'autorisation SSO.
</details>

<details>
  <summary>Dépannage</summary>

  Problèmes courants et solutions :

  - **Jeton non reconnu** :
     - Assurez-vous que le jeton est correctement enregistré dans les paramètres.
     - Vérifiez que le jeton n'a pas expiré.
     - Vérifiez que le jeton dispose des portées requises.
     - Essayez de régénérer le jeton.

  - **Accès à l'organisation refusé** :
     - Vérifiez si SSO est requis mais non activé.
     - Vérifiez l'appartenance à l'organisation.
     - Contactez l'administrateur de l'organisation si les politiques de jetons bloquent l'accès.

  - **Vérification du fonctionnement du jeton** :
     - L'application affichera une coche verte si le jeton est valide.
     - Essayez d'accéder à un dépôt pour confirmer les autorisations.
     - Vérifiez la console du navigateur pour tout message d'erreur.
</details>

#### Configuration du jeton GitLab

OpenHands exporte automatiquement un `GITLAB_TOKEN` vers l'environnement shell s'il est fourni :

<details>
  <summary>Configuration d'un jeton GitLab</summary>

  1. **Générer un jeton d'accès personnel (PAT)** :
   - Sur GitLab, allez dans Paramètres utilisateur > Jetons d'accès.
   - Créez un nouveau jeton avec les portées suivantes :
     - `api` (Accès API)
     - `read_user` (Lire les informations utilisateur)
     - `read_repository` (Lire le dépôt)
     - `write_repository` (Écrire dans le dépôt)
   - Définissez une date d'expiration ou laissez-la vide pour un jeton sans expiration.
  2. **Entrer le jeton dans OpenHands** :
   - Cliquez sur le bouton Paramètres (icône d'engrenage).
   - Collez votre jeton dans le champ `Jeton GitLab`.
   - Entrez l'URL de votre instance GitLab si vous utilisez GitLab auto-hébergé.
   - Cliquez sur `Enregistrer` pour appliquer les modifications.
</details>

<details>
  <summary>Dépannage</summary>

  Problèmes courants et solutions :

  - **Jeton non reconnu** :
     - Assurez-vous que le jeton est correctement enregistré dans les paramètres.
     - Vérifiez que le jeton n'a pas expiré.
     - Vérifiez que le jeton dispose des portées requises.
     - Pour les instances auto-hébergées, vérifiez l'URL correcte de l'instance.

  - **Accès refusé** :
     - Vérifiez les autorisations d'accès au projet.
     - Vérifiez si le jeton dispose des portées nécessaires.
     - Pour les dépôts de groupe/organisation, assurez-vous d'avoir un accès approprié.
</details>

### Paramètres avancés

1. Dans la page Paramètres, activez les options `Avancées` pour accéder aux paramètres supplémentaires.
2. Utilisez la zone de texte `Modèle personnalisé` pour saisir manuellement un modèle s'il n'est pas dans la liste.
3. Spécifiez une `URL de base` si requis par votre fournisseur LLM.

### Interagir avec l'IA

1. Tapez votre requête dans la zone de saisie.
2. Cliquez sur le bouton d'envoi ou appuyez sur Entrée pour soumettre votre message.
3. L'IA traitera votre saisie et fournira une réponse dans la fenêtre de discussion.
4. Vous pouvez poursuivre la conversation en posant des questions complémentaires ou en fournissant des informations supplémentaires.

## Conseils pour une utilisation efficace

- Soyez précis dans vos demandes pour obtenir les réponses les plus précises et utiles, comme décrit dans les [meilleures pratiques de prompt](../prompting/prompting-best-practices).
- Utilisez l'un des modèles recommandés, comme décrit dans la [section LLMs](usage/llms/llms.md).

N'oubliez pas que le mode GUI d'OpenHands est conçu pour rendre votre interaction avec l'assistant IA aussi fluide et intuitive
que possible. N'hésitez pas à explorer ses fonctionnalités pour maximiser votre productivité.
