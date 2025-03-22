# Documentação do OpenHands em Português Brasileiro

Esta pasta contém a tradução da documentação do OpenHands para o Português Brasileiro (pt-BR).

## Estrutura de Diretórios

- `docusaurus-plugin-content-docs/current/` - Contém as traduções dos documentos principais
- `docusaurus-theme-classic/` - Contém traduções de elementos da interface do usuário
- `code.json` - Contém traduções de strings de interface

## Contribuindo para a Tradução

Para contribuir com a tradução:

1. Faça um fork do repositório
2. Adicione ou atualize arquivos de tradução
3. Envie um pull request

## Executando Localmente

Para visualizar as traduções localmente:

```bash
cd docs
yarn start --locale pt-BR
```

## Atualizando Traduções

As traduções são atualizadas automaticamente quando o conteúdo original em inglês é alterado, usando o script `translation_updater.py`.

Para atualizar manualmente as traduções:

```bash
cd docs
export ANTHROPIC_API_KEY=seu_api_key
python translation_updater.py
```
