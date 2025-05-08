# 🧠 Agente Principal e Capacidades

## CodeActAgent

### Descrição

Este agente implementa a ideia CodeAct ([artigo](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) que consolida as **aç**ões dos agentes LLM em um
espaço de ação de **código** unificado para obter tanto _simplicidade_ quanto _desempenho_.

A ideia conceitual é ilustrada abaixo. A cada turno, o agente pode:

1. **Conversar**: Comunicar-se com humanos em linguagem natural para pedir esclarecimentos, confirmação, etc.
2. **CodeAct**: Escolher realizar a tarefa executando código

- Executar qualquer comando `bash` válido do Linux
- Executar qualquer código `Python` válido com [um interpretador Python interativo](https://ipython.org/). Isso é simulado através do comando `bash`, veja o sistema de plugins abaixo para mais detalhes.

![image](https://github.com/All-Hands-AI/OpenHands/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### Demonstração

https://github.com/All-Hands-AI/OpenHands/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

_Exemplo do CodeActAgent com `gpt-4-turbo-2024-04-09` realizando uma tarefa de ciência de dados (regressão linear)_.
