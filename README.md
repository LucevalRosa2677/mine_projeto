# Pipeline de Sanitização de Dados - Olist

## Descrição do Projeto

A Olist processa milhões de transações de e-commerce que alimentam relatórios de Business Intelligence e modelos de Machine Learning. Os lotes extraídos do banco oficial (`olist_products_dataset.csv` e `olist_orders_dataset.csv`) apresentavam inconsistências — categorias vazias, dimensões físicas ausentes, datas de entrega incompletas e formatos temporais heterogêneos — bloqueando relatórios automatizados.

Este projeto implementa um **pipeline ETL de sanitização** em Python puro (sem Pandas), aplicando regras de negócio, expressões regulares e formatação temporal para entregar bases confiáveis para análise e modelagem.

### O que o script faz

| Etapa | Arquivo | Ação |
|-------|---------|------|
| Produtos | `olist_products_dataset.csv` | Preenche categorias vazias, padroniza strings com `re`, imputa dimensões físicas pela média |
| Pedidos | `olist_orders_dataset.csv` | Valida hipótese de entregas vazias vs. cancelamento, formata `order_approved_at` para `DD/MM/YYYY` |
| Saída | `dados_sanitizados/` | Gera CSVs tratados e exibe relatório estatístico no terminal |

## Estrutura do Repositório

```
.
├── dados/                          # CSVs originais (não versionar se forem muito grandes)
├── dados_sanitizados/              # CSVs gerados pelo pipeline
├── funcoes.py                      # Funções modulares de transformação
├── main.py                         # Orquestração e relatório final
└── README.md
```

## Guia de Execução

### Pré-requisitos

- Python 3.8 ou superior
- Apenas biblioteca padrão (sem `pip install`)

### 1. Obter os dados

Clone ou baixe os CSVs do repositório oficial:

[https://github.com/fiesc-junior-prado/mine_projeto_bloco_1](https://github.com/fiesc-junior-prado/mine_projeto_bloco_1)

Coloque os arquivos na pasta `dados/`:

- `dados/olist_products_dataset.csv`
- `dados/olist_orders_dataset.csv`

### 2. Executar o pipeline

No terminal, na raiz do projeto:

```bash
python main.py
```

### 3. Resultado esperado

- Arquivos sanitizados em `dados_sanitizados/`
- Relatório no console com: linhas processadas, nulos corrigidos, pedidos cancelados e validação da hipótese de negócio

## Decisões Técnicas

**Categorias vazias:** preenchidas com `"Sem Categoria"` e depois padronizadas para `sem_categoria`.

**Dimensões físicas nulas (`product_weight_g`, `product_length_cm`, etc.):** imputação pela **média global** da coluna. Descartar registros reduziria o catálogo sem necessidade; valores médios mantêm a base utilizável para BI e evitam distorções extremas de modelos.

**Hipótese de entregas vazias:** o script separa pedidos sem `order_delivered_customer_date` e verifica se `order_status == canceled`. Na base analisada, a hipótese **não se confirma integralmente** — há entregas vazias também em status como `shipped`, `invoiced` e `unavailable`.

## Reflexão Teórica sobre Machine Learning

A qualidade dos dados de entrada define o teto de desempenho de qualquer modelo supervisionado. Quando categorias inconsistentes, valores ausentes tratados de forma ad hoc ou datas mal formatadas chegam ao treinamento, o algoritmo pode memorizar ruído em vez de padrões reais — fenômeno associado ao **overfitting** — ou falhar em capturar relações relevantes (**underfitting**), gerando previsões enviesadas. Um pipeline de limpeza explícito, com regras documentadas (imputação, padronização, filtros de negócio), reduz o risco de **Garbage In, Garbage Out** e torna o comportamento do modelo auditável.

Em contextos como a Black Friday, onde o volume e a pressão sobre decisões automatizadas aumentam, dados sanitizados de forma reproduzível permitem que features (peso, categoria, status do pedido, datas) representem a realidade operacional com menor viés. Isso não garante modelo perfeito, mas estabelece uma fundação necessária para generalização em produção e para comparações justas entre experimentos de IA.

## Fonte dos Dados

- Repositório de dados: [fiesc-junior-prado/mine_projeto_bloco_1](https://github.com/fiesc-junior-prado/mine_projeto_bloco_1)

## Autor Luceval Rosa Jr


Projeto desenvolvido no âmbito do **Módulo 1 - Mini-Projeto Avaliativo** (Mini / Inteligência Artificial e Visão Computacional).
