# Integração MCP

Este documento descreve como o Geo-Explorer disponibiliza suas funcionalidades
como ferramentas MCP para um cliente compatível. O servidor oferece uma
interface de chamada para operações já implementadas; **não executa modelos
nem agentes de IA**.

Consulte também o [README](../README.md), o [índice da documentação](index.md)
e a [visão de arquitetura](architecture.md).

## Arquitetura e inicialização

O ponto de entrada é [mcp_server/server.py](../mcp_server/server.py). A função
`create_server()` cria um `MCPServer` chamado `geo-explorer`, versão `1.0.0`,
e registra as quatro ferramentas por meio de
[register_all_tools()](../mcp_server/tools/__init__.py). `main()` chama
`create_server()` e inicia `mcp.run()`.

O registro é feito por decorators `@mcp.tool()` nas funções de
[mcp_server/tools/](../mcp_server/tools/). Os nomes das ferramentas são os
nomes dessas funções. Os adaptadores chamam funções de `commands/` e `core/`;
[formatters.py](../mcp_server/formatters.py) converte modelos e valores de
domínio em dicionários serializáveis.

## Transporte e execução

O servidor usa o transporte **stdio** padrão do SDK. O processo é iniciado
pelo cliente MCP, que se comunica com ele pela entrada e saída padrão. A saída
padrão é reservada às mensagens do protocolo; o servidor envia diagnósticos
por logging para stderr.

Com as dependências do projeto instaladas no ambiente Python que será usado
pelo cliente, o comando do processo é:

```powershell
python -m mcp_server.server
```

Inicie o processo pela configuração de servidor MCP do cliente, não como uma
API HTTP. O diretório de trabalho deve permitir que Python importe o pacote
`mcp_server`; use a raiz do projeto e o mesmo ambiente virtual em que as
dependências foram instaladas.

### Exemplo conceitual de configuração

Os nomes dos campos, a sintaxe e o formato do arquivo variam por cliente. O
exemplo abaixo descreve os valores que uma configuração equivalente precisa
fornecer; não é um arquivo pronto para um cliente específico:

```text
comando: <interpretador Python do ambiente virtual>
argumentos:
  - -m
  - mcp_server.server
diretório de trabalho: <raiz do Geo-Explorer>
transporte: stdio
```

Não é necessário configurar endpoint ou porta HTTP. Não há servidor HTTP
implementado no projeto.

## Dependências

As dependências declaradas em [requirements.txt](../requirements.txt) são:

```text
mcp>=2,<3
streamlit>=1.67,<2
pytest>=8.0
```

Para executar o servidor MCP, a dependência direta relevante é `mcp`. O arquivo
de requisitos instala também as dependências da GUI e de testes. As versões
são faixas, não versões exatas. Não há dependência de modelo de IA ou de
cliente MCP específico declarada pelo Geo-Explorer.

## Ferramentas registradas

Todas as assinaturas abaixo são as funções registradas nos decorators
`@mcp.tool()`. Todos os parâmetros têm anotação de tipo e são obrigatórios:
nenhuma dessas assinaturas declara valor padrão. Um parâmetro obrigatório de
lista ainda pode aceitar uma lista vazia quando indicado.

As estruturas de retorno descritas são os dicionários de aplicação produzidos
pelas funções e formatters do projeto. O cliente MCP recebe esses resultados
por meio do protocolo; os detalhes de envelope e apresentação dependem do
cliente.

### `get_learning_path`

**Assinatura registrada**

```python
get_learning_path(technology: str) -> dict
```

| Parâmetro | Tipo | Obrigatório | Regras |
|---|---|---:|---|
| `technology` | `str` | Sim | Não pode ser vazio ou conter apenas espaços. A busca ignora maiúsculas/minúsculas. |

**Comportamento:** carrega as trilhas locais, procura a primeira que
corresponda à tecnologia e devolve seus dados. Exemplo válido:

```json
{"technology": "Python"}
```

**Retorno de sucesso:** um objeto de trilha com `id`, `title`, `technology`,
`level` como texto, `description`, `steps` e `competencies`. Cada item de
`steps` contém `order`, `title`, `description` e `competencies_developed`.
As etapas são serializadas em ordem.

