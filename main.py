"""
Pipeline de sanitização de dados Olist - Módulo 1.
Orquestra leitura, transformação e relatório estatístico manual.
"""

from pathlib import Path

from funcoes import (
    analisar_entregas_vazias,
    calcular_medias_dimensoes,
    garantir_diretorio,
    sanitizar_pedidos,
    sanitizar_produtos,
    validar_base_sanitizada,
)

# Caminhos relativos ao diretório do script
BASE_DIR = Path(__file__).resolve().parent
PASTA_DADOS = BASE_DIR / "dados"
PASTA_SAIDA = BASE_DIR / "dados_sanitizados"

ARQUIVO_PRODUTOS_ENTRADA = PASTA_DADOS / "olist_products_dataset.csv"
ARQUIVO_PEDIDOS_ENTRADA = PASTA_DADOS / "olist_orders_dataset.csv"
ARQUIVO_PRODUTOS_SAIDA = PASTA_SAIDA / "olist_products_sanitizado.csv"
ARQUIVO_PEDIDOS_SAIDA = PASTA_SAIDA / "olist_orders_sanitizado.csv"


def exibir_relatorio(
    stats_produtos,
    stats_pedidos,
    analise_entregas,
    nulos_corrigidos_total,
    validacao,
):
    """Monta e imprime o sumário estatístico manual na tela."""
    linhas_total = stats_produtos["linhas_processadas"] + stats_pedidos["linhas_processadas"]
    pedidos_cancelados = analise_entregas["pedidos_cancelados_total"]

    entrega_vazia = analise_entregas["entrega_vazia_total"]
    cancel_vazio = analise_entregas["entrega_vazia_cancelado"]
    percentual_cancel = 0.0
    if entrega_vazia > 0:
        percentual_cancel = (cancel_vazio / entrega_vazia) * 100

    hipotese_confirmada = (
        entrega_vazia > 0
        and cancel_vazio == entrega_vazia
    )

    print("\n" + "=" * 60)
    print(" RELATÓRIO DE SANITIZAÇÃO - OLIST")
    print("=" * 60)
    print("SUMÁRIO ESTATÍSTICO (construído manualmente)")
    print("-" * 60)
    print(f"1. Total de linhas processadas:        {linhas_total}")
    print(f"   - Produtos: {stats_produtos['linhas_processadas']}")
    print(f"   - Pedidos:  {stats_pedidos['linhas_processadas']}")
    print(f"2. Total de registros nulos corrigidos: {nulos_corrigidos_total}")
    print(f"3. Total de pedidos cancelados:         {pedidos_cancelados}")
    print("-" * 60)
    print("DETALHAMENTO DAS CORREÇÕES")
    print(f"  - Categorias preenchidas ('Sem Categoria'): {stats_produtos['categorias_corrigidas']}")
    print(f"  - Dimensões físicas imputadas (média):      {stats_produtos['dimensoes_corrigidas']}")
    print(f"  - Datas de aprovação convertidas (BR):      {stats_pedidos['datas_formatadas']}")
    print("-" * 60)
    print("VALIDAÇÃO DA BASE SANITIZADA")
    if validacao["base_sanitizada"]:
        print("Resultado: BASE SANITIZADA — critérios de qualidade atendidos.")
    else:
        print("Resultado: BASE COM PENDÊNCIAS — revisar itens abaixo.")
    print(
        f"  - Produtos: categorias vazias = {validacao['produtos_nulos_categoria']}, "
        f"dimensões vazias = {validacao['produtos_nulos_dimensao']}"
    )
    print(
        f"  - Pedidos: datas de aprovação fora do padrão DD/MM/AAAA = "
        f"{validacao['pedidos_datas_invalidas']}"
    )
    print("-" * 60)
    print(f"Total de pedidos cancelados na base: {pedidos_cancelados}")
    print(f"Pedidos com data de entrega vazia:   {entrega_vazia}")
    print(f"  - Com status 'canceled':           {cancel_vazio}")
    print(f"  - Com outros status:               {analise_entregas['entrega_vazia_outros_status']}")
    print("-" * 60)
    print("HIPÓTESE DE NEGÓCIO (entrega vazia = pedido cancelado?)")
    if hipotese_confirmada:
        print("Resultado: CONFIRMADA - todas as entregas vazias são cancelamentos.")
    else:
        print(
            f"Resultado: NÃO CONFIRMADA integralmente - apenas "
            f"{percentual_cancel:.1f}% das entregas vazias são 'canceled'."
        )
        print("Distribuição por status (entrega vazia):")
        for status, quantidade in sorted(
            analise_entregas["status_entrega_vazia"].items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            print(f"    * {status or '(vazio)'}: {quantidade}")
    print("-" * 60)
    print("Arquivos gerados:")
    print(f"  - {ARQUIVO_PRODUTOS_SAIDA}")
    print(f"  - {ARQUIVO_PEDIDOS_SAIDA}")
    print("=" * 60 + "\n")


def main():
    """Fluxo principal do pipeline ETL de sanitização."""
    if not ARQUIVO_PRODUTOS_ENTRADA.exists() or not ARQUIVO_PEDIDOS_ENTRADA.exists():
        print(
            "ERRO: Coloque os arquivos CSV em 'dados/':\n"
            "  - olist_products_dataset.csv\n"
            "  - olist_orders_dataset.csv\n"
            "Fonte: https://github.com/fiesc-junior-prado/mine_projeto_bloco_1"
        )
        return

    garantir_diretorio(PASTA_SAIDA)

    print("Iniciando pipeline de sanitização Olist...")

    # Análise de regra de negócio antes da transformação de pedidos (dados brutos)
    analise_entregas = analisar_entregas_vazias(ARQUIVO_PEDIDOS_ENTRADA)

    # Produtos: médias -> sanitização
    medias = calcular_medias_dimensoes(ARQUIVO_PRODUTOS_ENTRADA)
    stats_produtos = sanitizar_produtos(
        ARQUIVO_PRODUTOS_ENTRADA,
        ARQUIVO_PRODUTOS_SAIDA,
        medias,
    )

    # Pedidos: formatação de datas
    stats_pedidos = sanitizar_pedidos(
        ARQUIVO_PEDIDOS_ENTRADA,
        ARQUIVO_PEDIDOS_SAIDA,
    )

    nulos_corrigidos_total = (
        stats_produtos["categorias_corrigidas"]
        + stats_produtos["dimensoes_corrigidas"]
    )

    validacao = validar_base_sanitizada(
        ARQUIVO_PRODUTOS_SAIDA,
        ARQUIVO_PEDIDOS_SAIDA,
    )

    exibir_relatorio(
        stats_produtos,
        stats_pedidos,
        analise_entregas,
        nulos_corrigidos_total,
        validacao,
    )


if __name__ == "__main__":
    main()
