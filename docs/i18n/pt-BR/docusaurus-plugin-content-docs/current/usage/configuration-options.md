# Opções de Configuração

Este guia detalha todas as opções de configuração disponíveis para o OpenHands, ajudando você a personalizar seu comportamento e integrá-lo com outros serviços.

:::note
Se você estiver executando no [Modo GUI](https://docs.all-hands.dev/modules/usage/how-to/gui-mode), as configurações disponíveis na UI de Configurações sempre terão precedência.
:::

## Configuração Principal

As opções de configuração principais são definidas na seção `[core]` do arquivo `config.toml`.

### Chaves de API
- `e2b_api_key`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Chave de API para E2B

- `modal_api_token_id`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: ID do token de API para Modal

- `modal_api_token_secret`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Segredo do token de API para Modal

### Workspace
- `workspace_base`
  - Tipo: `str`
  - Padrão: `"./workspace"`
  - Descrição: Caminho base para o workspace

- `cache_dir`
  - Tipo: `str`
  - Padrão: `"/tmp/cache"`
  - Descrição: Caminho do diretório de cache

### Depuração e Log
- `debug`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Habilitar depuração

- `disable_color`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Desabilitar cor na saída do terminal

### Trajetórias
- `save_trajectory_path`
  - Tipo: `str`
  - Padrão: `"./trajectories"`
  - Descrição: Caminho para armazenar trajetórias (pode ser uma pasta ou um arquivo). Se for uma pasta, as trajetórias serão salvas em um arquivo nomeado com o nome do id da sessão e extensão .json, nessa pasta.

- `replay_trajectory_path`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Caminho para carregar uma trajetória e reproduzir. Se fornecido, deve ser um caminho para o arquivo de trajetória no formato JSON. As ações no arquivo de trajetória seriam reproduzidas primeiro antes de qualquer instrução do usuário ser executada.

### Armazenamento de Arquivos
- `file_store_path`
  - Tipo: `str`
  - Padrão: `"/tmp/file_store"`
  - Descrição: Caminho do armazenamento de arquivos

- `file_store`
  - Tipo: `str`
  - Padrão: `"memory"`
  - Descrição: Tipo de armazenamento de arquivos

- `file_uploads_allowed_extensions`
  - Tipo: `list of str`
  - Padrão: `[".*"]`
  - Descrição: Lista de extensões de arquivo permitidas para uploads

- `file_uploads_max_file_size_mb`
  - Tipo: `int`
  - Padrão: `0`
  - Descrição: Tamanho máximo de arquivo para uploads, em megabytes

- `file_uploads_restrict_file_types`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Restringir tipos de arquivo para uploads de arquivos

- `file_uploads_allowed_extensions`
  - Tipo: `list of str`
  - Padrão: `[".*"]`
  - Descrição: Lista de extensões de arquivo permitidas para uploads

### Gerenciamento de Tarefas
- `max_budget_per_task`
  - Tipo: `float`
  - Padrão: `0.0`
  - Descrição: Orçamento máximo por tarefa (0.0 significa sem limite)

- `max_iterations`
  - Tipo: `int`
  - Padrão: `100`
  - Descrição: Número máximo de iterações

### Configuração do Sandbox
- `workspace_mount_path_in_sandbox`
  - Tipo: `str`
  - Padrão: `"/workspace"`
  - Descrição: Caminho para montar o workspace no sandbox

- `workspace_mount_path`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Caminho para montar o workspace

- `workspace_mount_rewrite`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Caminho para reescrever o caminho de montagem do workspace. Você geralmente pode ignorar isso, refere-se a casos especiais de execução dentro de outro contêiner.

### Diversos
- `run_as_openhands`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Executar como OpenHands

- `runtime`
  - Tipo: `str`
  - Padrão: `"docker"`
  - Descrição: Ambiente de execução

- `default_agent`
  - Tipo: `str`
  - Padrão: `"CodeActAgent"`
  - Descrição: Nome do agente padrão

- `jwt_secret`
  - Tipo: `str`
  - Padrão: `uuid.uuid4().hex`
  - Descrição: Segredo JWT para autenticação. Por favor, defina seu próprio valor.

## Configuração do LLM

As opções de configuração do LLM (Large Language Model) são definidas na seção `[llm]` do arquivo `config.toml`.

Para usá-las com o comando docker, passe `-e LLM_<opção>`. Exemplo: `-e LLM_NUM_RETRIES`.

:::note
Para configurações de desenvolvimento, você também pode definir configurações de LLM personalizadas nomeadas. Veja [Configurações Personalizadas de LLM](./llms/custom-llm-configs) para detalhes.
:::

**Credenciais AWS**
- `aws_access_key_id`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: ID da chave de acesso AWS

- `aws_region_name`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Nome da região AWS

- `aws_secret_access_key`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Chave secreta de acesso AWS

### Configuração da API
- `api_key`
  - Tipo: `str`
  - Padrão: `None`
  - Descrição: Chave de API a ser usada

- `base_url`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: URL base da API

- `api_version`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Versão da API

- `input_cost_per_token`
  - Tipo: `float`
  - Padrão: `0.0`
  - Descrição: Custo por token de entrada

- `output_cost_per_token`
  - Tipo: `float`
  - Padrão: `0.0`
  - Descrição: Custo por token de saída

### Provedor LLM Personalizado
- `custom_llm_provider`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Provedor LLM personalizado


### Tratamento de Mensagens
- `max_message_chars`
  - Tipo: `int`
  - Padrão: `30000`
  - Descrição: O número máximo aproximado de caracteres no conteúdo de um evento incluído no prompt para o LLM. Observações maiores são truncadas.

- `max_input_tokens`
  - Tipo: `int`
  - Padrão: `0`
  - Descrição: Número máximo de tokens de entrada

- `max_output_tokens`
  - Tipo: `int`
  - Padrão: `0`
  - Descrição: Número máximo de tokens de saída

### Seleção de Modelo
- `model`
  - Tipo: `str`
  - Padrão: `"claude-3-5-sonnet-20241022"`
  - Descrição: Modelo a ser usado

### Tentativas
- `num_retries`
  - Tipo: `int`
  - Padrão: `8`
  - Descrição: Número de tentativas a serem feitas

- `retry_max_wait`
  - Tipo: `int`
  - Padrão: `120`
  - Descrição: Tempo máximo de espera (em segundos) entre tentativas

- `retry_min_wait`
  - Tipo: `int`
  - Padrão: `15`
  - Descrição: Tempo mínimo de espera (em segundos) entre tentativas

- `retry_multiplier`
  - Tipo: `float`
  - Padrão: `2.0`
  - Descrição: Multiplicador para cálculo de backoff exponencial

### Opções Avançadas
- `drop_params`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Descartar quaisquer parâmetros não mapeados (não suportados) sem causar uma exceção

- `caching_prompt`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Usar o recurso de cache de prompt se fornecido pelo LLM e suportado

- `ollama_base_url`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: URL base para a API OLLAMA

- `temperature`
  - Tipo: `float`
  - Padrão: `0.0`
  - Descrição: Temperatura para a API

- `timeout`
  - Tipo: `int`
  - Padrão: `0`
  - Descrição: Timeout para a API

- `top_p`
  - Tipo: `float`
  - Padrão: `1.0`
  - Descrição: Top p para a API

- `disable_vision`
  - Tipo: `bool`
  - Padrão: `None`
  - Descrição: Se o modelo é capaz de visão, esta opção permite desabilitar o processamento de imagem (útil para redução de custo)

## Configuração do Agente

As opções de configuração do agente são definidas nas seções `[agent]` e `[agent.<agent_name>]` do arquivo `config.toml`.

### Configuração do LLM
- `llm_config`
  - Tipo: `str`
  - Padrão: `'your-llm-config-group'`
  - Descrição: O nome da configuração LLM a ser usada

### Configuração do Espaço de Ação
- `function_calling`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Se a chamada de função está habilitada

- `enable_browsing`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Se o delegado de navegação está habilitado no espaço de ação (funciona apenas com chamada de função)

- `enable_llm_editor`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Se o editor LLM está habilitado no espaço de ação (funciona apenas com chamada de função)

- `enable_jupyter`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Se o Jupyter está habilitado no espaço de ação

- `enable_history_truncation`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Se o histórico deve ser truncado para continuar a sessão ao atingir o limite de comprimento de contexto do LLM

### Uso de Microagentes
- `enable_prompt_extensions`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Se deve usar microagentes

- `disabled_microagents`
  - Tipo: `list of str`
  - Padrão: `None`
  - Descrição: Uma lista de microagentes a serem desabilitados

## Configuração do Sandbox

As opções de configuração do sandbox são definidas na seção `[sandbox]` do arquivo `config.toml`.

Para usá-las com o comando docker, passe `-e SANDBOX_<opção>`. Exemplo: `-e SANDBOX_TIMEOUT`.

### Execução
- `timeout`
  - Tipo: `int`
  - Padrão: `120`
  - Descrição: Timeout do sandbox em segundos

- `user_id`
  - Tipo: `int`
  - Padrão: `1000`
  - Descrição: ID do usuário do sandbox

### Imagem do Contêiner
- `base_container_image`
  - Tipo: `str`
  - Padrão: `"nikolaik/python-nodejs:python3.12-nodejs22"`
  - Descrição: Imagem do contêiner a ser usada para o sandbox

### Rede
- `use_host_network`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Usar a rede do host

- `runtime_binding_address`
  - Tipo: `str`
  - Padrão: `0.0.0.0`
  - Descrição: O endereço de ligação para as portas de tempo de execução. Especifica em qual interface de rede na máquina host o Docker deve ligar as portas de tempo de execução.

### Linting e Plugins
- `enable_auto_lint`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Habilitar linting automático após a edição

- `initialize_plugins`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Se deve inicializar plugins

### Dependências e Ambiente
- `runtime_extra_deps`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Dependências extras a serem instaladas na imagem de tempo de execução

- `runtime_startup_env_vars`
  - Tipo: `dict`
  - Padrão: `{}`
  - Descrição: Variáveis de ambiente a serem definidas no lançamento do tempo de execução

### Avaliação
- `browsergym_eval_env`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Ambiente BrowserGym a ser usado para avaliação

## Configuração de Segurança

As opções de configuração de segurança são definidas na seção `[security]` do arquivo `config.toml`.

Para usá-las com o comando docker, passe `-e SECURITY_<opção>`. Exemplo: `-e SECURITY_CONFIRMATION_MODE`.

### Modo de Confirmação
- `confirmation_mode`
  - Tipo
