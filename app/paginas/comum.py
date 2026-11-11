"""Peças usadas por mais de uma página do aplicativo."""
import math
from dataclasses import dataclass
from datetime import date

import streamlit as st

from app import db

DIVISOES = ["proporcional", "50/50", "individual"]
NOME_DIVISAO = {"proporcional": "Proporcional à renda", "50/50": "50/50", "individual": "Só de quem lançou"}
NOME_TIPO = {"saida": "Gasto", "entrada": "Entrada"}


@dataclass
class Contexto:
    con: object
    uid: int
    hoje: date
    pessoa: dict | None
    ano: int
    mes: int


def campos_lancamento(con, uid, prefixo: str, padrao: dict):
    """Desenha os campos de um lançamento. Os valores ficam em st.session_state[prefixo + campo].

    padrao: tipo, valor (reais), data, categoria_id, conta_id, regra_divisao, descricao
    """
    c1, c2, c3 = st.columns([1, 1, 1])
    tipo = c1.radio("Tipo", ["saida", "entrada"], key=f"{prefixo}tipo", horizontal=True,
                    format_func=NOME_TIPO.get, index=0 if padrao.get("tipo", "saida") == "saida" else 1)
    c2.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f", key=f"{prefixo}valor",
                    value=float(padrao.get("valor") or 0.0))
    c3.date_input("Data", key=f"{prefixo}data", value=padrao.get("data") or date.today(), format="DD/MM/YYYY")

    cats = {c["id"]: c for c in db.categorias(con, uid, tipo=tipo)}
    contas = {c["id"]: c for c in db.contas(con, uid)}
    cat_ids = list(cats)
    cat_padrao = padrao.get("categoria_id")
    c4, c5, c6 = st.columns([1, 1, 1])
    c4.selectbox("Categoria", cat_ids, key=f"{prefixo}categoria", format_func=lambda i: cats[i]["nome"],
                 index=cat_ids.index(cat_padrao) if cat_padrao in cat_ids else 0)
    conta_ids = [None] + list(contas)
    conta_padrao = padrao.get("conta_id")
    c5.selectbox("Forma de pagamento", conta_ids, key=f"{prefixo}conta",
                 format_func=lambda i: "— escolha —" if i is None else contas[i]["nome"],
                 index=conta_ids.index(conta_padrao) if conta_padrao in conta_ids else 0,
                 disabled=tipo == "entrada")
    regra = padrao.get("regra_divisao")
    c6.selectbox("Divisão", DIVISOES, key=f"{prefixo}divisao", format_func=NOME_DIVISAO.get,
                 index=DIVISOES.index(regra) if regra in DIVISOES else 0)
    st.text_input("Descrição", key=f"{prefixo}descricao", value=padrao.get("descricao") or "")


def ler_campos(prefixo: str) -> dict:
    s = st.session_state
    return {
        "tipo": s[f"{prefixo}tipo"],
        "valor_centavos": round((s[f"{prefixo}valor"] or 0) * 100),
        "data": s[f"{prefixo}data"],
        "categoria_id": s[f"{prefixo}categoria"],
        "conta_id": None if s[f"{prefixo}tipo"] == "entrada" else s[f"{prefixo}conta"],
        "regra_divisao": s[f"{prefixo}divisao"],
        "descricao": (s[f"{prefixo}descricao"] or "").strip(),
    }


def validar(campos: dict) -> str | None:
    if campos["valor_centavos"] <= 0:
        return "Informe um valor maior que zero."
    if campos["tipo"] == "saida" and campos["conta_id"] is None:
        return "Escolha a forma de pagamento."
    if campos["categoria_id"] is None:
        return "Escolha a categoria."
    return None


def registros(df) -> list[dict]:
    """DataFrame do editor → lista de dicts, trocando NaN/NaT por None."""
    saida = []
    for linha in df.to_dict("records"):
        limpa = {}
        for k, v in linha.items():
            if v is None or (isinstance(v, float) and math.isnan(v)):
                v = None
            elif hasattr(v, "item"):
                v = v.item()
            limpa[k] = v
        saida.append(limpa)
    return saida


def mostrar_aviso():
    """Mostra (uma vez) a mensagem deixada por um callback."""
    msg = st.session_state.pop("_aviso", None)
    if msg:
        tipo, texto = msg
        (st.success if tipo == "ok" else st.error)(texto)


def avisar(tipo: str, texto: str):
    st.session_state["_aviso"] = (tipo, texto)
