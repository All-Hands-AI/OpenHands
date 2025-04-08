# Modal ランタイム

[Modal](https://modal.com/) のパートナーが OpenHands 用のランタイムを提供しています。

Modal ランタイムを使用するには、アカウントを作成し、[API キーを作成](https://modal.com/settings)してください。

その後、OpenHands を起動するときに以下の環境変数を設定する必要があります：
```bash
docker run # ...
    -e RUNTIME=modal \
    -e MODAL_API_TOKEN_ID="your-id" \
    -e MODAL_API_TOKEN_SECRET="your-secret" \
```
