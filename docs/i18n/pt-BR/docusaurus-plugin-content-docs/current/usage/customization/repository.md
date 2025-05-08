# Personalização do Repositório

Você pode personalizar como o OpenHands interage com seu repositório criando um
diretório `.openhands` no nível raiz.

## Microagentes

Os microagentes permitem que você estenda os prompts do OpenHands com informações específicas do seu projeto e defina como o OpenHands
deve funcionar. Veja [Visão Geral dos Microagentes](../prompting/microagents-overview) para mais informações.


## Script de Configuração
Você pode adicionar um arquivo `.openhands/setup.sh`, que será executado toda vez que o OpenHands começar a trabalhar com seu repositório.
Este é um local ideal para instalar dependências, definir variáveis de ambiente e realizar outras tarefas de configuração.

Por exemplo:
```bash
#!/bin/bash
export MY_ENV_VAR="my value"
sudo apt-get update
sudo apt-get install -y lsof
cd frontend && npm install ; cd ..
```
