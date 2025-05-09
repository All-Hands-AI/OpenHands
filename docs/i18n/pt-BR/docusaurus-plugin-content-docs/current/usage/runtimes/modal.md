# Modal Runtime

Nossos parceiros da [Modal](https://modal.com/) forneceram um runtime para OpenHands.

Para usar o Modal Runtime, crie uma conta e, em seguida, [crie uma chave API.](https://modal.com/settings)

Você precisará definir as seguintes variáveis de ambiente ao iniciar o OpenHands:
```bash
docker run # ...
    -e RUNTIME=modal \
    -e MODAL_API_TOKEN_ID="seu-id" \
    -e MODAL_API_TOKEN_SECRET="sua-chave-api-modal" \
```
