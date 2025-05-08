# Configuration d'exécution

:::note
Cette section est destinée aux utilisateurs qui souhaitent utiliser un environnement d'exécution autre que Docker pour OpenHands.
:::

Un environnement d'exécution est un environnement où l'agent OpenHands peut modifier des fichiers et exécuter des commandes.

Par défaut, OpenHands utilise un [environnement d'exécution basé sur Docker](./runtimes/docker), fonctionnant sur votre ordinateur local.
Cela signifie que vous ne payez que pour le LLM que vous utilisez, et votre code n'est jamais envoyé qu'au LLM.

Nous prenons également en charge d'autres environnements d'exécution, qui sont généralement gérés par des tiers.

De plus, nous fournissons un [Environnement d'exécution local](./runtimes/local) qui s'exécute directement sur votre machine sans Docker,
ce qui peut être utile dans des environnements contrôlés comme les pipelines CI.

## Environnements d'exécution disponibles

OpenHands prend en charge plusieurs environnements d'exécution différents :

- [Environnement Docker](./runtimes/docker.md) - L'environnement d'exécution par défaut qui utilise des conteneurs Docker pour l'isolation (recommandé pour la plupart des utilisateurs).
- [Environnement distant OpenHands](./runtimes/remote.md) - Environnement d'exécution basé sur le cloud pour l'exécution parallèle (bêta).
- [Environnement Modal](./runtimes/modal.md) - Environnement d'exécution fourni par nos partenaires chez Modal.
- [Environnement Daytona](./runtimes/daytona.md) - Environnement d'exécution fourni par Daytona.
- [Environnement local](./runtimes/local.md) - Exécution directe sur votre machine locale sans Docker.
