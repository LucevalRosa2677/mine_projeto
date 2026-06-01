"""
Funções auxiliares do pipeline de sanitização Olist.
Utiliza apenas bibliotecas nativas: csv, re, datetime.
"""

import csv
import re
from datetime import datetime
from pathlib import Path



# Colunas numéricas de dimensões físicas do catálogo de produtos
COLUNAS_DIMENSOES = (
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
)

# Padrão regex: remove pontuação e símbolos, preservando letras, números e underscore
REGEX_LIMPEZA_CATEGORIA = re.compile(r"[^a-z0-9_\s]")
REGEX_ESPACOS_MULTIPLOS = re.compile(r"\s+")


def valor_vazio(valor):
    """Retorna True se o valor for None, string vazia ou apenas espaços."""
    return valor is None or str(valor).strip() == ""


def padronizar_categoria(nome_categoria):
    """
    Padroniza o nome da categoria: minúsculas, strip e limpeza via regex.
    Espaços internos viram underscore para manter consistência (ex: esporte_lazer).
    """
    if valor_vazio(nome_categoria):
        nome_categoria = "sem_categoria"
    texto = str(nome_categoria).lower().strip()
    texto = REGEX_LIMPEZA_CATEGORIA.sub("", texto)
    texto = REGEX_ESPACOS_MULTIPLOS.sub("_", texto).strip("_")
    return texto if texto else "sem_categoria"


