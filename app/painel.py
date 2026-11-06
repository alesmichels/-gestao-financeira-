"""Painel no navegador (Fase 1: visão geral simples).

Uso:  streamlit run app/painel.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import config, db, resumos  # noqa: E402
from app.resumos import brl  # noqa: E402
from app.servico import MESES  # noqa: E402

st.set_page_config(page_title="Gestão Financeira", layout="wide")


@st.cache_resource
def conexao():
    return db.conectar()


con = conexao()
try:
    uid = db.unidade_padrao(con)
except RuntimeError as e:
    st.error(f"{e}")
    st.stop()

hoje = config.hoje()

# ---------- barra lateral ----------
with st.sidebar:
    st.title("Gestão Financeira")
    unidade = con.execute("SELECT nome FROM unidades WHERE id = ?", (uid,)).fetchone()["nome"]
    st.caption(f"Unidade: {unidade}")
    opcoes = []
    a, m = hoje.year, hoje.month
    for _ in range(12):
        opcoes.append((a, m))
        a, m = (a, m - 1) if m > 1 else (a - 1, 12)
    ano, mes = st.selectbox("Mês", opcoes, format_func=lambda x: f"{MESES[x[1] - 1]} {x[0]}")
    st.divider()
    st.caption(f"Banco: {config.DB_PATH.name}")

inicio, fim = resumos.mes_inteiro(ano, mes)
st.header(f"Visão geral · {MESES[mes - 1]} {ano}")

# ---------- pendentes ----------
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

# ---------- números do mês ----------
r = resumos.resumo_periodo(con, uid, inicio, fim)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Receitas", brl(r["entradas"]))
k2.metric("Gastos", brl(r["saidas"]))
k3.metric("Saldo", brl(r["saldo"]))
k4.metric("Lançamentos confirmados", r["qtd"])

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Gastos por categoria")
    if r["categorias"]:
        df = pd.DataFrame(r["categorias"], columns=["Categoria", "centavos"])
        df["Valor (R$)"] = df["centavos"] / 100
        st.bar_chart(df, x="Categoria", y="Valor (R$)", horizontal=True, sort="-Valor (R$)")
    else:
        st.info("Sem gastos confirmados neste mês.")
with col_b:
    st.subheader("Formas de pagamento")
    if r["contas"]:
        st.dataframe(pd.DataFrame([(n, brl(v)) for n, v in r["contas"]], columns=["Forma", "Valor"]),
                     hide_index=True, width="stretch")
    st.subheader("Acerto do casal")
    ac = resumos.acerto(con, uid, inicio, fim)
    st.dataframe(pd.DataFrame([(p["nome"], brl(p["pagou"]), brl(p["deveria"])) for p in ac["pessoas"]],
                              columns=["Pessoa", "Pagou", "Parte dele(a)"]), hide_index=True, width="stretch")
    if ac["valor"] >= 1 and ac["de"] != ac["para"]:
        st.write(f"**{ac['de']} transfere {brl(ac['valor'])} para {ac['para']}.**")
    else:
        st.write("Tudo acertado.")

st.subheader("Faturas abertas (hoje)")
fs = resumos.faturas(con, uid, hoje)
if fs:
    st.dataframe(pd.DataFrame([{
        "Cartão": f["conta"], "Valor": brl(f["total"]), "Fecha": f"{f['fechamento']:%d/%m}",
        "Vence": f"{f['vencimento']:%d/%m}" if f["vencimento"] else "", "Dias para fechar": f["dias_para_fechar"],
    } for f in fs]), hide_index=True, width="stretch")

# ---------- lançamentos ----------
st.subheader("Lançamentos do mês")
linhas = db.lancamentos_periodo(con, uid, inicio, fim, status=("confirmado", "pendente", "cancelado"))
if linhas:
    df = pd.DataFrame([{
        "ID": l["id"], "Data": f"{date.fromisoformat(l['data']):%d/%m}", "Tipo": l["tipo"],
        "Descrição": l["descricao"], "Categoria": l["categoria"], "Forma": l["conta"],
        "Quem lançou": l["autor"], "Divisão": l["regra_divisao"], "Origem": l["origem"],
        "Valor": brl(l["valor_centavos"]), "Status": l["status"],
    } for l in linhas])
    mostrar_cancelados = st.toggle("Mostrar cancelados", value=False)
    if not mostrar_cancelados:
        df = df[df["Status"] != "cancelado"]
    st.dataframe(df, hide_index=True, width="stretch")
else:
    st.info("Nenhum lançamento neste mês ainda.")

with st.expander("Novo lançamento pelo painel"):
    with st.form("novo", clear_on_submit=True):
        tipo = st.radio("Tipo", ["saida", "entrada"], horizontal=True,
                        format_func=lambda t: "Gasto" if t == "saida" else "Entrada")
        c1, c2, c3 = st.columns(3)
        valor = c1.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        data_l = c2.date_input("Data", value=hoje, format="DD/MM/YYYY")
        descricao = c3.text_input("Descrição")
        cats = [dict(c) for c in db.categorias(con, uid, tipo=tipo)]
        contas = [dict(c) for c in db.contas(con, uid)]
        pess = [dict(c) for c in db.pessoas(con, uid)]
        c4, c5, c6 = st.columns(3)
        cat = c4.selectbox("Categoria", cats, format_func=lambda c: c["nome"])
        conta = c5.selectbox("Forma de pagamento", [None] + list(contas),
                             format_func=lambda c: "—" if c is None else c["nome"])
        autor = c6.selectbox("Quem", pess, format_func=lambda p: p["nome"])
        divisao = st.selectbox("Divisão", ["(padrão da categoria)", "proporcional", "50/50", "individual"])
        if st.form_submit_button("Salvar"):
            if valor <= 0:
                st.error("Informe um valor maior que zero.")
            elif tipo == "saida" and conta is None:
                st.error("Escolha a forma de pagamento.")
            else:
                regra = cat["regra_divisao"] if divisao.startswith("(") else divisao
                db.criar_lancamento(con, unidade_id=uid, data=data_l, tipo=tipo, valor_centavos=round(valor * 100),
                                    descricao=descricao or cat["nome"], categoria_id=cat["id"],
                                    conta_id=conta["id"] if conta else None, autor_id=autor["id"],
                                    regra_divisao=regra, origem="painel", status="confirmado")
                st.success("Lançamento salvo.")
                st.rerun()

with st.expander("Cancelar um lançamento"):
    with st.form("cancelar"):
        lid = st.number_input("ID do lançamento (coluna ID da tabela)", min_value=1, step=1)
        if st.form_submit_button("Cancelar lançamento"):
            l = db.lancamento(con, int(lid))
            if l is None or l["unidade_id"] != uid:
                st.error("ID não encontrado.")
            else:
                db.atualizar_lancamento(con, int(lid), acao="cancelado", status="cancelado")
                st.success(f"Cancelado: {l['descricao']} · {brl(l['valor_centavos'])}")
                st.rerun()
