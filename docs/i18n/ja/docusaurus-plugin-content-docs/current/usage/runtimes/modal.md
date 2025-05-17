# Modal ランタイム

[Modal](https://modal.com/)のパートナーがOpenHands用のランタイムを提供しています。

Modal ランタイムを使用するには、アカウントを作成し、[APIキーを作成してください。](https://modal.com/settings)

その後、OpenHandsを起動する際に以下の環境変数を設定する必要があります：
```bash
docker run # ...
    -e RUNTIME=modal \
    -e MODAL_API_TOKEN_ID="your-id" \
    -e MODAL_API_TOKEN_SECRET="modal-api-key" \
```