def calcular_medias_dimensoes(caminho_arquivo):
    """
    Primeira passagem: calcula a média aritmética de cada dimensão física
    considerando apenas registros com valor numérico válido.
    """
    somas = {coluna: 0.0 for coluna in COLUNAS_DIMENSOES}
    contagens = {coluna: 0 for coluna in COLUNAS_DIMENSOES}

    with open(caminho_arquivo, mode="r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            for coluna in COLUNAS_DIMENSOES:
                valor = linha.get(coluna, "")
                if not valor_vazio(valor):
                    try:
                        somas[coluna] += float(valor)
                        contagens[coluna] += 1
                    except ValueError:
                        pass

    medias = {}
    for coluna in COLUNAS_DIMENSOES:
        if contagens[coluna] > 0:
            medias[coluna] = round(somas[coluna] / contagens[coluna], 2)
        else:
            medias[coluna] = 0.0
    return medias


def sanitizar_produtos(caminho_entrada, caminho_saida, medias_dimensoes):
    """
    Lê o CSV de produtos linha a linha, aplica regras de negócio e grava saída.

    Regra para dimensões físicas nulas: imputação pela média global da coluna.
    Justificativa: descartar linhas removeria produtos válidos do catálogo; a média
    preserva o volume da base e reduz viés extremo frente a valores zerados arbitrários.
    """
    estatisticas = {
        "linhas_processadas": 0,
        "categorias_corrigidas": 0,
        "dimensoes_corrigidas": 0,
    }

    with open(caminho_entrada, mode="r", encoding="utf-8", newline="") as entrada, open(
        caminho_saida, mode="w", encoding="utf-8", newline=""
    ) as saida:
        leitor = csv.DictReader(entrada)
        escritor = csv.DictWriter(saida, fieldnames=leitor.fieldnames)
        escritor.writeheader()

        for linha in leitor:
            estatisticas["linhas_processadas"] += 1

            if valor_vazio(linha.get("product_category_name")):
                linha["product_category_name"] = "Sem Categoria"
                estatisticas["categorias_corrigidas"] += 1

            categoria_anterior = linha["product_category_name"]
            linha["product_category_name"] = padronizar_categoria(categoria_anterior)

            for coluna in COLUNAS_DIMENSOES:
                if valor_vazio(linha.get(coluna)):
                    linha[coluna] = str(medias_dimensoes[coluna])
                    estatisticas["dimensoes_corrigidas"] += 1

            escritor.writerow(linha)

    return estatisticas


def formatar_data_brasileira(data_str):
    """
    Converte 'YYYY-MM-DD HH:MM:SS' para 'DD/MM/YYYY'.
    Retorna string vazia se a data de entrada for nula ou inválida.
    """
    if valor_vazio(data_str):
        return ""
    try:
        data_obj = datetime.strptime(data_str.strip(), "%Y-%m-%d %H:%M:%S")
        return data_obj.strftime("%d/%m/%Y")
    except ValueError:
        return ""


def analisar_entregas_vazias(caminho_arquivo):
    """
    Valida a hipótese de negócio: entregas vazias estão associadas a pedidos cancelados?
    Retorna contadores para o relatório final.
    """
    resultado = {
        "entrega_vazia_total": 0,
        "entrega_vazia_cancelado": 0,
        "entrega_vazia_outros_status": 0,
        "pedidos_cancelados_total": 0,
        "status_entrega_vazia": {},
    }

    with open(caminho_arquivo, mode="r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            status = (linha.get("order_status") or "").strip().lower()

            if status == "canceled":
                resultado["pedidos_cancelados_total"] += 1

            if valor_vazio(linha.get("order_delivered_customer_date")):
                resultado["entrega_vazia_total"] += 1
                resultado["status_entrega_vazia"][status] = (
                    resultado["status_entrega_vazia"].get(status, 0) + 1
                )
                if status == "canceled":
                    resultado["entrega_vazia_cancelado"] += 1
                else:
                    resultado["entrega_vazia_outros_status"] += 1

    return resultado


def sanitizar_pedidos(caminho_entrada, caminho_saida):
    """Formata order_approved_at e grava pedidos sanitizados."""
    estatisticas = {"linhas_processadas": 0, "datas_formatadas": 0}

    with open(caminho_entrada, mode="r", encoding="utf-8", newline="") as entrada, open(
        caminho_saida, mode="w", encoding="utf-8", newline=""
    ) as saida:
        leitor = csv.DictReader(entrada)
        escritor = csv.DictWriter(saida, fieldnames=leitor.fieldnames)
        escritor.writeheader()

        for linha in leitor:
            estatisticas["linhas_processadas"] += 1
            data_aprovacao = linha.get("order_approved_at", "")
            if not valor_vazio(data_aprovacao):
                data_formatada = formatar_data_brasileira(data_aprovacao)
                if data_formatada:
                    linha["order_approved_at"] = data_formatada
                    estatisticas["datas_formatadas"] += 1
            escritor.writerow(linha)

    return estatisticas


REGEX_DATA_BR = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def validar_base_sanitizada(caminho_produtos, caminho_pedidos):
    """
    Verifica os arquivos de saída: ausência de nulos críticos em produtos
    e formato brasileiro nas datas de aprovação preenchidas.
    """
    validacao = {
        "produtos_nulos_categoria": 0,
        "produtos_nulos_dimensao": 0,
        "pedidos_datas_invalidas": 0,
        "base_sanitizada": False,
    }

    with open(caminho_produtos, mode="r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            if valor_vazio(linha.get("product_category_name")):
                validacao["produtos_nulos_categoria"] += 1
            for coluna in COLUNAS_DIMENSOES:
                if valor_vazio(linha.get(coluna)):
                    validacao["produtos_nulos_dimensao"] += 1

    with open(caminho_pedidos, mode="r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            data_aprovacao = linha.get("order_approved_at", "")
            if not valor_vazio(data_aprovacao) and not REGEX_DATA_BR.match(
                str(data_aprovacao).strip()
            ):
                validacao["pedidos_datas_invalidas"] += 1

    produtos_ok = (
        validacao["produtos_nulos_categoria"] == 0
        and validacao["produtos_nulos_dimensao"] == 0
    )
    pedidos_ok = validacao["pedidos_datas_invalidas"] == 0
    validacao["base_sanitizada"] = produtos_ok and pedidos_ok
    return validacao


def garantir_diretorio(caminho):
    """Cria o diretório de saída se ainda não existir."""
    Path(caminho).mkdir(parents=True, exist_ok=True)
