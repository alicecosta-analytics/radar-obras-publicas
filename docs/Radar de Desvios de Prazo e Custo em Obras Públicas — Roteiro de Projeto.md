# Radar de Desvios de Prazo e Custo em Obras Públicas — Roteiro de Projeto

Oct 21, 2026 · @Alice Costa

## Resumo

O projeto mede quanto os contratos de empreitadas de obras públicas em Portugal desviam do preço e do prazo contratados, e quais características do contrato explicam esses desvios. A fase 1 usa os dados abertos do Portal Base (IMPIC); a fase 2 acrescenta as obras federais brasileiras do ObrasGov como comparação.

O método adapta os índices da Gestão do Valor Agregado (EVM) a dados de contrato encerrado: um índice de desempenho de custo (preço contratado ÷ preço efetivo) e um de prazo (prazo previsto ÷ prazo realizado). A análise combina estatística descritiva, testes de comparação entre grupos e regressão para identificar preditores do desvio.

Entregas: pipeline em Python, banco SQL documentado, painel público, repositório com README e um artigo curto de divulgação.

**Palavras-chave:** gestão do valor agregado; desvio de custo; desvio de prazo; contratação pública; dados abertos; Portugal.

## 1. Introdução

### 1.1 Contexto

Desvios de custo e prazo são a regra, não a exceção, em obras públicas. No estudo de referência da área, Flyvbjerg, Holm e Buhl (2002) analisaram 258 projetos de infraestrutura de transporte e encontraram custo real 28% acima do previsto, em média, com nove em cada dez projetos estourando o orçamento ([World Bank PPP](https://ppp.worldbank.org/index.php/library/underestimating-costs-public-works-projects-error-or-lie); [arXiv](https://arxiv.org/abs/1303.6604)).

Em Portugal, o Tribunal de Contas acompanha o tema por meio das fiscalizações aos contratos adicionais de empreitadas. No triénio 2020–2022, a parcela de contratos de empreitada sem alterações caiu para 55,15%, e o Tribunal voltou a pedir mais rigor na elaboração dos projetos ([Cuatrecasas, 2023](https://www.cuatrecasas.com/pt/global/art/contratos-adicionais-relatorio-tribunal-de-contas-1)). Entre 2017 e 2020, os trabalhos a mais encareceram 2.709 contratos analisados em 106 milhões de euros ([DN](https://www.dn.pt/dinheiro/trabalhos-extra-nas-obras-publicas-custaram-mais-106-milhoes-ao-erario-publico-13054807.html)).

No Brasil, o TCU identificou mais de 14 mil obras paralisadas com recursos da União no Acórdão 1.079/2019-Plenário, somando R$ 144 bilhões de investimento previsto ([TCU](https://portal.tcu.gov.br/imprensa/noticias/tcu-cnj-e-atricon-assinam-termo-de-cooperacao-tecnica-sobre-obras-paralisadas)).

### 1.2 Problema de pesquisa

Os relatórios oficiais descrevem o volume agregado dos desvios, mas não respondem, contrato a contrato, *quais características* tornam um contrato mais propenso a estourar. Além disso, os dados abertos que permitem essa análise (Portal Base) são pouco explorados com ferramentas de gestão de projetos como a EVM.

**Pergunta central:** qual é a magnitude dos desvios de custo e prazo nas empreitadas de obras públicas em Portugal, e quais características do contrato estão associadas a esses desvios?

### 1.3 Justificativa

- **Acadêmica:** aplica índices de EVM, normalmente usados no controle de um projeto em andamento, a uma população de contratos encerrados — um uso de portfólio, não de projeto.
- **Prática:** gera evidência sobre onde concentrar o controle (tipo de procedimento, porte, entidade), útil a donos de obra e órgãos de fiscalização.
- **Profissional:** demonstra, num único projeto público e verificável, competências de PMO (EVM, governança, lições aprendidas) e de dados (pipeline, SQL, estatística, visualização), voltado ao mercado português.

## 2. Objetivos

### 2.1 Objetivo geral

Medir e explicar os desvios de custo e prazo nas empreitadas de obras públicas em Portugal, com índices inspirados na Gestão do Valor Agregado, e comparar com as obras federais brasileiras numa segunda fase.

### 2.2 Objetivos específicos

1. Avaliar a completude dos dados abertos do Portal Base para análise de execução contratual.
2. Construir um pipeline reprodutível de coleta, limpeza e carga em banco SQL.
3. Definir e calcular os índices de desempenho de custo (CPIc) e de prazo (SPIc) por contrato.
4. Descrever a distribuição dos desvios por tipo de procedimento, porte, região e entidade adjudicante.
5. Estimar, por regressão, quais variáveis do contrato predizem o estouro.
6. Publicar os resultados num painel interativo e num repositório documentado.
7. (Fase 2) Replicar os índices com dados do ObrasGov e comparar os dois países.

### 2.3 Perguntas de pesquisa e hipóteses

| # | Pergunta | Hipótese de trabalho |
| --- | --- | --- |
| P1 | Que parcela dos contratos tem dados de execução preenchidos? | H1: a completude é baixa e não aleatória (varia por entidade e porte), o que exige tratar viés de seleção. |
| P2 | Qual é a distribuição dos desvios de custo e prazo? | H2: as distribuições são assimétricas à direita; a mediana do desvio é positiva e há cauda longa. |
| P3 | O desvio difere por tipo de procedimento? | H3: ajustes diretos e consultas prévias têm desvios diferentes dos concursos públicos. |
| P4 | O porte do contrato prediz o desvio? | H4: contratos maiores e mais longos têm maior probabilidade de estouro de prazo. |
| P5 | Custo e prazo estouram juntos? | H5: os desvios de custo e de prazo são positivamente correlacionados. |
| P6 | (Fase 2) Os padrões se repetem no Brasil? | H6: a direção dos efeitos se mantém; a magnitude difere. |

As hipóteses são pontos de partida para o teste estatístico, não conclusões antecipadas.

## 3. Referencial teórico

O referencial sustenta três escolhas do projeto: usar índices de EVM como métrica, tratar o desvio como fenômeno sistemático (não acidental) e ler os dados à luz das regras de contratação de cada país.

### 3.1 Gestão do Valor Agregado (EVM)

A EVM integra escopo, prazo e custo para medir objetivamente o desempenho de um projeto e projetar seu resultado ([PMI, 2019](https://www.pmi.org/shop/p-/book/the-standard-for-earned-value-management/00101618501)). Seus três valores básicos são o valor planejado (PV), o valor agregado (EV) e o custo real (AC), dos quais derivam os índices:

```latex
CPI = \frac{EV}{AC} \qquad SPI = \frac{EV}{PV}
```

CPI e SPI abaixo de 1 indicam, respectivamente, custo acima do previsto e atraso. Base de leitura: Practice Standard for EVM, 2.ª ed. ([PMI, 2011](https://vufind.katalog.k.utb.cz/Record/80158/TOC)), e The Standard for EVM ([PMI, 2019](https://www.pmi.org/standards/earned-value-management)).

### 3.2 Earned Schedule e o problema do SPI

O SPI clássico mede prazo em unidades monetárias. Por isso, um projeto concluído com atraso termina com SPI = 1 ([Lipke, 2003, via PMWL](https://pmworldlibrary.net/?p=154839)). Lipke propôs o Earned Schedule (ES), que mede o desempenho de prazo em unidades de tempo; o padrão do PMI de 2019 passou a incorporar o conceito ([PMI, 2019](https://www.pmi.org/shop/p-/book/the-standard-for-earned-value-management/00101618501)).

**Implicação para o projeto:** como os dados são de contratos encerrados, o índice de prazo será calculado em tempo (prazo previsto ÷ prazo realizado), na lógica do Earned Schedule, e não com o SPI monetário.

### 3.3 Desvios em obras públicas: magnitude e explicações

- **Magnitude.** Flyvbjerg, Holm e Buhl (2002) mostraram, em 258 projetos de transporte, que o custo real superou o previsto em 28% em média, e que o padrão se manteve ao longo de 70 anos ([arXiv](https://arxiv.org/pdf/1303.7405)).
- **Categorias de explicação.** Cantarelli et al. (2010) agrupam as explicações da literatura em técnicas, econômicas, psicológicas e políticas, com as políticas como dominantes ([EJTIR](https://journals.open.tudelft.nl/ejtir/article/view/2864)).
- **Visão crítica.** Ahiaga-Dagbui e Smith (2014) distinguem subestimação inicial de crescimento de custo durante a execução, dois fenômenos frequentemente confundidos ([Emerald](https://emerald.com/insight/content/doi/10.1108/JFMPC-06-2013-0027/full/html)). Love e Ahiaga-Dagbui (2018) contestam a dicotomia "erro ou mentira" de Flyvbjerg ([IDEAS/RePEc](https://ideas.repec.org/a/eee/transa/v113y2018icp357-368.html)).
- **Portugal.** Uma dissertação da Universidade Lusófona analisou 41 empreendimentos a partir de auditorias do Tribunal de Contas (2008–2011) e resumiu as causas mais frequentes dos desvios ([ReCiL, 2012](https://recil.ulusofona.pt/items/9317ccde-8159-4582-9b3c-5188dd5e5de9)).

**Implicação para o projeto:** este trabalho mede *crescimento* de custo e prazo após a assinatura (contratado vs. efetivo), não a subestimação na fase de decisão. A distinção deve constar explicitamente nas conclusões.

### 3.4 Marco legal e transparência

| País | Norma de contratação | Fonte de dados | O que importa para o projeto |
| --- | --- | --- | --- |
| Portugal | [Código dos Contratos Públicos, DL 18/2008](https://faolex.fao.org/docs/pdf/por238404.pdf), com alterações até o DL 66/2025 | [Portal Base / IMPIC](https://dados.gov.pt/en/datasets/contratos-publicos-portal-base-impic-contratos-de-2012-a-2026/) | Trabalhos complementares podem chegar a 50% do valor do contrato ([Cuatrecasas](https://www.cuatrecasas.com/pt/global/art/contratos-adicionais-relatorio-tribunal-de-contas-1)); o Portal publica formação e execução dos contratos ([Portaria 701-F/2008](https://www.madeira.gov.pt//Portals/23/Documentos/ContratacaoPublica/Portaria%20701-F_2008.pdf)). |
| Brasil | Lei 14.133/2021 (a conferir na fase 2) | [ObrasGov – API pública](https://www.gov.br/obrasgov/pt-br/ferramentas-de-gestao-e-transparencia/api-de-dados-abertos-obrasgov-br_novo) | Cobre obras com recursos federais; o TCU já apontou lacunas no cadastro único de obras ([TCU](https://portal.tcu.gov.br/data/files/6B/E7/E8/14/6E0BC8103A4A64C8F18818A8/Monitoramento%20de%20Obras%20Paralisadas.pdf)). |

### 3.5 Lacuna

Os estudos portugueses encontrados trabalham com amostras de auditoria (dezenas de obras) ou com totais agregados do Tribunal de Contas. Não foi encontrado, nesta revisão inicial, um estudo que aplique índices de EVM contrato a contrato sobre a base completa do Portal Base. A revisão deve ser aprofundada no Google Scholar e no RCAAP antes de afirmar a lacuna como definitiva.

## 4. Método

Pesquisa quantitativa, descritiva e explicativa, com dados secundários abertos e corte transversal. A unidade de análise é o **contrato de empreitada de obras públicas** registado no Portal Base.

### 4.1 Fontes de dados

| Fonte | Conteúdo | Formato e atualização | Uso |
| --- | --- | --- | --- |
| [IMPIC – Contratos 2012–2026](https://dados.gov.pt/en/datasets/contratos-publicos-portal-base-impic-contratos-de-2012-a-2026/) | Um registo por contrato | Aberto, quinzenal | Base principal |
| [IMPIC – Modificações contratuais 2012–2026](https://dados.gov.pt/es/datasets/contratos-publicos-portal-base-impic-modificacoes-contratuais-de-2012-a-2026/) | Alterações de preço e prazo | Aberto, semestral | Prorrogações de prazo, causas dos desvios, limite inferior de custo e checagem do preço efetivo |
| [Relatórios anuais da contratação pública (Base)](https://www.base.gov.pt/Base4/media/1elfqicv/relat%C3%B3rio-anual-da-contrata%C3%A7%C3%A3o-p%C3%BAblica-2023.pdf) | Totais oficiais por ano | PDF | Validação dos totais |
| INE – índices de preços (a definir) | Inflação / custos de construção | CSV | Deflação de valores |
| [ObrasGov – API pública](https://www.gov.br/obrasgov/pt-br/ferramentas-de-gestao-e-transparencia/api-de-dados-abertos-obrasgov-br_novo) | Obras federais, execução física | API REST | Fase 2 |

### 4.2 Recorte da população

1. Tipo de contrato exatamente igual a "Empreitadas de obras públicas". Ficam de fora os contratos mistos (empreitada com bens ou serviços, cerca de 1%) e as concessões de obras públicas, que têm outro regime.
2. Período: **2019 a 2022** para os índices de execução (reporte do fecho estável, perto de 40–47%). 2018 entra só como teste de robustez, por ser ano de transição. De 2023 em diante, os contratos ficam fora dos índices até que a maioria tenha tido tempo de fechar. De 2012 a 2017, o fecho quase não era reportado (5% em 2017); esses anos servem apenas para análises da linha de base (procedimento, concorrência, preço base vs. contratual).
3. Para os índices de execução: contrato com data de fecho preenchida, preço efetivo maior que zero, fim por cumprimento e prazo contratual maior que zero. Resoluções, revogações e anulações são analisadas à parte, como sinal de falha do projeto.

### 4.3 Indicadores (adaptação da EVM a contratos encerrados)

Como cada contrato é observado uma vez, já encerrado, os índices comparam o compromisso inicial (equivalente à linha de base) com o resultado final:

```latex
CPI_c = \frac{\text{pre\c{c}o contratual}}{\text{pre\c{c}o total efetivo}} \qquad SPI_c = \frac{\text{prazo contratual (dias)}}{\text{data de fecho} - \text{data de celebra\c{c}\~ao}}
```

Valores abaixo de 1 indicam estouro de custo ou atraso. Para leitura em percentagem, usa-se também o desvio relativo:

```latex
\Delta_{custo} = \frac{\text{efetivo} - \text{contratual}}{\text{contratual}} \qquad \Delta_{prazo} = \frac{\text{realizado} - \text{previsto}}{\text{previsto}}
```

**Revisão após a Fase 0: desenho em intervalo.** Nenhuma medida isolada de prazo é perfeita, então o projeto usa duas, uma de cada lado do valor real:

| Dimensão | Limite inferior | Medida direta | Limite superior |
| --- | --- | --- | --- |
| Prazo | Prorrogação formal: `modifPrazoExecucao` da última modificação ÷ prazo contratual | — | SPIc: tempo até o fecho no Portal, que inclui um intervalo administrativo |
| Custo | Preço final da última modificação (`modifContratoPrecoAlterado`) | CPIc com `PrecoTotalEfetivo`, nos contratos fechados | — |

O atraso real de cada grupo de contratos é reportado como um intervalo entre a prorrogação formal e o tempo até o fecho. Para custo, o CPIc dos contratos fechados é a medida principal; o preço final da última modificação serve de limite inferior nos contratos ainda sem fecho, o que amplia a cobertura.

Na base de modificações, cada linha é um fundamento, e não um ato: os registos são deduplicados por contrato, data, preço e prazo, e o estado final de cada contrato é o do último ato. O preço e o prazo alterados são os **novos totais**, e não acréscimos (mediana da razão sobre o contratual: 1,05 para preço e 1,16 para prazo, em 2021).

Limitações assumidas: a data de celebração aproxima o início real da obra (o auto de consignação pode ser posterior), e a data de fecho pode ser bem posterior ao fim da obra. As duas inflam o atraso medido. Uma auditoria manual de cerca de 20 contratos no Portal Base vai verificar a que evento corresponde a data de fecho. Os campos foram confirmados no arquivo de 2021: `precoContratual`, `PrecoTotalEfetivo`, `prazoExecucao` (em dias), `dataCelebracaoContrato`, `dataFechoContrato` e `tipoFimContrato`.

### 4.4 Etapas da análise

1. **Diagnóstico de completude (P1).** Percentagem de contratos com campos de execução válidos, por ano, entidade, porte e procedimento. Uma regressão logística de "tem dados de execução" sobre as características do contrato mede o viés de seleção.
2. **Limpeza.** Remoção de duplicados; tratamento de valores impossíveis (preço efetivo zero, datas invertidas); winsorização ou exclusão documentada de extremos; deflação para preços de um ano-base.
3. **Estatística descritiva (P2).** Mediana, quartis, % de contratos com estouro, histogramas e boxplots de CPIc e SPIc.
4. **Comparação entre grupos (P3).** Kruskal-Wallis e Mann-Whitney, por serem robustos às distribuições assimétricas esperadas; tamanho de efeito reportado.
5. **Associação custo × prazo (P5).** Correlação de Spearman entre os dois desvios.
6. **Modelos explicativos (P4).** (a) Regressão logística para a probabilidade de estouro (CPIc < 1; SPIc < 1); (b) regressão linear sobre o log do índice, com erros-padrão agrupados por entidade adjudicante. Diagnóstico de multicolinearidade (VIF) e de resíduos.
7. **Robustez.** Repetir os modelos com o indicador alternativo de modificações e com a amostra sem extremos.

### 4.5 Variáveis explicativas candidatas

| Variável | Tipo | Hipótese ligada |
| --- | --- | --- |
| Preço contratual (log, deflacionado) | Contínua | H4 |
| Prazo contratual (dias) | Contínua | H4 |
| Tipo de procedimento (concurso público, ajuste direto, consulta prévia, outros) | Categórica | H3 |
| Tipo de entidade (autarquia, administração central, empresa pública) | Categórica | — |
| Região (NUTS II) do local de execução | Categórica | — |
| Código CPV (tipo de obra, 2 a 3 dígitos) | Categórica | — |
| Ano de celebração | Categórica / tendência | — |
| Financiamento europeu, n.º de concorrentes (se disponíveis) | Binária / contínua | — |

### 4.6 Banco de dados

Modelo dimensional em SQL (PostgreSQL ou SQLite): uma tabela fato de contratos (valores, prazos, índices calculados), uma tabela fato de modificações, e dimensões de entidade, procedimento, região, CPV e tempo. As consultas analíticas ficam versionadas no repositório, cada uma ligada a uma pergunta de pesquisa.

### 4.7 Ferramentas

Python (pandas, statsmodels, scipy), SQL, Jupyter para a análise, Streamlit para o painel, Git/GitHub para versão e publicação.

### 4.8 Validade e limitações

- **Viés de seleção:** só cerca de metade das empreitadas tem o encerramento reportado (47% em 2021). Se os contratos bem geridos reportam mais, os desvios ficam subestimados. A etapa 1 mede esse risco e ele é declarado nas conclusões.
- **Data de fecho administrativa:** a data de fecho parece incluir um intervalo burocrático depois do fim da obra, o que infla o atraso, sobretudo nas obras curtas (ver 4.3 e o Diário da Fase 0).
- **Preço efetivo possivelmente copiado:** em metade dos contratos encerrados, o preço efetivo é exatamente igual ao contratual. Pode ser obra sem desvio ou repetição automática do valor. O cruzamento com a base de modificações vai testar a consistência.
- **Qualidade do registo:** os dados são declarados pelas próprias entidades, sem auditoria campo a campo. Erros detectados em 2021: datas de fecho anteriores à celebração, preços efetivos em escala errada (CPIc acima de 1.700) e prazos incompatíveis com as datas.
- **Causalidade:** a regressão mostra associação, não causa.
- **Escopo:** o projeto mede o crescimento de custo após a assinatura, não a subestimação na fase de decisão (ver 3.3).
- **Comparação PT × BR (fase 2):** universos diferentes (todas as entidades vs. obras federais) e moedas diferentes; a comparação será feita sobre índices adimensionais e com ressalvas explícitas.

## 5. Plano de execução

Com 2 horas por semana, o núcleo do projeto (fases 0 a 4) leva cerca de 70 horas, ou seja, uns 8 a 9 meses, com publicação prevista para o início de julho de 2027. O cronograma inclui duas semanas de folga no fim do ano. Cada fase fecha com um critério de passagem (gate).

| Fase | Horas estimadas | Início | Fim |
| --- | --- | --- | --- |
| 0 — Diagnóstico dos dados | 8 h (4 semanas) | 26/10/2026 | 22/11/2026 |
| 1 — Pipeline e limpeza | 16 h (8 semanas + 2 de folga) | 23/11/2026 | 31/01/2027 |
| 2 — Banco e consultas SQL | 12 h (6 semanas) | 01/02/2027 | 14/03/2027 |
| 3 — Estatística e modelos | 20 h (10 semanas) | 15/03/2027 | 23/05/2027 |
| 4 — Painel e divulgação | 12 h (6 semanas) | 24/05/2027 | 04/07/2027 |
| 5 — Extensão Brasil (opcional) | 16 h (8 semanas) | 05/07/2027 | 29/08/2027 |

As horas são estimativas iniciais. Se a Fase 0 consumir mais que o previsto, as datas seguintes devem ser revistas no seu gate. A Fase 2 depende de concluir o curso de SQL até fevereiro de 2027; se o curso atrasar, as fases 2 e 3 podem trocar de ordem, porque a análise estatística roda sobre a base tratada em Python.

1. **Fase 0 — Diagnóstico dos dados (agora).**
   - Baixar contratos e modificações do IMPIC; filtrar empreitadas; ler o dicionário de dados.
   - Entrega: relatório de completude dos campos (notebook).
   - *Gate:* existem contratos suficientes com preço efetivo e data de fecho? Se não, o indicador principal passa a ser o de modificações.
2. **Fase 1 — Pipeline e limpeza (Python).**
   - Scripts de download, padronização de tipos, deflação e regras de limpeza documentadas.
   - Entrega: base tratada e log de exclusões.
   - *Gate:* totais anuais batem com os relatórios oficiais do Base dentro de uma margem definida.
3. **Fase 2 — Banco e consultas (após o curso de SQL).**
   - Modelo dimensional, carga, consultas analíticas ligadas a P1–P5.
   - Entrega: esquema, scripts SQL e consultas comentadas no repositório.
4. **Fase 3 — Estatística e modelos (com a pós da UFMG).**
   - Etapas 3 a 7 da seção 4.4.
   - Entrega: notebook de análise com tabelas de resultados e diagnóstico dos modelos.
   - *Gate:* resultados robustos às duas versões do indicador.
5. **Fase 4 — Painel e divulgação.**
   - Painel em Streamlit, README final, artigo curto e post no LinkedIn.
6. **Fase 5 — Extensão Brasil (opcional).**
   - Coleta via API do ObrasGov, cálculo do SPIc com datas previstas e situação da obra, comparação com ressalvas.

### 5.1 Estrutura sugerida do repositório

```
radar-obras-publicas/
├── README.md            # pergunta, método, resultados, limitações
├── data/
│   ├── raw/             # arquivos originais (não versionados)
│   └── processed/
├── src/
│   ├── extract.py       # download
│   ├── transform.py     # limpeza e índices
│   └── load.py          # carga no banco
├── sql/
│   ├── schema.sql
│   └── queries/         # uma consulta por pergunta
├── notebooks/
│   ├── 01_completude.ipynb
│   ├── 02_descritiva.ipynb
│   └── 03_modelos.ipynb
├── app/                 # painel Streamlit
└── docs/
    └── dicionario_dados.md
```

## 6. Resultados esperados e divulgação

O resultado central é um retrato quantitativo, contrato a contrato, de quanto e onde as empreitadas públicas portuguesas desviam de custo e prazo, com a qualidade dos dados medida e declarada.

| Entrega | Público | Formato |
| --- | --- | --- |
| Relatório de completude do Portal Base | Recrutadores de dados, academia | Notebook + seção no README |
| Distribuição de CPIc e SPIc por grupo | Gestores, PMO | Painel interativo |
| Modelo de preditores de estouro | Academia, órgãos de controle | Notebook com tabelas de regressão |
| Lições aprendidas para donos de obra | PMO, setor público | Seção do README e post |
| Repositório completo e reprodutível | Recrutadores | GitHub |
| Post no LinkedIn com 3 achados e o link do painel | Rede profissional em Portugal | Texto curto + 1 gráfico |

**Fase 2 (Brasil):** um segundo post, comparando os índices adimensionais dos dois países com as ressalvas da seção 4.8.

**Questões em aberto antes de começar**

- [x] Ritmo semanal: 2 h/semana (cronograma na seção 5).
- [ ] Painel: Streamlit ou Looker Studio. Decidir no gate da Fase 3. Streamlit reaproveita o código Python e conta mais para o portfólio de dados; Looker Studio fica pronto mais rápido se o tempo estiver apertado.
- [x] Revisão do método: sem orientador. Substituir por (a) uma revisão crítica do notebook da Fase 3 feita comigo, (b) a publicação do método no README antes dos resultados, para receber comentários, e (c) a checagem dos modelos contra o diagnóstico da seção 4.4.

## 7. Diário da Fase 0

Registo dos achados e das decisões de método, na ordem em que aconteceram. Serve de base para o log de exclusões da Fase 1 e para a seção de limitações do README.

### 22/10/2026 — Diagnóstico do arquivo de 2021

**Ambiente:** VS Code, notebook `analise.ipynb`, ambiente virtual `.venv` com pandas e openpyxl, `requirements.txt` gerado. Os 15 arquivos anuais (2012–2026) foram baixados em xlsx, de 16 a 65 MB cada.

**Volume:** 187.416 contratos de todos os tipos em 2021, com 39 colunas. Empreitadas puras: 13.850.

**Completude dos campos-chave nas empreitadas de 2021:**

| Campo | Preenchido | Leitura |
| --- | --- | --- |
| `precoContratual`, `prazoExecucao`, `dataCelebracaoContrato` | 100% | Linha de base completa |
| `PrecoTotalEfetivo` | 100% | Falso: é zero em todos os contratos sem fecho |
| `dataFechoContrato`, `tipoFimContrato` | 47% | Encerramento reportado |
| `concorrentes` | 79% | Variável útil para o modelo |
| `precoBaseProcedimento` | 100% | Permite um indicador extra: preço base vs. contratual |
| `NUTs` | 1% | Inutilizável; a região sai de `LocalExecucao` |

**Primeiros índices (6.340 contratos válidos):**

- **Custo:** mediana do CPIc = 1,00; 38% dos contratos com estouro; percentil 10 = 0,87. Resultado plausível.
- **Prazo:** mediana do SPIc = 0,33 e 91% "atrasados". Alto demais para ser só atraso de obra.
- **Atraso em dias até o fecho, por faixa de prazo contratual (medianas):** até 30 d → 71; 31–90 d → 138; 91–180 d → 305; 181–365 d → 412; mais de 1 ano → 377. O atraso nem é fixo (o que indicaria só burocracia) nem proporcional ao prazo (o que indicaria só atraso de obra): é uma mistura dos dois.
- **Erros de registo:** 27 contratos com fecho no mesmo dia ou antes da celebração; 79 com CPIc abaixo de 0,5 ou acima de 2; mínimo de −2.935 dias de atraso. Cerca de 1,7% dos válidos.

**Decisões de método**

1. D1 — Usar só as empreitadas puras (ver 4.2).
2. D2 — Preço efetivo válido apenas com data de fecho e valor maior que zero.
3. D3 — Excluir dos índices os contratos não terminados por cumprimento; analisar as rescisões à parte.
4. D4 — Excluir datas impossíveis e CPIc fora do intervalo 0,5–2, registando cada exclusão (a regra de extremos pode ser refinada na Fase 1).
5. D5 — SPIc reinterpretado como limite superior do atraso; prorrogações da base de modificações como medida principal de prazo (ver 4.3).

**Próximos passos**

- [x] Repetir o diagnóstico em outros anos (feito para 2017–2023, ver abaixo).
- [x] Baixar a base de modificações contratuais e ver a estrutura (ver abaixo).
- [ ] Auditoria manual: abrir cerca de 20 contratos no Portal Base e identificar a que evento corresponde a data de fecho.
- [x] Cruzar contratos com efetivo igual ao contratual com a base de modificações (ver abaixo).
- [ ] Verificar na legislação se a Portaria 57/2018 ou a revisão do CCP de 2018 (DL 111-B/2017) explica o início do reporte do fecho. Pista: nota de versão do Portal Base de 2020, que cita as Portarias 57/2018 e 284/2019 e a designação das causas de extinção.

### 22/10/2026 — Série 2017–2023

O diagnóstico foi transformado numa função (`diagnostico(ano)`) e aplicado a sete anos. As regras de limpeza D1 a D4 já estão aplicadas.

| Ano | Empreitadas | Com fecho | Válidos | Efetivo = contratual | CPIc p10 | Estouro de custo | Atraso mediano (dias) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2017 | 16.183 | 5,2% | 712 | 25,6% | 0,92 | 36,7% | 506 |
| 2018 | 10.343 | 28,3% | 2.814 | 57,9% | 0,96 | 22,1% | 194 |
| 2019 | 11.522 | 39,1% | 4.385 | 62,6% | 0,96 | 20,2% | 177 |
| 2020 | 12.734 | 44,8% | 5.592 | 58,9% | 0,92 | 25,2% | 147 |
| 2021 | 13.850 | 46,6% | 6.234 | 50,9% | 0,88 | 37,4% | 164 |
| 2022 | 9.886 | 43,4% | 4.174 | 55,8% | 0,89 | 31,6% | 143 |
| 2023 | 12.602 | 36,9% | 4.533 | 55,7% | 0,90 | 30,0% | 141 |

A mediana do CPIc é 1,00 em todos os anos.

**Achados**

- **O reporte do fecho começa em 2018** e se estabiliza perto de 45% entre 2020 e 2022. Hipótese a verificar: efeito da revisão do CCP em vigor desde janeiro de 2018.
- **A queda em 2023 é censura:** obras recentes ainda não tiveram tempo de fechar no Portal.
- **O estouro de custo salta em 2021** (de 20–25% para 37%) e segue em 30–32% em 2022–2023; o percentil 10 do CPIc piora de 0,96 para cerca de 0,88. Hipótese: alta de preços de materiais e energia em 2021–2022, período em que Portugal criou um regime excecional de revisão de preços (DL 36/2022). Explicação alternativa a controlar na Fase 3: mudança no mix de contratos.
- **A queda do atraso mediano não é melhoria:** nos anos recentes só as obras rápidas fecharam (censura). Reforça a decisão D5.

**Decisão de método**

6. D6 — Janela de análise dos índices: 2019–2022, com 2018 como robustez (ver 4.2).

**Pergunta nova para a Fase 3**

- P7 — O estouro de custo aumentou nos contratos executados durante a alta de preços de 2021–2022, mesmo controlando porte, tipo de obra e procedimento?

### 22/10/2026 — Base de modificações contratuais (2021)

**Estrutura:** os arquivos se chamam `modcontrats` + ano. O de 2021 tem 10.116 linhas e 8 colunas, todas 100% preenchidas: `idcontrato`, `modifContratoFundamento`, `modifContratoTipoAto`, `modifContratoData`, `modifContratoPrecoAlterado`, `modifPrazoExecucao`, `modifDataPublicacao` e `Ano` (ano do contrato, não da modificação). A ligação com os contratos é pelo `idcontrato`.

**Leitura das colunas:**

- O preço e o prazo alterados são os novos totais (mediana da razão sobre o contratual: 1,05 e 1,16).
- Cada linha é um fundamento; após deduplicar ficam 10.045 atos, de 6.246 contratos.
- A base inclui modificações pequenas e atos que só mudam o prazo (percentil 10 das razões = 1,00), então a regra de publicitação acima de 10% do Portal não se aplica aos dados abertos.
- Há razões extremas (até 10.464) que são erros de registo.

**Empreitadas de 2021:** 2.625 das 13.850 (19%) têm pelo menos uma modificação, com cerca de dois atos por contrato.

**Fundamentos mais frequentes (linhas, empreitadas de 2021):**

| Fundamento | Linhas |
| --- | --- |
| Trabalhos complementares (art. 370.º CCP) | 2.915 |
| Revisão ordinária de preços | 545 |
| Trabalhos complementares e trabalhos a menos | 372 |
| Trabalhos a menos (art. 379.º) | 335 |
| Alteração anormal e imprevisível das circunstâncias (art. 312.º, a) | 320 |
| Interesse público, necessidades novas (art. 312.º, b) | 161 |
| Revisão extraordinária de preços (DL 36/2022) | 139 |
| Prorrogação de prazo (art. 13.º do DL 6/2004) | 137 |
| Interesse público (art. 312.º, c) | 111 |
| Prorrogação de prazo (art. 4.º do DL 36/2022) | 104 |

Os trabalhos complementares dominam, o que confirma o diagnóstico do Tribunal de Contas sobre a falta de rigor dos projetos de execução. A crise de preços aparece explicitamente: 563 linhas ligadas à alteração anormal das circunstâncias ou ao DL 36/2022, evidência direta para a P7.

**Consistência entre as bases (empreitadas fechadas de 2021):**

|  | Efetivo diferente do contratual | Efetivo igual ao contratual |
| --- | --- | --- |
| Sem modificação registada | 40% | 60% |
| Com modificação registada | 94% | 6% |

- Quando houve modificação, o preço efetivo foi atualizado em 94% dos casos. **O efetivo não é cópia automática**, e o CPIc dos contratos fechados é confiável.
- Nos 1.145 contratos modificados e fechados, a razão efetivo ÷ preço final da última modificação tem mediana 1,00 e quartis 1,00–1,09. Quando difere, o efetivo tende a ser maior (revisão ordinária e acertos finais pagos sem novo ato).
- Ponto em aberto: 40% dos contratos fechados sem modificação têm efetivo diferente do contratual. Verificar a direção dessa diferença na Fase 1.

**Decisões de método**

7. D7 — Desenho em intervalo para o prazo: prorrogação formal como limite inferior e SPIc como limite superior (ver 4.3).
8. D8 — Preço final da última modificação como limite inferior do custo nos contratos sem fecho.
9. D9 — Base de modificações deduplicada por contrato, data, preço e prazo; estado final = último ato.

**Gate da Fase 0: cumprido em 22/10/2026,** um mês antes do previsto. Há contratos suficientes com dados de execução, as regras de limpeza estão definidas e as medidas foram validadas entre as duas bases. A auditoria manual e a checagem da Portaria 57/2018 seguem em paralelo com a Fase 1.

## 8. Diário da Fase 1

### 26/10/2026 — Estrutura, conversão e script de limpeza

**Estrutura e versionamento:** pastas `data/raw`, `data/interim`, `data/processed`, `src`, `notebooks` e `docs`. Git instalado e configurado; o `.gitignore` deixa de fora o `.venv` e todas as pastas de dados (os brutos são públicos e os demais são gerados pelos scripts). Dois commits: Fase 0 e script de limpeza.

**Conversão (`src/converter.py`):** os 15 arquivos de contratos (2012–2026) e os 5 de modificações (2018–2022) foram convertidos de xlsx para parquet em cerca de 10 minutos, sem perda de linhas. Cada ano passa a carregar em segundos.

**Limpeza e índices (`src/transform.py`):** aplica as decisões D1 a D9 a todos os anos. Nenhum contrato é apagado: cada regra vira uma coluna de flag e os índices só são calculados onde o contrato passa. Saídas: `empreitadas.parquet`, `modificacoes_atos.parquet` e `log_exclusoes.csv`.

**Validação contra a Fase 0:** os contratos válidos para custo batem com o notebook (2021: 6.231 vs. 6.234; 2022: 4.174 vs. 4.174). As diferenças de 1 a 3 contratos vêm da remoção de duplicados entre arquivos anuais e do agrupamento pela data de celebração.

**Janela 2019–2022:** 20.380 contratos com CPIc válido (estouro de custo em 29%); 20.601 com SPIc\_fecho (mediana 0,34); 7.241 empreitadas modificadas.

**Checagem do prazo formal (notebook `02_checagens_fase1`):**

- Entre as empreitadas modificadas: 45% tiveram o prazo prorrogado, 53% mantiveram o prazo (a modificação mexeu só no preço) e 2% reduziram o prazo.
- Em nenhum contrato o último ato tem prazo menor que um ato anterior. A regra "estado final = último ato" (D9) está correta.
- Nos 3.279 contratos prorrogados, a prorrogação mediana é de 39% sobre o prazo original (quartis: +19% a +78%; percentil 90: 2,4 vezes o prazo).
- **O intervalo de atraso é largo:** o limite inferior (prorrogação formal, mediana +39% nos prorrogados) e o limite superior (tempo até o fecho, mediana de cerca de 3 vezes o prazo) estão bem distantes. A auditoria manual da data de fecho ganha importância para estreitar esse intervalo.

**Observação nos anos antigos:** de 2012 a 2017, muitos contratos sem data de fecho têm preço efetivo preenchido (em 2017, 15.344 sem fecho e só 8.052 com efetivo zero). O preenchimento seguia outra lógica antes de 2018. Não altera o recorte, mas entra nas limitações.

**Pendências da Fase 1**

- [x] Conferir a distribuição do SPIc\_formal.
- [ ] Deflacionar o preço contratual com o índice de custo de construção do INE (só para a variável de porte na Fase 3; ver D10).
- [x] Validar o número e o valor das empreitadas por ano contra o relatório anual do Base (ver abaixo).
- [ ] Auditoria manual da data de fecho (cerca de 20 contratos).

### 26/10/2026 — Validação contra os relatórios anuais do Base

Os relatórios de [2021](https://www.base.gov.pt/Base4/media/burjhsro/relatório-anual-da-contratação-pública-2021.pdf), [2022](https://www.base.gov.pt/Base4/media/jv0fv3zp/relatório-anual-da-contratação-pública_2022.pdf) e [2023](https://www.base.gov.pt/Base4/media/1elfqicv/relat%C3%B3rio-anual-da-contrata%C3%A7%C3%A3o-p%C3%BAblica-2023.pdf) não publicam o número absoluto de contratos de obras, só a variação anual; os números oficiais abaixo foram reconstruídos a partir dela. Os relatórios têm inconsistências internas, e a categoria oficial de "obras públicas" inclui serviços relacionados com obras, sendo mais ampla que o filtro D1.

| Ano | Contratos oficiais (reconstr.) | Contratos nossos | Diferença | Valor oficial (M€) | Valor nosso (M€) | Diferença |
| --- | --- | --- | --- | --- | --- | --- |
| 2020 | 12.894 | 12.733 | −1,2% | 3.547 | 3.933 | +10,9% |
| 2021 | 15.215 | 13.844 | −9,0% | 4.435 | 3.742 | −15,6% |
| 2022 | 10.605 | 9.882 | −6,8% | 2.813 | 2.733 | −2,9% |
| 2023 | 13.002 | 12.461 | −4,2% | ≈ 4.140 | 4.562 | +10,2% |

- **Contagem: aprovada.** Todos os anos ficam até 10% abaixo dos oficiais, na direção esperada pelo filtro mais estreito.
- **Valor: diferenças explicadas, sem erros de registo.** Os 10 maiores contratos de cada ano são todos obras reais de grande porte (Metro do Porto, Metropolitano de Lisboa, Infraestruturas de Portugal, APDL), com preço contratual próximo do preço base. Eles concentram 24% do valor em 2020 e 2023; um único contrato (Metro do Porto, 379 M€ em 2023) muda o total anual em cerca de 9%. Diferenças de classificação ou de ano de registo desses megaprojetos explicam as oscilações de ±16%.
- **Achado lateral:** alguns contratos têm `precoBaseProcedimento` igual a zero (por exemplo, três da REN em 2023). Zero significa "não informado", como no preço efetivo; vale a mesma regra se o preço base for usado.

**Decisões de método**

10. D10 — Os índices (CPIc, SPIc) não são deflacionados: a inflação durante a execução faz parte do desvio medido (P7). A deflação aplica-se só ao preço contratual usado como variável de porte.
11. D11 — Resultados agregados usam medianas e percentagens de contratos, não somas em euros, que são dominadas por poucos megaprojetos. Os megaprojetos (por exemplo, acima de 50 M€) são analisados também à parte, na linha de Flyvbjerg.
12. D12 — `precoBaseProcedimento` igual a zero é tratado como ausente.

**Gate da Fase 1: cumprido em 26/10/2026,** com a ressalva do valor documentada acima. Ficam para o início da Fase 3: a deflação (D10) e a auditoria manual da data de fecho.

## Referências

Formato ABNT. Itens marcados "(a conferir)" precisam de verificação dos dados completos antes da versão final.

AHIAGA-DAGBUI, D. D.; SMITH, S. D. Rethinking construction cost overruns: cognition, learning and estimation. **Journal of Financial Management of Property and Construction**, v. 19, n. 1, p. 38-54, 2014. Disponível em: [Emerald](https://emerald.com/insight/content/doi/10.1108/JFMPC-06-2013-0027/full/html).

BRASIL. Tribunal de Contas da União. **Acórdão 1.079/2019 – Plenário**. Auditoria operacional sobre obras paralisadas. Rel. Min. Vital do Rêgo, 15 maio 2019. Ver: [TCU – Auditoria operacional em obras paralisadas](https://portal.tcu.gov.br/data/files/8F/12/9D/F2/4281671023455957E18818A8/Auditoria_operacional_obras_paralisadas.pdf).

BRASIL. Tribunal de Contas da União. **Monitoramento de obras paralisadas** (Acórdão 1.328/2020 – Plenário). Disponível em: [TCU](https://portal.tcu.gov.br/data/files/6B/E7/E8/14/6E0BC8103A4A64C8F18818A8/Monitoramento%20de%20Obras%20Paralisadas.pdf).

BRASIL. Ministério da Gestão e da Inovação em Serviços Públicos. **API de Dados Abertos Obrasgov.br**. Disponível em: [gov.br](https://www.gov.br/obrasgov/pt-br/ferramentas-de-gestao-e-transparencia/api-de-dados-abertos-obrasgov-br_novo).

BRASIL. **Lei n.º 14.133, de 1.º de abril de 2021**. Lei de Licitações e Contratos Administrativos. (a conferir)

CANTARELLI, C. C.; FLYVBJERG, B.; MOLIN, E. J. E.; VAN WEE, B. Cost overruns in large-scale transportation infrastructure projects: explanations and their theoretical embeddedness. **European Journal of Transport and Infrastructure Research**, v. 10, n. 1, p. 5-18, 2010. DOI: [10.18757/ejtir.2010.10.1.2864](https://doi.org/10.18757/ejtir.2010.10.1.2864).

DESVIOS de prazos e de custos na execução de empreitadas de obras públicas. 2012. Dissertação (Mestrado em Engenharia Civil) – Universidade Lusófona. Disponível em: [ReCiL](https://recil.ulusofona.pt/items/9317ccde-8159-4582-9b3c-5188dd5e5de9). (autor a conferir)

FLYVBJERG, B.; HOLM, M. S.; BUHL, S. Underestimating costs in public works projects: error or lie? **Journal of the American Planning Association**, v. 68, n. 3, p. 279-295, 2002. DOI: 10.1080/01944360208976273. Disponível em: [arXiv](https://arxiv.org/abs/1303.6604).

LIPKE, W. Schedule is different. **The Measurable News**, mar. 2003. Disponível em: [earnedschedule.com](https://www.earnedschedule.com/Docs/Schedule%20is%20Different.pdf).

LOVE, P. E. D.; AHIAGA-DAGBUI, D. D. Debunking fake news in a post-truth era: the plausible untruths of cost underestimation in transport infrastructure projects. **Transportation Research Part A: Policy and Practice**, v. 113, p. 357-368, 2018. Disponível em: [IDEAS/RePEc](https://ideas.repec.org/a/eee/transa/v113y2018icp357-368.html).

PORTUGAL. **Decreto-Lei n.º 18/2008, de 29 de janeiro**. Aprova o Código dos Contratos Públicos (versão consolidada). Disponível em: [FAOLEX](https://faolex.fao.org/docs/pdf/por238404.pdf).

PORTUGAL. **Portaria n.º 701-F/2008**. Portal dos Contratos Públicos e modelos de relatório. Disponível em: [Madeira.gov.pt](https://www.madeira.gov.pt//Portals/23/Documentos/ContratacaoPublica/Portaria%20701-F_2008.pdf).

PORTUGAL. **Portaria n.º 318-B/2023**. Portal Base. Disponível em: [base.gov.pt](https://www.base.gov.pt/Base4/media/aezdh4bi/portaria-318-b_2023_portal-base.pdf).

IMPIC – Instituto dos Mercados Públicos, do Imobiliário e da Construção. **Contratos Públicos – Portal Base – Contratos de 2012 a 2026**. dados.gov.pt. Disponível em: [dados.gov.pt](https://dados.gov.pt/en/datasets/contratos-publicos-portal-base-impic-contratos-de-2012-a-2026/).

IMPIC. **Contratos Públicos – Portal Base – Modificações contratuais de 2012 a 2026**. Disponível em: [dados.gov.pt](https://dados.gov.pt/es/datasets/contratos-publicos-portal-base-impic-modificacoes-contratuais-de-2012-a-2026/).

IMPIC. **Relatório anual da contratação pública 2023**. Disponível em: [base.gov.pt](https://www.base.gov.pt/Base4/media/1elfqicv/relat%C3%B3rio-anual-da-contrata%C3%A7%C3%A3o-p%C3%BAblica-2023.pdf).

PROJECT MANAGEMENT INSTITUTE. **Practice standard for earned value management**. 2. ed. Newtown Square: PMI, 2011.

PROJECT MANAGEMENT INSTITUTE. **The standard for earned value management**. Newtown Square: PMI, 2019. Disponível em: [PMI](https://www.pmi.org/shop/p-/book/the-standard-for-earned-value-management/00101618501).

TRIBUNAL DE CONTAS (Portugal). **Relatório da ação de fiscalização concomitante – Contratos adicionais, triénio 2020-2022**. 2023. Resumo em: [Cuatrecasas](https://www.cuatrecasas.com/pt/global/art/contratos-adicionais-relatorio-tribunal-de-contas-1). (localizar o relatório original no site do Tribunal)

**Leituras recomendadas para a Fase 3** (a selecionar com a pós): um manual de econometria aplicada (ex.: Wooldridge, *Introdução à Econometria*) para regressão logística, erros agrupados e diagnóstico de modelos.
