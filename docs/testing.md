# Testes

Este documento descreve como executar e interpretar os testes automatizados
do Geo-Explorer e quais limites permanecem para validação manual. O objetivo
da suíte é verificar modelos e regras de domínio, carregamento dos catálogos,
comandos, páginas Streamlit e ferramentas MCP sem depender de serviços
externos.

Consulte também o [README](../README.md), o
[índice da documentação](index.md), a [arquitetura](architecture.md), a
[documentação MCP](mcp.md) e os [exemplos](examples.md).

## Ferramentas e dependências

- **pytest:** executor recomendado para toda a suíte. Descobre tanto funções
  de teste no estilo pytest quanto classes `unittest.TestCase`.
- **unittest:** biblioteca padrão usada por parte dos testes para organizar
  casos e aplicar mocks. Não é uma dependência adicional.
- **Streamlit AppTest:** usado nos testes GUI para executar a aplicação e
  interagir com navegação, formulários, seletores e estado da sessão sem
  abrir um navegador.
- **unittest.mock:** usado para simular dados vazios e falhas de carregamento
  nos testes de interface.

As dependências declaradas no
[requirements.txt](../requirements.txt) incluem `pytest>=8.0`,
`streamlit>=1.67,<2` e `mcp>=2,<3`. O AppTest faz parte das ferramentas de
teste do Streamlit; não é necessário instalar uma dependência separada para
ele.

## Preparar o ambiente no Windows PowerShell

Execute na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Os comandos abaixo também devem ser executados a partir da raiz do
repositório, com esse ambiente ativado.

## Comandos de execução

### Suíte completa

```powershell
python -m pytest -q
```

### Um arquivo específico

Por exemplo, para executar somente os testes da página de análise:

```powershell
python -m pytest -q tests\test_gui_analise.py
```

### Grupos por camada

**Modelos, carregamento de trilhas e análise de competências:**

```powershell
python -m pytest -q tests\test_data_loader.py tests\test_competency_analyzer.py
```

**Comandos CLI:**

```powershell
python -m pytest -q tests\test_trilha.py tests\test_desafio.py tests\test_certificado.py tests\test_analise.py
```

**Interface Streamlit:**

```powershell
python -m pytest -q tests\test_gui_home.py tests\test_gui_trilhas.py tests\test_gui_desafio.py tests\test_gui_certificado.py tests\test_gui_analise.py
```

**Ferramentas e formatters MCP:**

```powershell
python -m pytest -q tests\test_mcp_tools.py
```

Os comandos por camada são combinações dos arquivos de teste existentes.
Não há um comando `unittest discover` recomendado como substituto da suíte
completa: ele não executa funções de teste no estilo pytest.

## Organização dos testes

Há 12 arquivos `test_*.py` em `tests/`. Não existe um arquivo dedicado apenas
aos dataclasses de `core/models.py`; os modelos são exercitados pelos testes
de carregamento, análise, comandos e formatters.

### Modelos, carregamento e análise de competências

- [test_data_loader.py](../tests/test_data_loader.py) verifica o carregamento
  dos catálogos de trilhas, a conversão para `LearningPath` e `LearningStep`,
  níveis, campos obrigatórios selecionados e etapas. Também cobre caminho
  inexistente, JSON inválido, estrutura de nível superior incorreta e níveis
  desconhecidos.
  Inclui verificações de carregamento independente do diretório de trabalho.
- [test_competency_analyzer.py](../tests/test_competency_analyzer.py) testa
  normalização, cálculo de prioridade, geração de recomendações, escolha de
  alvo por proximidade de nível, comparação de competências, cobertura,
  preservação de nomes e ordenação. Inclui filtros por tecnologia e casos
  com os catálogos reais.

### Comandos CLI

- [test_trilha.py](../tests/test_trilha.py) verifica busca por tecnologia,
  correspondência sem diferença de caixa, entradas vazias e desconhecidas,
  conteúdo impresso, etapas ordenadas, competências e não mutação dos dados.
- [test_desafio.py](../tests/test_desafio.py) cobre leitura do catálogo de
  desafios, conversão para modelos, filtros por tecnologia e nível,
  correspondência sem diferença de caixa, ausência de resultados, entradas
  inválidas, conteúdo da saída e integridade dos dados e identificadores.
- [test_certificado.py](../tests/test_certificado.py) verifica dados gerados,
  identificadores únicos, data padrão e datas fornecidas, competências,
  validação de participante e atividade, disclaimer e formatação impressa.
- [test_analise.py](../tests/test_analise.py) verifica a formatação CLI da
  análise, o índice e aviso de autodeclaração, correspondências, lacunas,
  competências extras, recomendações, prioridades e filtragem por interesse.

### Interface Streamlit

Todos os cinco arquivos GUI usam `streamlit.testing.v1.AppTest`, com mocks
pontuais para estados que seriam difíceis de produzir com os catálogos reais:

