"""Página Configurações: pessoas, formas de pagamento, categorias e backup."""
import pandas as pd
import streamlit as st

from app import backup, config, db
from app.paginas.comum import Contexto, mostrar_aviso, registros

TIPOS_CONTA = ["credito", "debito", "pix", "vale", "dinheiro"]
NOMES_TIPO_CONTA = {"credito": "Crédito", "debito": "Débito", "pix": "Pix", "vale": "Vale", "dinheiro": "Dinheiro"}


def _versao(nome):
    return st.session_state.get(f"_v_{nome}", 0)


def _nova_versao(nome):
    st.session_state[f"_v_{nome}"] = _versao(nome) + 1


def _salvar(nome, funcao, con, uid, original_ids, editado):
    linhas = registros(editado)
    ids_atuais = {l["id"] for l in linhas if l.get("id")}
    try:
        funcao(con, uid, linhas)
        removidos = original_ids - ids_atuais
        if removidos:
            tabela = {"pessoas": "pessoas", "contas": "contas", "categorias": "categorias"}[nome]
            with db.transacao(con):
                con.executemany(f"UPDATE {tabela} SET ativo = 0 WHERE id = ? AND unidade_id = ?",
                                [(i, uid) for i in removidos])
        _nova_versao(nome)
        st.session_state["_aviso"] = ("ok", "Configurações salvas.")
        st.rerun()
    except ValueError as e:
        st.error(str(e))


def render(ctx: Contexto):
    con, uid = ctx.con, ctx.uid
    st.header("Configurações")
    mostrar_aviso()
    st.caption("Edite direto nas tabelas e clique em Salvar. Para tirar um item sem perder o histórico, "
               "desmarque **Ativo**. Linhas apagadas também ficam apenas inativas.")

    # ---------- pessoas ----------
    st.subheader("Pessoas")
    st.caption("Peso: a parte de cada um nos custos divididos proporcionalmente (ex.: 0,58 e 0,42).")
    pess = db.pessoas(con, uid, incluir_inativos=True)
    df = pd.DataFrame([{"id": p["id"], "nome": p["nome"], "peso_divisao": p["peso_divisao"],
                        "telegram_id": p["telegram_id"], "ativo": bool(p["ativo"])} for p in pess],
                      columns=["id", "nome", "peso_divisao", "telegram_id", "ativo"])
    ed = st.data_editor(df, key=f"ed_pessoas_{_versao('pessoas')}", num_rows="dynamic", hide_index=True,
                        width="stretch", column_config={
                            "id": None,
                            "nome": st.column_config.TextColumn("Nome", required=True),
                            "peso_divisao": st.column_config.NumberColumn("Peso na divisão", min_value=0.0,
                                                                          max_value=1.0, step=0.01, format="%.2f"),
                            "telegram_id": st.column_config.NumberColumn("ID do Telegram (só para o bot)",
                                                                         format="%d"),
                            "ativo": st.column_config.CheckboxColumn("Ativo", default=True),
                        })
    if st.button("Salvar pessoas"):
        _salvar("pessoas", db.salvar_pessoas, con, uid, {p["id"] for p in pess}, ed)

    # ---------- contas ----------
    st.subheader("Formas de pagamento e cartões")
    st.caption("Titular: quem paga essa conta (vazio = conjunta, ou quem lançou no caso de Pix/Débito). "
               "Dias de fechamento e vencimento só para cartão de crédito. "
               "Apelidos: palavras que o lançamento rápido reconhece, separadas por vírgula, sem acento.")
    nomes_pessoas = [p["nome"] for p in pess]
    contas = db.contas(con, uid, incluir_inativos=True)
    titular = {p["id"]: p["nome"] for p in pess}
    df = pd.DataFrame([{"id": c["id"], "nome": c["nome"], "tipo": c["tipo"],
                        "titular": titular.get(c["titular_id"], ""), "dia_fechamento": c["dia_fechamento"],
                        "dia_vencimento": c["dia_vencimento"], "apelidos": db.apelidos_para_texto(c["apelidos"]),
                        "ativo": bool(c["ativo"])} for c in contas],
                      columns=["id", "nome", "tipo", "titular", "dia_fechamento", "dia_vencimento", "apelidos", "ativo"])
    ed = st.data_editor(df, key=f"ed_contas_{_versao('contas')}", num_rows="dynamic", hide_index=True,
                        width="stretch", column_config={
                            "id": None,
                            "nome": st.column_config.TextColumn("Nome", required=True),
                            "tipo": st.column_config.SelectboxColumn("Tipo", options=TIPOS_CONTA, required=True,
                                                                     default="pix"),
                            "titular": st.column_config.SelectboxColumn("Titular", options=[""] + nomes_pessoas),
                            "dia_fechamento": st.column_config.NumberColumn("Fecha dia", min_value=1, max_value=31,
                                                                            step=1, format="%d"),
                            "dia_vencimento": st.column_config.NumberColumn("Vence dia", min_value=1, max_value=31,
                                                                            step=1, format="%d"),
                            "apelidos": st.column_config.TextColumn("Apelidos", width="large"),
                            "ativo": st.column_config.CheckboxColumn("Ativo", default=True),
                        })
    if st.button("Salvar formas de pagamento"):
        _salvar("contas", db.salvar_contas, con, uid, {c["id"] for c in contas}, ed)

    # ---------- categorias ----------
    st.subheader("Categorias")
    st.caption("Divisão padrão: proporcional à renda, 50/50 ou individual (só de quem lançou).")
    cats = db.categorias(con, uid, incluir_inativos=True)
    df = pd.DataFrame([{"id": c["id"], "nome": c["nome"], "tipo": c["tipo"], "regra_divisao": c["regra_divisao"],
                        "apelidos": db.apelidos_para_texto(c["apelidos"]), "ativo": bool(c["ativo"])} for c in cats],
                      columns=["id", "nome", "tipo", "regra_divisao", "apelidos", "ativo"])
    ed = st.data_editor(df, key=f"ed_categorias_{_versao('categorias')}", num_rows="dynamic", hide_index=True,
                        width="stretch", column_config={
                            "id": None,
                            "nome": st.column_config.TextColumn("Nome", required=True),
                            "tipo": st.column_config.SelectboxColumn("Tipo", options=["saida", "entrada"],
                                                                     required=True, default="saida"),
                            "regra_divisao": st.column_config.SelectboxColumn(
                                "Divisão", options=["proporcional", "50/50", "individual"], required=True,
                                default="proporcional"),
                            "apelidos": st.column_config.TextColumn("Apelidos", width="large"),
                            "ativo": st.column_config.CheckboxColumn("Ativo", default=True),
                        })
    if st.button("Salvar categorias"):
        _salvar("categorias", db.salvar_categorias, con, uid, {c["id"] for c in cats}, ed)

    # ---------- backup ----------
    st.subheader("Seus dados e backup")
    st.write(f"Todos os dados ficam num único arquivo neste computador: `{config.DB_PATH}`. "
             "Fechar o navegador não apaga nada.")
    c1, c2 = st.columns(2)
    if c1.button("Fazer backup agora"):
        destino = backup.main()
        c1.success(f"Backup salvo em `{destino}`")
    c2.download_button("Baixar cópia do banco", data=config.DB_PATH.read_bytes(),
                       file_name=f"financas-{ctx.hoje:%Y-%m-%d}.db", mime="application/octet-stream")
    st.caption("Guarde a cópia num pen drive ou na nuvem de vez em quando. "
               "Para restaurar, feche o aplicativo e coloque a cópia no lugar de dados\\financas.db.")
