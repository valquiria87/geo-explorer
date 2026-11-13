# Exemplos práticos

Este guia mostra formas de usar as interfaces CLI, Streamlit e MCP do
Geo-Explorer. Os exemplos usam os catálogos JSON locais fornecidos com o
projeto. Nomes de pessoas e perfis são fictícios. Os exemplos não alteram os
catálogos.

As sequências de entrada abaixo foram conferidas com o código e, nos exemplos
CLI, executadas com os valores indicados. As descrições dos resultados são
resumos ilustrativos, não transcrições completas. Campos como identificador e
data do certificado são gerados durante a execução e podem variar.

Para visão geral, consulte o [README](../README.md), o
[índice da documentação](index.md), a [arquitetura](architecture.md) e a
[documentação MCP](mcp.md).

## Preparar o ambiente

No Windows PowerShell, execute a partir da raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

As dependências declaradas incluem `mcp`, `streamlit` e `pytest`, com faixas
de versão indicadas em [requirements.txt](../requirements.txt).

### Iniciar as interfaces

**CLI**, em modo interativo:

```powershell
python main.py
```

**Streamlit:**

```powershell
python -m streamlit run gui\app.py
```

**Servidor MCP:**

```powershell
python -m mcp_server.server
```

O comando MCP inicia o servidor com transporte stdio e deve ser usado pelo
processo de um cliente MCP compatível. Ele não inicia um endpoint HTTP. Os
detalhes de inicialização e chamadas estão em [mcp.md](mcp.md).

## Consultar uma trilha pela CLI

O menu de [main.py](../main.py) oferece a opção 1 para consultar uma trilha.
Execute `python main.py` e informe as respostas quando o programa as solicitar:

```text
Opção do menu: 1
Tecnologia: Python
Opção do menu após o resultado: 5
```

Esse exemplo foi executado com o catálogo atual. A trilha encontrada é
**Python Foundations**, de nível `beginner`, com descrição, competências
gerais e cinco etapas ordenadas. A saída do comando inclui título, tecnologia,
nível, descrição, as etapas com suas competências desenvolvidas e a lista
geral de competências. O programa não imprime novamente o JSON bruto.

A busca de tecnologia não diferencia maiúsculas de minúsculas; o valor
`python` também corresponde à tecnologia `Python`.

## Consultar um desafio por tecnologia e nível

No menu da CLI, a opção 2 solicita tecnologia e nível e escolhe um desafio
compatível. Para selecionar um registro específico sem depender de uma
escolha aleatória entre vários resultados, este exemplo usa **AI Agents** no
nível `beginner`, combinação que corresponde a um desafio no catálogo atual:

```text
Opção do menu: 2
Tecnologia: AI Agents
Nível: beginner
Opção do menu após o resultado: 5
```

O desafio correspondente é **Question-Answering Agent with Tool Use**. A saída
do comando apresenta título, tecnologia, nível, estimativa de seis horas,
descrição, critérios de avaliação e competências avaliadas. O título e os
metadados citados vêm de [challenges.json](../data/challenges.json); a
descrição é uma proposta de exercício. Ela não significa que o Geo-Explorer
implemente ou execute o agente, uma ferramenta de busca ou uma calculadora.

Na CLI e na ferramenta MCP, a escolha é aleatória entre os desafios que
correspondem ao filtro. A interface Streamlit permite selecionar um desafio
específico entre os resultados disponíveis.

## Gerar um certificado fictício pela CLI

A opção 3 solicita participante, atividade, tecnologia, nível e competências
separadas por vírgula. Por exemplo:

```text
Opção do menu: 3
Participante: Ana Exemplo
Atividade: Python Foundations
Tecnologia: Python
Nível: beginner
Competências: Python syntax and semantics, control flow
Opção do menu após o resultado: 5
```

O comando exibe os dados do certificado e o aviso
**CERTIFICADO FICTÍCIO — SEM VALIDADE OFICIAL**. O identificador é criado a
cada geração, e a data de emissão corresponde à data corrente; portanto,
esses valores não devem ser copiados como resultados fixos. O certificado é
um registro de apresentação, não uma certificação profissional, e não há
exportação de arquivo.

## Analisar competências pela CLI

A opção 4 recebe nome, competências separadas por vírgulas, nível, objetivo
profissional e tecnologias de interesse. Use este perfil fictício:

```text
Opção do menu: 4
Nome: Ana Exemplo
Competências: Python syntax and semantics, control flow, file I/O, Git
Nível atual: beginner
Objetivo: Consolidar fundamentos de Python
Tecnologias de interesse: Python
Opção do menu após o resultado: 5
```

Com o catálogo atual, o resultado da execução apresenta a trilha **Python
Foundations** e índice de cobertura declarada de **21,4% (3 de 14
competências)**. As competências correspondentes são `Python syntax and
semantics`, `control flow` e `file I/O`; `Git` aparece como competência
declarada fora do escopo dessa trilha. As demais competências da trilha são
listadas como não declaradas, com recomendações priorizadas. Neste exemplo,
`virtual environments` aparece primeiro, com prioridade 4.

O objetivo profissional é apresentado no perfil, mas o analisador atual não o
usa para calcular correspondências ou prioridades. A análise compara apenas
as competências informadas com as trilhas selecionadas. O próprio resultado
avisa que as competências são autodeclaradas e não verificadas por evidências
práticas; o índice não comprova proficiência.

