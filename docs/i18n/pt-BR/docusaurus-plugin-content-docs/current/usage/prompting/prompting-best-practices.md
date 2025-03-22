# Melhores Práticas de Prompt

Ao trabalhar com o desenvolvedor de software OpenHands AI, é crucial fornecer prompts claros e eficazes. Este guia descreve as melhores práticas para criar prompts que produzirão as respostas mais precisas e úteis.

## Características de Bons Prompts

Bons prompts são:

- **Concretos**: Eles explicam exatamente qual funcionalidade deve ser adicionada ou qual erro precisa ser corrigido.
- **Específicos de localização**: Se conhecido, eles explicam os locais na base de código que devem ser modificados.
- **Escopo apropriado**: Eles devem ter o tamanho de uma única funcionalidade, normalmente não excedendo 100 linhas de código.

## Exemplos

### Exemplos de Bons Prompts

- "Adicione uma função `calculate_average` em `utils/math_operations.py` que recebe uma lista de números como entrada e retorna sua média."
- "Corrija o TypeError em `frontend/src/components/UserProfile.tsx` ocorrendo na linha 42. O erro sugere que estamos tentando acessar uma propriedade de undefined."
- "Implemente a validação de entrada para o campo de e-mail no formulário de registro. Atualize `frontend/src/components/RegistrationForm.tsx` para verificar se o e-mail está em um formato válido antes do envio."

### Exemplos de Maus Prompts

- "Torne o código melhor." (Muito vago, não concreto)
- "Reescreva todo o backend para usar um framework diferente." (Escopo não apropriado)
- "Há um bug em algum lugar na autenticação do usuário. Você pode encontrá-lo e corrigi-lo?" (Falta especificidade e informações de localização)

## Dicas para Prompts Eficazes

- Seja o mais específico possível sobre o resultado desejado ou o problema a ser resolvido.
- Forneça contexto, incluindo caminhos de arquivo relevantes e números de linha, se disponíveis.
- Divida tarefas grandes em prompts menores e gerenciáveis.
- Inclua quaisquer mensagens de erro ou logs relevantes.
- Especifique a linguagem de programação ou framework se não for óbvio a partir do contexto.

Lembre-se, quanto mais preciso e informativo for o seu prompt, melhor a IA poderá ajudá-lo a desenvolver ou modificar o software OpenHands.

Veja [Começando com o OpenHands](../getting-started) para mais exemplos de prompts úteis.
