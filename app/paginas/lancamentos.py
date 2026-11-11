"""Página Lançamentos: lançamento rápido por texto, formulário completo e edição."""
import hashlib
from datetime import date

import pandas as pd
import streamlit as st

from app import db, resumos
from app.paginas.comum import (NOME_DIVISAO, NOME_TIPO, Contexto, avisar, campos_lancamento, ler_campos,
                               mostrar_aviso, validar)
from app.parser import interpretar
from app.resumos import brl
from app.servico import MESES


def _salvar_novo(con, uid, pessoa, prefixo, origem_texto=None, limpar=None):
    campos = ler_campos(prefixo)
    erro = validar(campos)
    if erro:
        avisar("erro", erro)
        return
    cat = con.execute("SELECT nome FROM categorias WHERE id = ?", (campos["categoria_id"],)).fetchone()
    db.criar_lancamento(con, unidade_id=uid, autor_id=pessoa["id"] if pessoa else None, origem="painel",
                        mensagem_origem=origem_texto, status="confirmado",
                        **{**campos, "descricao": campos["descricao"] or cat["nome"]})
    avisar("ok", f"Salvo: {campos['descricao'] or cat['nome']} · {brl(campos['valor_centavos'])}")
    for chave in limpar or []:
        st.session_state[chave] = ""


def _salvar_edicao(con, lid, pessoa, prefixo):
    campos = ler_campos(prefixo)
    erro = validar(campos)
    if erro:
        avisar("erro", erro)
        return
    db.atualizar_lancamento(con, lid, pessoa["id"] if pessoa else None, **campos)
    avisar("ok", "Alterações salvas.")


def _cancelar(con, lid, pessoa):
    db.atualizar_lancamento(con, lid, pessoa["id"] if pessoa else None, acao="cancelado", status="cancelado")
    avisar("ok", "Lançamento cancelado. Ele continua no histórico, mas sai dos totais.")


def _reativar(con, lid, pessoa):
    db.atualizar_lancamento(con, lid, pessoa["id"] if pessoa else None, acao="reativado", status="confirmado")
    avisar("ok", "Lançamento reativado.")


def render(ctx: Contexto):
    con, uid, pessoa = ctx.con, ctx.uid, ctx.pessoa
    st.header("Lançamentos")
    mostrar_aviso()
    if pessoa is None:
        st.warning("Cadastre ao menos uma pessoa em Configurações.")
        return

    # ---------- lançamento rápido ----------
    st.subheader("Lançamento rápido")
    st.caption("Escreva numa linha só, como num chat: `mercado 87,50 crédito picpay` · "
               "`farmácia 42,90 pix ontem` · `gasolina 180 cartão conjunto` · `recebi salário 5.200`")
    texto = st.text_input("O que foi gasto ou recebido?", key="rapido_texto",
                          placeholder="mercado 87,50 crédito picpay")
    if texto.strip():
        r = interpretar(texto, ctx.hoje, db.contas(con, uid), db.categorias(con, uid))
        if r.valor_centavos is None:
            st.warning("Não achei o valor. Escreva o número, por exemplo `mercado 87,50 pix`.")
        else:
            st.caption("Confira o que foi entendido e ajuste se precisar:")
            prefixo = "rap_" + hashlib.md5(texto.encode()).hexdigest()[:8] + "_"
            campos_lancamento(con, uid, prefixo, {
                "tipo": r.tipo, "valor": r.valor_centavos / 100, "data": r.data,
                "categoria_id": r.categoria["id"] if r.categoria else None,
                "conta_id": r.conta["id"] if r.conta else None,
                "regra_divisao": r.regra_divisao, "descricao": r.descricao,
            })
            avisos = []
            if r.tipo == "saida" and r.conta is None:
                avisos.append("não reconheci a forma de pagamento")
            if r.categoria_incerta:
                avisos.append("não reconheci a categoria")
            if avisos:
                st.info("Atenção: " + " e ".join(avisos) + ". Escolha acima. Para o aplicativo aprender a palavra, "
                        "acrescente-a nos apelidos em Configurações.")
            st.button("Salvar lançamento", type="primary", key="salvar_rapido", on_click=_salvar_novo,
                      args=(con, uid, pessoa, prefixo, texto, ["rapido_texto"]))

    # ---------- formulário completo ----------
    with st.expander("Formulário completo (sem digitar a frase)"):
        n = st.session_state.get("_form_n", 0)
        prefixo = f"form{n}_"
        campos_lancamento(con, uid, prefixo, {"data": ctx.hoje})

        def _salvar_form():
            _salvar_novo(con, uid, pessoa, prefixo)
            if st.session_state.get("_aviso", ("",))[0] == "ok":
                st.session_state["_form_n"] = n + 1  # zera o formulário

        st.button("Salvar", key=f"salvar_form{n}", on_click=_salvar_form)

    # ---------- lista do mês ----------
    st.subheader(f"Lançamentos de {MESES[ctx.mes - 1].lower()} de {ctx.ano}")
    inicio, fim = resumos.mes_inteiro(ctx.ano, ctx.mes)
    mostrar_cancelados = st.toggle("Mostrar cancelados", value=False)
    status = ("confirmado", "pendente", "cancelado") if mostrar_cancelados else ("confirmado", "pendente")
    linhas = db.lancamentos_periodo(con, uid, inicio, fim, status=status)
    if not linhas:
        st.caption("Nenhum lançamento neste mês.")
        return

    df = pd.DataFrame([{
        "ID": l["id"], "Data": f"{date.fromisoformat(l['data']):%d/%m}", "Tipo": NOME_TIPO[l["tipo"]],
        "Descrição": l["descricao"], "Categoria": l["categoria"], "Forma": l["conta"] or "",
        "Valor": brl(l["valor_centavos"]), "Divisão": NOME_DIVISAO.get(l["regra_divisao"], l["regra_divisao"]),
        "Quem lançou": l["autor"] or "", "Status": l["status"],
    } for l in linhas])
    st.caption("Clique numa linha para editar ou cancelar.")
    evento = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun",
                          selection_mode="single-row", key="tabela_lancamentos",
                          column_config={"ID": st.column_config.NumberColumn(width="small")})
    selecionadas = evento.selection.rows if evento and evento.selection else []
    if not selecionadas:
        return

    lid = int(df.iloc[selecionadas[0]]["ID"])
    l = db.lancamento(con, lid)
    with st.container(border=True):
        st.markdown(f"**Editando:** {l['descricao']} · {brl(l['valor_centavos'])} "
                    f"({'cancelado' if l['status'] == 'cancelado' else l['status']})")
        prefixo = f"ed{lid}_{l['atualizado_em']}_"
        campos_lancamento(con, uid, prefixo, {
            "tipo": l["tipo"], "valor": l["valor_centavos"] / 100, "data": date.fromisoformat(l["data"]),
            "categoria_id": l["categoria_id"], "conta_id": l["conta_id"],
            "regra_divisao": l["regra_divisao"], "descricao": l["descricao"],
        })
        if l["mensagem_origem"]:
            st.caption(f"Texto original: “{l['mensagem_origem']}”")
        c1, c2, _ = st.columns([1, 1, 3])
        c1.button("Salvar alterações", type="primary", key=f"salvar_ed{lid}", on_click=_salvar_edicao,
                  args=(con, lid, pessoa, prefixo))
        if l["status"] == "cancelado":
            c2.button("Reativar", key=f"reativar{lid}", on_click=_reativar, args=(con, lid, pessoa))
        else:
            c2.button("Cancelar lançamento", key=f"cancelar{lid}", on_click=_cancelar, args=(con, lid, pessoa))
