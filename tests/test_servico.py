"""Simula a conversa completa do bot, sem Telegram."""
from datetime import date

import pytest

from app import db, servico

HOJE = date(2026, 11, 5)


@pytest.fixture
def alexandre(con):
    return db.pessoa_por_telegram(con, 111)


def _dados(resp):
    return [dado for linha in resp.botoes for _, dado in linha]


def test_fluxo_lancar_e_confirmar(con, uid, alexandre):
    r = servico.processar_texto(con, uid, alexandre, "mercado 87,50 crédito picpay", HOJE, em_grupo=True)
    assert "R$ 87,50" in r.texto and "Crédito PicPay" in r.texto and "Confirma?" in r.texto
    ok = next(d for d in _dados(r) if d.startswith("ok:"))
    lid = int(ok.split(":")[1])
    assert db.lancamento(con, lid)["status"] == "pendente"

    r2 = servico.processar_callback(con, uid, alexandre, ok, HOJE)
    assert r2.editar and "Registrado" in r2.texto and "Fatura Crédito PicPay: R$ 87,50" in r2.texto
    assert db.lancamento(con, lid)["status"] == "confirmado"


def test_conversa_sem_valor_no_grupo_e_ignorada(con, uid, alexandre):
    assert servico.processar_texto(con, uid, alexandre, "chego às oito", HOJE, em_grupo=True) is None
    assert "Não achei o valor" in servico.processar_texto(con, uid, alexandre, "oi", HOJE, em_grupo=False).texto


def test_sem_forma_pergunta_e_completa(con, uid, alexandre):
    r = servico.processar_texto(con, uid, alexandre, "mercado 40 crédito", HOJE, em_grupo=False)
    assert "Qual cartão?" in r.texto
    escolhas = [d for d in _dados(r) if d.startswith("scon:")]
    assert len(escolhas) == 4  # só cartões de crédito
    r2 = servico.processar_callback(con, uid, alexandre, escolhas[0], HOJE)
    assert "Confirma?" in r2.texto


def test_corrigir_categoria(con, uid, alexandre):
    r = servico.processar_texto(con, uid, alexandre, "presente 80 pix", HOJE, em_grupo=False)
    assert "Não reconheci a categoria" in r.texto
    lid = int(_dados(r)[0].split(":")[1])
    r2 = servico.processar_callback(con, uid, alexandre, f"fcat:{lid}", HOJE)
    lazer = next(d for linha in r2.botoes for rot, d in linha if rot == "Lazer")
    servico.processar_callback(con, uid, alexandre, lazer, HOJE)
    assert db.lancamento(con, lid)["categoria"] == "Lazer"
    acoes = [x["acao"] for x in con.execute("SELECT acao FROM historico WHERE lancamento_id = ?", (lid,))]
    assert acoes == ["criado", "editado"]


def test_desfazer_ultimo(con, uid, alexandre):
    r = servico.processar_texto(con, uid, alexandre, "uber 23 pix", HOJE, em_grupo=False)
    servico.processar_callback(con, uid, alexandre, _dados(r)[0], HOJE)
    r2 = servico.processar_texto(con, uid, alexandre, servico.BOTAO_DESFAZER, HOJE, em_grupo=False)
    desf = next(d for d in _dados(r2) if d.startswith("desf:"))
    r3 = servico.processar_callback(con, uid, alexandre, desf, HOJE)
    assert "Desfeito" in r3.texto
    assert db.lancamento(con, int(desf.split(":")[1]))["status"] == "cancelado"


def test_menu_resumos(con, uid, alexandre):
    r = servico.processar_texto(con, uid, alexandre, servico.BOTAO_RESUMOS, HOJE, em_grupo=False)
    assert set(_dados(r)) == {"res:hoje", "res:semana", "res:mes", "res:fat", "res:acerto", "res:metas"}
    for dado in _dados(r):
        texto = servico.processar_callback(con, uid, alexandre, dado, HOJE).texto
        assert texto


def test_descricao_com_html_e_escapada(con, uid, alexandre):
    r = servico.processar_texto(con, uid, alexandre, "<b>teste</b> 10 pix", HOJE, em_grupo=False)
    assert "<b>teste</b>" not in r.texto and "&lt;b&gt;" in r.texto
