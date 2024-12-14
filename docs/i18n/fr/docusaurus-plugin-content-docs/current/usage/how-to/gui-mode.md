

# Mode Interface Graphique

## Introduction

OpenHands fournit un mode Interface Graphique (GUI) convivial pour interagir avec l'assistant IA. Ce mode offre une façon intuitive de configurer l'environnement, gérer les paramètres et communiquer avec l'IA.

## Installation et Configuration

1. Suivez les instructions du guide d'[Installation](../installation) pour installer OpenHands.

2. Après avoir exécuté la commande, accédez à OpenHands à l'adresse [http://localhost:3000](http://localhost:3000).

## Interagir avec l'Interface Graphique

### Configuration Initiale

1. Lors du premier lancement, vous verrez une fenêtre modale de paramètres.
2. Sélectionnez un `Fournisseur LLM` et un `Modèle LLM` dans les menus déroulants.
3. Entrez la `Clé API` correspondante pour le fournisseur choisi.
4. Cliquez sur "Enregistrer" pour appliquer les paramètres.

### Paramètres Avancés

1. Activez `Options Avancées` pour accéder aux paramètres supplémentaires.
2. Utilisez la zone de texte `Modèle Personnalisé` pour entrer manuellement un modèle s'il n'est pas dans la liste.
3. Spécifiez une `URL de Base` si requise par votre fournisseur LLM.

### Interface Principale

L'interface principale se compose de plusieurs éléments clés :

1. **Fenêtre de Chat** : La zone centrale où vous pouvez voir l'historique de conversation avec l'assistant IA.
2. **Zone de Saisie** : Située en bas de l'écran, utilisez-la pour taper vos messages ou commandes à l'IA.
3. **Bouton Envoyer** : Cliquez dessus pour envoyer votre message à l'IA.
4. **Bouton Paramètres** : Une icône d'engrenage qui ouvre la fenêtre modale des paramètres, vous permettant d'ajuster votre configuration à tout moment.
5. **Panneau Espace de Travail** : Affiche les fichiers et dossiers de votre espace de travail, vous permettant de naviguer et visualiser les fichiers, ou l'historique des commandes passées de l'agent ou de navigation web.

### Interagir avec l'IA

1. Tapez votre question, requête ou description de tâche dans la zone de saisie.
2. Cliquez sur le bouton envoyer ou appuyez sur Entrée pour soumettre votre message.
3. L'IA traitera votre saisie et fournira une réponse dans la fenêtre de chat.
4. Vous pouvez poursuivre la conversation en posant des questions de suivi ou en fournissant des informations supplémentaires.

## Conseils pour une Utilisation Efficace

1. Soyez spécifique dans vos requêtes pour obtenir les réponses les plus précises et utiles, comme décrit dans les [meilleures pratiques d'invite](../prompting-best-practices).
2. Utilisez le panneau d'espace de travail pour explorer la structure de votre projet.
3. Utilisez l'un des modèles recommandés, comme décrit dans la section [LLMs](usage/llms/llms.md).

N'oubliez pas, le mode Interface Graphique d'OpenHands est conçu pour rendre votre interaction avec l'assistant IA aussi fluide et intuitive que possible. N'hésitez pas à explorer ses fonctionnalités pour maximiser votre productivité.
