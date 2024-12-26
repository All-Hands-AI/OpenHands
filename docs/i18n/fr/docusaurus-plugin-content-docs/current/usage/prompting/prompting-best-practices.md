

# Meilleures pratiques pour les prompts

Lorsque vous travaillez avec le développeur de logiciels OpenHands AI, il est crucial de fournir des prompts clairs et efficaces. Ce guide décrit les meilleures pratiques pour créer des prompts qui produiront les réponses les plus précises et les plus utiles.

## Caractéristiques des bons prompts

Les bons prompts sont :

1. **Concrets** : Ils expliquent exactement quelle fonctionnalité doit être ajoutée ou quelle erreur doit être corrigée.
2. **Spécifiques à l'emplacement** : Si connu, ils expliquent les emplacements dans la base de code qui doivent être modifiés.
3. **Correctement dimensionnés** : Ils doivent avoir la taille d'une seule fonctionnalité, ne dépassant généralement pas 100 lignes de code.

## Exemples

### Exemples de bons prompts

1. "Ajoutez une fonction `calculate_average` dans `utils/math_operations.py` qui prend une liste de nombres en entrée et renvoie leur moyenne."

2. "Corrigez le TypeError dans `frontend/src/components/UserProfile.tsx` se produisant à la ligne 42. L'erreur suggère que nous essayons d'accéder à une propriété de undefined."

3. "Implémentez la validation des entrées pour le champ email dans le formulaire d'inscription. Mettez à jour `frontend/src/components/RegistrationForm.tsx` pour vérifier si l'email est dans un format valide avant la soumission."

### Exemples de mauvais prompts

1. "Améliorez le code." (Trop vague, pas concret)

2. "Réécrivez tout le backend pour utiliser un framework différent." (Pas correctement dimensionné)

3. "Il y a un bug quelque part dans l'authentification des utilisateurs. Pouvez-vous le trouver et le corriger ?" (Manque de spécificité et d'informations de localisation)

## Conseils pour des prompts efficaces

1. Soyez aussi précis que possible sur le résultat souhaité ou le problème à résoudre.
2. Fournissez du contexte, y compris les chemins de fichiers et les numéros de ligne pertinents si disponibles.
3. Décomposez les grandes tâches en prompts plus petits et gérables.
4. Incluez tous les messages d'erreur ou logs pertinents.
5. Spécifiez le langage de programmation ou le framework s'il n'est pas évident d'après le contexte.

N'oubliez pas, plus votre prompt est précis et informatif, mieux l'IA pourra vous aider à développer ou à modifier le logiciel OpenHands.

Voir [Démarrer avec OpenHands](../getting-started) pour plus d'exemples de prompts utiles.