## Usar a interface Streamlit

Inicie a aplicação com `python -m streamlit run gui\app.py`. A navegação
lateral personalizada oferece **Início**, **Trilhas de Aprendizagem**,
**Desafio Prático**, **Certificado** e **Análise de Competências**. A Home
também tem botões para abrir Trilhas, Desafio, Análise e Certificado.

### Trilhas

Em **Trilhas de Aprendizagem**, selecione uma opção no campo
**Tecnologia / Trilha**, por exemplo **Python — Python Foundations**. A página
apresenta tecnologia, nível, descrição, competências da trilha e etapas em
ordem. As competências gerais e as de cada etapa podem ser abertas nos
expansores da página.

### Desafio Prático

Em **Desafio Prático**, selecione **AI Agents**, o nível **Iniciante** e
**Question-Answering Agent with Tool Use**. Depois de clicar em **Exibir
desafio**, a página apresenta descrição, tempo estimado, competências
avaliadas e critérios de avaliação. A combinação usada precisa ter pelo menos
um resultado no catálogo; se não houver, a página informa que não há desafios
disponíveis para aquela tecnologia e nível.

### Certificado

Em **Certificado**, preencha participante, atividade, tecnologia e nível. No
campo **Competências desenvolvidas**, informe uma competência por linha; o
campo pode ficar vazio. Por exemplo, use `Ana Exemplo`, `Python Foundations`,
`Python`, **Iniciante** e as competências `Python syntax and semantics` e
`control flow`.

Clique em **Gerar certificado** para exibir os dados e o aviso de que ele é
fictício e não tem validade oficial. A tecnologia não pode ficar vazia; nome
do participante e atividade também precisam ser informados. O resultado fica
na sessão e não é exportado.

### Análise de Competências

Em **Análise de Competências**, informe opcionalmente o nome, o objetivo
profissional, o nível atual, tecnologias de interesse e competências — uma
por linha. Se não selecionar tecnologias, a análise considera todas as
trilhas. Clique em **Analisar perfil**.

O resultado mostra o perfil informado e, para cada trilha selecionada, o
índice de cobertura declarada, as competências correspondentes, as lacunas e
as recomendações priorizadas. O aviso sobre competências autodeclaradas e
não verificadas por evidências práticas aparece na página e junto da análise.

O perfil e os resultados são mantidos em `st.session_state` durante a sessão
do Streamlit, permitindo navegar entre páginas sem banco de dados. Não há
persistência entre sessões ou armazenamento de perfil em banco.

## Fazer chamadas MCP

As chamadas a seguir usam os nomes e os argumentos documentados em
[mcp.md](mcp.md). Elas mostram somente o nome da ferramenta e seu objeto de
argumentos; não representam envelopes de resposta do protocolo. A seleção de
desafio pode variar, e o identificador e a data de um certificado são
dinâmicos.

### Consultar uma trilha

```text
Ferramenta: get_learning_path
Argumentos:
{"technology": "Python"}
```

O resultado estruturado contém dados da trilha, incluindo título, nível,
descrição, etapas ordenadas e competências.

### Obter um desafio

```text
Ferramenta: get_challenge
Argumentos:
{"technology": "Python", "level": "beginner"}
```

A ferramenta filtra os desafios de Python no nível `beginner` e escolhe um
resultado. O objeto retornado inclui descrição, critérios de avaliação,
competências avaliadas e estimativa de horas, quando informada no catálogo.

### Gerar dados de um certificado fictício

```text
Ferramenta: generate_certificate
Argumentos:
{
  "participant": "Ana Exemplo",
  "activity": "Python Foundations",
  "technology": "Python",
  "level": "beginner",
  "competencies": ["Python syntax and semantics", "control flow"]
}
```

O resultado contém os dados do certificado, inclusive identificador, data de
emissão e disclaimer fictício. A ferramenta não exporta arquivo.

### Analisar competências

```text
Ferramenta: analyze_competencies
Argumentos:
{
  "competencies": ["Python syntax and semantics", "control flow"],
  "level": "beginner",
  "goal": "Consolidar fundamentos de Python",
  "technologies_of_interest": ["Python"]
}
```

O resultado traz uma análise para cada trilha correspondente, com cobertura,
competências correspondentes, lacunas e recomendações. As competências
fornecidas continuam sendo autodeclaradas; a ferramenta não verifica
proficiência prática.

## Limitações e observações

- Os exemplos usam catálogos JSON locais e estáticos; não dependem de serviços
  externos.
- Os resultados podem mudar quando os catálogos forem alterados. Desafios são
  selecionados aleatoriamente pela CLI e pelo MCP quando há mais de uma
  correspondência.
- A aplicação apresenta descrições e critérios de desafios, mas não executa
  nem avalia automaticamente as soluções.
- Competências são autodeclaradas e não verificadas por evidências práticas.
- Certificados são fictícios, sem validade oficial e sem exportação.
- Dados do perfil da interface gráfica são mantidos na sessão Streamlit, sem
  persistência em banco de dados.
- O servidor MCP usa stdio e não oferece endpoint HTTP. O Geo-Explorer não
  executa modelos ou agentes de IA; menções a eles nos desafios são parte das
  propostas de exercício, não integrações implementadas pelo projeto.
