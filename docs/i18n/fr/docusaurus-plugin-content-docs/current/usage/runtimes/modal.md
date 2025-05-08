# Runtime Modal

Nos partenaires chez [Modal](https://modal.com/) ont fourni un runtime pour OpenHands.

Pour utiliser le Runtime Modal, créez un compte, puis [créez une clé API.](https://modal.com/settings)

Vous devrez ensuite définir les variables d'environnement suivantes lors du démarrage d'OpenHands :
```bash
docker run # ...
    -e RUNTIME=modal \
    -e MODAL_API_TOKEN_ID="your-id" \
    -e MODAL_API_TOKEN_SECRET="modal-api-key" \
```