**Erros retornados como dicionário:**

- tecnologia vazia: `{"error": "Parameter 'technology' must not be empty."}`;
- nenhuma trilha correspondente: `{"error": "No learning path found for technology: '<tecnologia>'."}`.

Falhas de leitura ou validação do catálogo não são convertidas por essa
ferramenta em um dicionário `error`; as exceções do carregador podem propagar
para o tratamento do SDK.

### `get_challenge`

**Assinatura registrada**

```python
get_challenge(technology: str, level: str) -> dict
```

| Parâmetro | Tipo | Obrigatório | Regras |
|---|---|---:|---|
| `technology` | `str` | Sim | Não pode ser vazio ou conter apenas espaços. A comparação ignora maiúsculas/minúsculas. |
| `level` | `str` | Sim | Após remover espaços externos e converter para minúsculas, deve ser `beginner`, `intermediate` ou `advanced`. |

**Comportamento:** carrega `data/challenges.json`, filtra por tecnologia e
nível e seleciona aleatoriamente um dos desafios correspondentes. A seleção
pode variar entre chamadas. Exemplo válido:

```json
{"technology": "Python", "level": "beginner"}
```

**Retorno de sucesso:** um objeto com `id`, `title`, `technology`, `level`
como texto, `description`, `evaluation_criteria`, `competencies_assessed` e
`estimated_hours`. O último campo pode ser `null` quando não há estimativa.

**Erros retornados como dicionário:**

- tecnologia vazia: `{"error": "Parameter 'technology' must not be empty."}`;
- nível inválido: `{"error": "Invalid level '<valor>'. Valid values: beginner, intermediate, advanced."}`;
- nenhum resultado: `{"error": "No challenge found for technology '<tecnologia>' at level '<nível>'."}`.

Erros de leitura ou validação do catálogo não são convertidos em um dicionário
`error` por essa ferramenta.

### `generate_certificate`

**Assinatura registrada**

```python
generate_certificate(
    participant: str,
    activity: str,
    technology: str,
    level: str,
    competencies: list[str],
) -> dict
```

| Parâmetro | Tipo | Obrigatório | Regras |
|---|---|---:|---|
| `participant` | `str` | Sim | Não pode ser vazio ou conter apenas espaços. |
| `activity` | `str` | Sim | Não pode ser vazio ou conter apenas espaços. |
| `technology` | `str` | Sim | A assinatura exige o texto; a implementação não valida se ele corresponde ao catálogo nem rejeita texto vazio. |
| `level` | `str` | Sim | Após remover espaços externos e converter para minúsculas, deve ser `beginner`, `intermediate` ou `advanced`. |
| `competencies` | `list[str]` | Sim | Pode ser uma lista vazia. |

Não há parâmetro MCP para data de emissão: o builder usa a data atual. Exemplo
válido com a trilha Python do catálogo:

```json
{
  "participant": "Ana Exemplo",
  "activity": "Python Foundations",
  "technology": "Python",
  "level": "beginner",
  "competencies": ["Python syntax and semantics", "control flow"]
}
```

**Retorno de sucesso:** `id`, `participant`, `activity`, `technology`,
`level`, `issued_on`, `competencies`, `disclaimer` e `recognition`.
`issued_on` é serializado como data ISO-8601; o identificador é criado pelo
builder. O disclaimer é
`CERTIFICADO FICTÍCIO — SEM VALIDADE OFICIAL`.

**Erros retornados como dicionário:** participante vazio, atividade vazia ou
nível inválido resultam em `{"error": "<mensagem>"}`. As mensagens definidas
pelo código são, respectivamente, `Participant name must not be empty.`,
`Activity name must not be empty.` e
`Invalid level '<valor>'. Valid values: beginner, intermediate, advanced.`

O certificado é fictício e não tem validade oficial. Esta ferramenta retorna
dados; não gera PDF ou arquivo de exportação.

### `analyze_competencies`

**Assinatura registrada**

```python
analyze_competencies(
    competencies: list[str],
    level: str,
    goal: str,
    technologies_of_interest: list[str],
) -> dict
```

