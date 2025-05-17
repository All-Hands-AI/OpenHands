# Melhores Práticas para Prompts

Ao trabalhar com o desenvolvedor de software OpenHands AI, fornecer prompts claros e eficazes é fundamental para obter respostas precisas
e úteis. Este guia descreve as melhores práticas para elaborar prompts eficazes.

## Características de Bons Prompts

Bons prompts são:

- **Concretos**: Descrevem claramente qual funcionalidade deve ser adicionada ou qual erro precisa ser corrigido.
- **Específicos quanto à localização**: Especificam os locais na base de código que devem ser modificados, se conhecidos.
- **Adequadamente delimitados**: Focam em uma única funcionalidade, geralmente não excedendo 100 linhas de código.

## Exemplos

### Exemplos de Bons Prompts

- Adicione uma função `calculate_average` em `utils/math_operations.py` que receba uma lista de números como entrada e retorne a média deles.
- Corrija o TypeError em `frontend/src/components/UserProfile.tsx` que ocorre na linha 42. O erro sugere que estamos tentando acessar uma propriedade de undefined.
- Implemente validação de entrada para o campo de e-mail no formulário de registro. Atualize `frontend/src/components/RegistrationForm.tsx` para verificar se o e-mail está em um formato válido antes do envio.

### Exemplos de Prompts Ruins

- Melhore o código. (Muito vago, não concreto)
- Reescreva todo o backend para usar um framework diferente. (Não adequadamente delimitado)
- Há um bug em algum lugar na autenticação do usuário. Você pode encontrá-lo e corrigi-lo? (Falta especificidade e informações de localização)

## Dicas para Prompts Eficazes

- Seja o mais específico possível sobre o resultado desejado ou o problema a ser resolvido.
- Forneça contexto, incluindo caminhos de arquivos relevantes e números de linha, se disponíveis.
- Divida tarefas grandes em prompts menores e gerenciáveis.
- Inclua mensagens de erro ou logs relevantes.
- Especifique a linguagem de programação ou framework, se não for óbvio.

Quanto mais precisos e informativos forem seus prompts, melhor o OpenHands poderá ajudá-lo.

Veja [Começando com OpenHands](../getting-started) para mais exemplos de prompts úteis.
