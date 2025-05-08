# Meilleures pratiques pour les prompts

Lorsque vous travaillez avec le développeur IA OpenHands, fournir des prompts clairs et efficaces est essentiel pour obtenir des réponses précises et utiles. Ce guide présente les meilleures pratiques pour élaborer des prompts efficaces.

## Caractéristiques des bons prompts

Les bons prompts sont :

- **Concrets** : Décrivez clairement quelle fonctionnalité doit être ajoutée ou quelle erreur doit être corrigée.
- **Spécifiques à l'emplacement** : Précisez les emplacements dans la base de code qui doivent être modifiés, si connus.
- **Correctement délimités** : Concentrez-vous sur une seule fonctionnalité, ne dépassant généralement pas 100 lignes de code.

## Exemples

### Exemples de bons prompts

- Ajouter une fonction `calculate_average` dans `utils/math_operations.py` qui prend une liste de nombres en entrée et renvoie leur moyenne.
- Corriger le TypeError dans `frontend/src/components/UserProfile.tsx` qui se produit à la ligne 42. L'erreur suggère que nous essayons d'accéder à une propriété de undefined.
- Implémenter la validation des entrées pour le champ email dans le formulaire d'inscription. Mettre à jour `frontend/src/components/RegistrationForm.tsx` pour vérifier si l'email est dans un format valide avant la soumission.

### Exemples de mauvais prompts

- Améliorer le code. (Trop vague, pas concret)
- Réécrire tout le backend pour utiliser un framework différent. (Portée inappropriée)
- Il y a un bug quelque part dans l'authentification utilisateur. Pouvez-vous le trouver et le corriger ? (Manque de spécificité et d'informations sur l'emplacement)

## Conseils pour des prompts efficaces

- Soyez aussi précis que possible sur le résultat souhaité ou le problème à résoudre.
- Fournissez du contexte, y compris les chemins de fichiers pertinents et les numéros de ligne si disponibles.
- Décomposez les tâches importantes en prompts plus petits et gérables.
- Incluez les messages d'erreur ou les journaux pertinents.
- Précisez le langage de programmation ou le framework, si ce n'est pas évident.

Plus votre prompt est précis et informatif, mieux OpenHands pourra vous aider.

Voir [Démarrer avec OpenHands](../getting-started) pour plus d'exemples de prompts utiles.