| Parâmetro | Tipo | Obrigatório | Regras |
|---|---|---:|---|
| `competencies` | `list[str]` | Sim | Pode ser vazia; os valores são tratados como competências informadas pela pessoa. |
| `level` | `str` | Sim | Após remover espaços externos e converter para minúsculas, deve ser `beginner`, `intermediate` ou `advanced`. |
| `goal` | `str` | Sim | Pode ser vazia. É armazenada no perfil de entrada, mas o analisador atual não a usa para calcular correspondências, prioridades ou recomendações. |
| `technologies_of_interest` | `list[str]` | Sim | Lista vazia significa analisar todas as trilhas. A filtragem por tecnologia ignora maiúsculas/minúsculas. |

Exemplo válido para a trilha Python:

```json
{
  "competencies": ["Python syntax and semantics", "control flow"],
  "level": "beginner",
  "goal": "Consolidar fundamentos de Python",
  "technologies_of_interest": ["Python"]
}
```

**Retorno de sucesso:**

```text
{
  "analyses": [<análise serializada>, ...],
  "total": <quantidade de análises>
}
```

Cada análise contém `path`, `coverage_index`, `matched_competencies`,
`missing_competencies`, `extra_competencies` e `recommendations`. `path` usa a
estrutura serializada de trilha descrita em `get_learning_path`. Cada
recomendação contém `id`, `learner_id`, `recommendation_type`, `target_id`,
`rationale`, `competencies_to_develop` e `priority`.

Se nenhuma trilha corresponder às tecnologias informadas, o retorno é:

```json
{
  "analyses": [],
  "total": 0,
  "message": "No learning paths found for the specified technologies."
}
```

Um nível inválido retorna
`{"error": "Invalid level '<valor>'. Valid values: beginner, intermediate, advanced."}`.
Falhas de leitura ou validação dos catálogos não são convertidas em um
dicionário `error` pela implementação.

As competências são autodeclaradas e não são verificadas por evidências
práticas. O objeto de análise serializado não inclui um campo de disclaimer;
clientes devem preservar esse aviso na apresentação dos resultados.

## Formatação das respostas

Os formatters em [mcp_server/formatters.py](../mcp_server/formatters.py)
fazem transformações estruturais:

- níveis de domínio (`Level`) são convertidos para seus valores textuais;
- etapas de trilha são ordenadas por `order`;
- recomendações são serializadas com o tipo textual e os campos do modelo;
- a data do certificado é convertida para ISO-8601.

As ferramentas retornam objetos Python serializáveis. A formatação final do
conteúdo MCP e sua apresentação visual são responsabilidade do SDK e do
cliente, não de uma interface HTTP do Geo-Explorer.

## Erros e limitações gerais

- As respostas `{"error": ...}` descritas acima são dicionários retornados
  pelas funções das ferramentas, não documentação de um formato de erro do
  protocolo MCP.
- As exceções de I/O ou de dados inválidos dos catálogos não são tratadas
  uniformemente pelas ferramentas; onde não há `try/except`, elas propagam
  para o SDK.
- O catálogo é local e estático; as descrições de desafios não implementam as
  integrações ou bibliotecas que mencionam.
- O servidor registra quatro ferramentas. Não há recursos MCP, prompts
  registrados ou endpoint HTTP no código atual.
- A análise compara competências informadas com as descritas nas trilhas; não
  comprova proficiência. O parâmetro `goal` não altera a análise atual.
- Certificados são fictícios, sem validade oficial e sem exportação.
- O Geo-Explorer não executa modelos ou agentes de IA; fornece operações que
  um cliente MCP pode chamar.

## Testes MCP

Os testes ficam em
[tests/test_mcp_tools.py](../tests/test_mcp_tools.py) e cobrem:

- formatters;
- chamadas diretas às funções `*_impl`, sem iniciar transporte;
- registro e descoberta das quatro ferramentas;
- chamadas de ferramenta via `Client(create_server())` em processo.

Os testes de integração exercitam o protocolo pelo caminho de despacho direto
do SDK e **não abrem uma conexão stdio**. Para validar a inicialização real em
um cliente, configure o processo conforme a seção de transporte e faça uma
chamada pelo cliente MCP escolhido.

Para executar apenas os testes dessa camada, a partir da raiz do projeto:

```powershell
python -m pytest -q tests\test_mcp_tools.py
```
