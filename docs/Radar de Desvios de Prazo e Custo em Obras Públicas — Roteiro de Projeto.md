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
| [IMPIC – Modificações contratuais 2012–2026](https://dados.gov.pt/es/datasets/contratos-publicos-portal-base-impic-modificacoes-contratuais-de-2012-a-2026/) | Alterações de preço e prazo | Aberto, semestral | Indicador alternativo de desvio |
| [Relatórios anuais da contratação pública (Base)](https://www.base.gov.pt/Base4/media/1elfqicv/relat%C3%B3rio-anual-da-contrata%C3%A7%C3%A3o-p%C3%BAblica-2023.pdf) | Totais oficiais por ano | PDF | Validação dos totais |
| INE – índices de preços (a definir) | Inflação / custos de construção | CSV | Deflação de valores |
| [ObrasGov – API pública](https://www.gov.br/obrasgov/pt-br/ferramentas-de-gestao-e-transparencia/api-de-dados-abertos-obrasgov-br_novo) | Obras federais, execução física | API REST | Fase 2 |

### 4.2 Recorte da população

1. Tipo de contrato = empreitadas de obras públicas.
2. Data de celebração entre 2012 e o último ano com contratos majoritariamente encerrados (definir após a etapa 4.4).
3. Para os índices de execução: apenas contratos com preço efetivo e data de fecho preenchidos e válidos.

### 4.3 Indicadores (adaptação da EVM a contratos encerrados)

Como cada contrato é observado uma vez, já encerrado, os índices comparam o compromisso inicial (equivalente à linha de base) com o resultado final:

```latex
CPI_c = \frac{\text{pre\c{c}o contratual}}{\text{pre\c{c}o total efetivo}} \qquad SPI_c = \frac{\text{prazo contratual (dias)}}{\text{data de fecho} - \text{data de celebra\c{c}\~ao}}
```

Valores abaixo de 1 indicam estouro de custo ou atraso. Para leitura em percentagem, usa-se também o desvio relativo:

```latex
\Delta_{custo} = \frac{\text{efetivo} - \text{contratual}}{\text{contratual}} \qquad \Delta_{prazo} = \frac{\text{realizado} - \text{previsto}}{\text{previsto}}
```

Indicador alternativo, para contratos sem fecho registado: soma das modificações de preço ÷ preço contratual, a partir da base de modificações.

Limitação assumida: a data de celebração é uma aproximação do início real da obra (o auto de consignação pode ser posterior), o que tende a superestimar o atraso. O nome exato de cada campo será confirmado no dicionário de dados do IMPIC.

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

- **Viés de seleção:** se só os contratos bem geridos reportam o fecho, os desvios ficam subestimados. A etapa 1 mede esse risco e ele é declarado nas conclusões.
- **Qualidade do registo:** os dados são declarados pelas próprias entidades, sem auditoria campo a campo.
- **Causalidade:** a regressão mostra associação, não causa.
- **Escopo:** o projeto mede o crescimento de custo após a assinatura, não a subestimação na fase de decisão (ver 3.3).
- **Comparação PT × BR (fase 2):** universos diferentes (todas as entidades vs. obras federais) e moedas diferentes; a comparação será feita sobre índices adimensionais e com ressalvas explícitas.

## 5. Plano de execução

O projeto avança em cinco fases, cada uma fechada por um critério de passagem (gate), na ordem dos seus estudos. As datas ficam em aberto até você definir o ritmo semanal disponível.

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

- [ ] Qual o ritmo semanal disponível, para converter as fases em datas?
- [ ] O painel será Streamlit (mais "dados") ou Looker Studio (mais rápido)?
- [ ] Algum orientador da pós pode revisar o método da Fase 3?

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