- [test_gui_home.py](../tests/test_gui_home.py) verifica os quatro blocos da
  Home, seus botões de navegação e os cinco destinos da sidebar.
- [test_gui_trilhas.py](../tests/test_gui_trilhas.py) verifica o seletor e os
  dados da trilha, a ordem de exibição das etapas, a lista vazia e mensagens
  para falhas de carregamento.
- [test_gui_desafio.py](../tests/test_gui_desafio.py) verifica lista vazia,
  filtro e seleção de desafio, conteúdo exibido, estado da sessão, filtros
  sem resultado e erros de carregamento.
- [test_gui_certificado.py](../tests/test_gui_certificado.py) verifica
  submissão do formulário, dados e disclaimer, entradas obrigatórias,
  competências vazias, parsing de linhas e manutenção do certificado ao
  navegar entre páginas.
- [test_gui_analise.py](../tests/test_gui_analise.py) verifica submissão e
  estado do perfil, análise de todas as trilhas quando nenhum interesse é
  selecionado, navegação e retenção dos resultados, ordem das recomendações,
  lacunas e detalhes de recomendação, além de estados vazios e erros de
  carregamento.

O AppTest exercita a aplicação Streamlit em teste, mas não equivale a uma
verificação visual completa em navegador real.

### Ferramentas e formatters MCP

- [test_mcp_tools.py](../tests/test_mcp_tools.py) verifica os formatters de
  trilhas, desafios, certificados e análises; chamadas diretas às funções
  `*_impl`; validações e respostas para entradas não atendidas; e registro,
  descoberta e chamadas das quatro ferramentas via `Client(create_server())`.

As chamadas do cliente MCP são feitas em processo pelo caminho de despacho do
SDK. Elas não iniciam o transporte stdio.

## Cobertura observada

Considerando os casos presentes nos arquivos de teste, há verificações de:

- fluxos válidos de consulta, filtragem, geração de dados e análise;
- entradas vazias, tecnologias ou níveis desconhecidos e ausência de
  resultados;
- catálogos ausentes, JSON malformado e estruturas incompatíveis nos
  carregadores testados;
- comparação completa, parcial ou sem correspondências, índice de cobertura,
  recomendações, prioridades e ordenação;
- navegação, submissão de formulários, mensagens para estados vazios e
  retenção de dados selecionados em `st.session_state`;
- chaves e conversões dos formatters, descoberta de ferramentas e chamadas
  MCP em processo.

Os testes usam os JSON locais, objetos em memória e mocks. Os testes de
carregamento que precisam de arquivos inválidos criam arquivos temporários e
os removem ao final; eles não substituem os catálogos do projeto.

## Limites e verificações manuais

- **Visualização completa no navegador:** AppTest verifica elementos e
  interações, não layout visual completo, responsividade ou diferenças entre
  navegadores. Isso exige uma revisão manual no navegador. O histórico da
  Etapa 12.6 registra uma verificação visual pontual da navegação, não uma
  validação visual abrangente de todas as páginas.
- **MCP stdio e clientes externos:** a suíte não inicia o servidor por stdio
  nem testa interoperabilidade com clientes MCP externos. Essa validação
  requer iniciar o processo pelo cliente escolhido.
- **Fluxo interativo completo da CLI:** os testes cobrem funções de comando e
  texto apresentado, mas não simulam de ponta a ponta o loop de menu de
  `main.py`.
- **Cobertura de código:** não foi identificada configuração de cobertura,
  arquivo de configuração pytest/coverage ou dependência `pytest-cov` em
  `requirements.txt`. Portanto, este documento não informa percentual de
  cobertura.
- **Modelos:** não há módulo de testes dedicado a `core/models.py`; os modelos
  são verificados indiretamente pelos testes das camadas que os consomem.
- **Escopo de validação de dados:** os testes exercitam os erros enumerados
  nos arquivos de teste, mas não constituem prova de validação de todas as
  entradas JSON possíveis.

## Interpretar os resultados do pytest

O modo `-q` reduz a listagem de cada caso e mantém o resumo final. Em geral:

- `passed` indica testes concluídos com sucesso;
- `failed` indica asserções que não foram satisfeitas;
- `error` indica falhas durante preparação ou execução do caso;
- `skipped` indica testes que foram explicitamente ignorados.

Quando houver falhas, consulte o bloco correspondente no resumo para ver o
arquivo, o teste, a linha e a asserção que falhou. Um resultado totalmente
bem-sucedido termina sem falhas e com código de saída zero. O número de
testes aprovados pode mudar conforme os testes do repositório mudarem.

## Último resultado registrado

O histórico disponível registra a execução da suíte completa após a correção
de navegação da Etapa 12.6:

```text
python -m pytest -q
450 passed
```

Esse é o último resultado registrado, **não uma execução realizada durante a
criação deste documento**. Nenhum teste foi executado nesta atividade.
