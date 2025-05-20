# Opções de Configuração

:::note
Esta página descreve todas as opções de configuração disponíveis para o OpenHands, permitindo que você personalize seu comportamento e
o integre com outros serviços. No Modo GUI, quaisquer configurações aplicadas através da interface de Configurações terão precedência.
:::

## Configuração Principal

As opções de configuração principal são definidas na seção `[core]` do arquivo `config.toml`.

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

### Espaço de Trabalho
- `workspace_base` **(Obsoleto)**
  - Tipo: `str`
  - Padrão: `"./workspace"`
  - Descrição: Caminho base para o espaço de trabalho. **Obsoleto: Use `SANDBOX_VOLUMES` em vez disso.**

- `cache_dir`
  - Tipo: `str`
  - Padrão: `"/tmp/cache"`
  - Descrição: Caminho do diretório de cache

### Depuração e Registro
- `debug`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Ativar depuração

- `disable_color`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Desativar cores na saída do terminal

### Trajetórias
- `save_trajectory_path`
  - Tipo: `str`
  - Padrão: `"./trajectories"`
  - Descrição: Caminho para armazenar trajetórias (pode ser uma pasta ou um arquivo). Se for uma pasta, as trajetórias serão salvas em um arquivo nomeado com o ID da sessão e extensão .json, nessa pasta.

- `replay_trajectory_path`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Caminho para carregar uma trajetória e reproduzir. Se fornecido, deve ser um caminho para o arquivo de trajetória em formato JSON. As ações no arquivo de trajetória serão reproduzidas primeiro antes que qualquer instrução do usuário seja executada.

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
  - Tipo: `lista de str`
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
  - Tipo: `lista de str`
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

### Configuração da Sandbox
- `volumes`
  - Tipo: `str`
  - Padrão: `None`
  - Descrição: Montagens de volume no formato 'caminho_host:caminho_container[:modo]', ex. '/meu/dir/host:/workspace:rw'. Múltiplas montagens podem ser especificadas usando vírgulas, ex. '/caminho1:/workspace/caminho1,/caminho2:/workspace/caminho2:ro'

- `workspace_mount_path_in_sandbox` **(Obsoleto)**
  - Tipo: `str`
  - Padrão: `"/workspace"`
  - Descrição: Caminho para montar o espaço de trabalho na sandbox. **Obsoleto: Use `SANDBOX_VOLUMES` em vez disso.**

- `workspace_mount_path` **(Obsoleto)**
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Caminho para montar o espaço de trabalho. **Obsoleto: Use `SANDBOX_VOLUMES` em vez disso.**

- `workspace_mount_rewrite` **(Obsoleto)**
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Caminho para reescrever o caminho de montagem do espaço de trabalho. Você geralmente pode ignorar isso, refere-se a casos especiais de execução dentro de outro contêiner. **Obsoleto: Use `SANDBOX_VOLUMES` em vez disso.**

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

Para usar estas com o comando docker, passe `-e LLM_<opção>`. Exemplo: `-e LLM_NUM_RETRIES`.

:::note
Para configurações de desenvolvimento, você também pode definir configurações de LLM personalizadas com nomes. Veja [Configurações Personalizadas de LLM](./llms/custom-llm-configs) para detalhes.
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
  - Descrição: Chave de acesso secreta AWS

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

### Provedor de LLM Personalizado
- `custom_llm_provider`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Provedor de LLM personalizado

### Manipulação de Mensagens
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

### Repetição de Tentativas
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
  - Descrição: Multiplicador para cálculo de recuo exponencial

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
  - Descrição: Tempo limite para a API

- `top_p`
  - Tipo: `float`
  - Padrão: `1.0`
  - Descrição: Top p para a API

- `disable_vision`
  - Tipo: `bool`
  - Padrão: `None`
  - Descrição: Se o modelo for capaz de visão, esta opção permite desativar o processamento de imagens (útil para redução de custos)

## Configuração do Agente

As opções de configuração do agente são definidas nas seções `[agent]` e `[agent.<nome_do_agente>]` do arquivo `config.toml`.

### Configuração do LLM
- `llm_config`
  - Tipo: `str`
  - Padrão: `'your-llm-config-group'`
  - Descrição: O nome da configuração de LLM a ser usada

### Configuração do Espaço de Ações
- `function_calling`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Se a chamada de função está habilitada

- `enable_browsing`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Se o delegado de navegação está habilitado no espaço de ações (funciona apenas com chamada de função)

- `enable_llm_editor`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Se o editor LLM está habilitado no espaço de ações (funciona apenas com chamada de função)

- `enable_jupyter`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Se o Jupyter está habilitado no espaço de ações

- `enable_history_truncation`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Se o histórico deve ser truncado para continuar a sessão quando atingir o limite de comprimento de contexto do LLM

### Uso de Microagentes
- `enable_prompt_extensions`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Se deve usar microagentes

- `disabled_microagents`
  - Tipo: `lista de str`
  - Padrão: `None`
  - Descrição: Uma lista de microagentes para desativar

## Configuração da Sandbox

As opções de configuração da sandbox são definidas na seção `[sandbox]` do arquivo `config.toml`.

Para usar estas com o comando docker, passe `-e SANDBOX_<opção>`. Exemplo: `-e SANDBOX_TIMEOUT`.

### Execução
- `timeout`
  - Tipo: `int`
  - Padrão: `120`
  - Descrição: Tempo limite da sandbox em segundos

- `user_id`
  - Tipo: `int`
  - Padrão: `1000`
  - Descrição: ID de usuário da sandbox

### Imagem do Contêiner
- `base_container_image`
  - Tipo: `str`
  - Padrão: `"nikolaik/python-nodejs:python3.12-nodejs22"`
  - Descrição: Imagem do contêiner a ser usada para a sandbox

### Rede
- `use_host_network`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Usar rede do host

- `runtime_binding_address`
  - Tipo: `str`
  - Padrão: `0.0.0.0`
  - Descrição: O endereço de vinculação para as portas de runtime. Especifica qual interface de rede na máquina host o Docker deve vincular as portas de runtime.

### Linting e Plugins
- `enable_auto_lint`
  - Tipo: `bool`
  - Padrão: `false`
  - Descrição: Habilitar linting automático após edição

- `initialize_plugins`
  - Tipo: `bool`
  - Padrão: `true`
  - Descrição: Se deve inicializar plugins

### Dependências e Ambiente
- `runtime_extra_deps`
  - Tipo: `str`
  - Padrão: `""`
  - Descrição: Dependências extras para instalar na imagem de runtime

- `runtime_startup_env_vars`
  - Tipo: `dict`
  - Padr
