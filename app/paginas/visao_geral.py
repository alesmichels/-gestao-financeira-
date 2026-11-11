"""Página Visão geral: números do mês."""
from datetime import date

import pandas as pd
import streamlit as st

from app import db, resumos
from app.paginas.comum import Contexto, mostrar_aviso
from app.resumos import brl
from app.servico import MESES


def render(ctx: Contexto):
    con, uid = ctx.con, ctx.uid
    inicio, fim = resumos.mes_inteiro(ctx.ano, ctx.mes)
    st.header(f"Visão geral · {MESES[ctx.mes - 1]} {ctx.ano}")
    mostrar_aviso()

    pend = db.pendentes(con, uid)
    if pend:
        with st.expander(f"{len(pend)} lançamento(s) aguardando confirmação", expanded=True):
            for l in pend:
                c1, c2, c3 = st.columns([6, 1, 1])
                c1.write(f"{date.fromisoformat(l['data']):%d/%m} · {l['descricao']} · {brl(l['valor_centavos'])} "
                         f"· lançado por {l['autor'] or '?'}")
                if c2.button("Confirmar", key=f"ok{l['id']}", disabled=l["tipo"] == "saida" and not l["conta_id"]):
                    db.atualizar_lancamento(con, l["id"], acao="confirmado", status="confirmado")
                    st.rerun()
                if c3.button("Cancelar", key=f"cx{l['id']}"):
                    db.atualizar_lancamento(con, l["id"], acao="cancelado", status="cancelado")
                    st.rerun()

    r = resumos.resumo_periodo(con, uid, inicio, fim)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Receitas", brl(r["entradas"]))
    k2.metric("Gastos", brl(r["saidas"]))
    k3.metric("Saldo", brl(r["saldo"]))
    k4.metric("Lançamentos confirmados", r["qtd"])

    if r["qtd"] == 0:
        st.info("Nenhum lançamento neste mês ainda. Vá em **Lançamentos** para registrar o primeiro.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Gastos por categoria")
        if r["categorias"]:
            df = pd.DataFrame(r["categorias"], columns=["Categoria", "centavos"])
            df["Valor (R$)"] = df["centavos"] / 100
            st.bar_chart(df, x="Categoria", y="Valor (R$)", horizontal=True, sort="-Valor (R$)")
        else:
            st.caption("Sem gastos confirmados neste mês.")
    with col_b:
        st.subheader("Formas de pagamento")
        if r["contas"]:
            st.dataframe(pd.DataFrame([(n, brl(v)) for n, v in r["contas"]], columns=["Forma", "Valor"]),
                         hide_index=True, width="stretch")
        else:
            st.caption("Sem gastos confirmados neste mês.")

        st.subheader("Acerto do casal")
        ac = resumos.acerto(con, uid, inicio, fim)
        st.dataframe(pd.DataFrame([(p["nome"], brl(p["pagou"]), brl(p["deveria"])) for p in ac["pessoas"]],
                                  columns=["Pessoa", "Pagou", "Parte dele(a)"]), hide_index=True, width="stretch")
        if ac["valor"] >= 1 and ac["de"] != ac["para"]:
            st.write(f"**{ac['de']} transfere {brl(ac['valor'])} para {ac['para']}.**")
        else:
            st.write("Tudo acertado.")

    st.subheader("Faturas abertas (hoje)")
    fs = resumos.faturas(con, uid, ctx.hoje)
    if fs:
        st.dataframe(pd.DataFrame([{
            "Cartão": f["conta"], "Valor": brl(f["total"]), "Fecha": f"{f['fechamento']:%d/%m}",
            "Vence": f"{f['vencimento']:%d/%m}" if f["vencimento"] else "", "Dias para fechar": f["dias_para_fechar"],
        } for f in fs]), hide_index=True, width="stretch")
    else:
        st.caption("Nenhum cartão de crédito com dia de fechamento. Ajuste em Configurações.")
