from datetime import date

from app import db, resumos


def _lanc(con, uid, conta, categoria, valor, autor, data=date(2026, 11, 3), tipo="saida", status="confirmado"):
    contas = {c["nome"]: c for c in db.contas(con, uid)}
    cats = {c["nome"]: c for c in db.categorias(con, uid)}
    pess = {p["nome"]: p["id"] for p in db.pessoas(con, uid)}
    return db.criar_lancamento(
        con, unidade_id=uid, data=data, tipo=tipo, valor_centavos=valor, descricao=categoria,
        categoria_id=cats[categoria]["id"], conta_id=contas[conta]["id"] if conta else None,
        autor_id=pess[autor], regra_divisao=cats[categoria]["regra_divisao"], status=status)


def test_brl():
    assert resumos.brl(123456) == "R$ 1.234,56"
    assert resumos.brl(5) == "R$ 0,05"
    assert resumos.brl(-2000) == "-R$ 20,00"


def test_resumo_mes_ignora_pendentes_e_cancelados(con, uid):
    _lanc(con, uid, None, "Salário", 500000, "Alexandre", tipo="entrada")
    _lanc(con, uid, "Pix", "Mercado", 10000, "Alexandre")
    _lanc(con, uid, "Pix", "Mercado", 2000, "Parceira", status="pendente")
    _lanc(con, uid, "Pix", "Lazer", 9900, "Parceira", status="cancelado")
    r = resumos.resumo_periodo(con, uid, date(2026, 11, 1), date(2026, 11, 30))
    assert r["entradas"] == 500000
    assert r["saidas"] == 10000
    assert r["saldo"] == 490000
    assert r["pendentes"] == 1
    assert r["categorias"] == [("Mercado", 10000)]


def test_ciclo_fatura():
    assert resumos.ciclo_fatura(12, date(2026, 11, 5)) == (date(2026, 10, 12), date(2026, 11, 12))
    assert resumos.ciclo_fatura(12, date(2026, 11, 12)) == (date(2026, 11, 12), date(2026, 12, 12))
    assert resumos.ciclo_fatura(31, date(2026, 2, 10)) == (date(2026, 1, 31), date(2026, 2, 28))


def test_faturas(con, uid):
    _lanc(con, uid, "Crédito PicPay", "Mercado", 8750, "Alexandre", data=date(2026, 11, 5))
    _lanc(con, uid, "Crédito PicPay", "Mercado", 1000, "Alexandre", data=date(2026, 10, 1))  # fatura anterior
    fs = {f["conta"]: f for f in resumos.faturas(con, uid, date(2026, 11, 5))}
    assert fs["Crédito PicPay"]["total"] == 8750
    assert fs["Crédito PicPay"]["fechamento"] == date(2026, 11, 12)
    assert fs["Crédito PicPay"]["vencimento"] == date(2026, 11, 19)
    assert fs["Crédito PicPay"]["dias_para_fechar"] == 7


def test_acerto_proporcional_e_50_50(con, uid):
    # Alexandre paga R$ 1.000 de mercado (proporcional 58/42): Parceira deve 420
    _lanc(con, uid, "Pix", "Mercado", 100000, "Alexandre")
    # Parceira paga R$ 200 de gasolina no cartão dela (50/50): Alexandre deve 100
    _lanc(con, uid, "Crédito Parceira", "Carro", 20000, "Parceira")
    # cartão conjunto e gasto individual não entram
    _lanc(con, uid, "Crédito Conjunto", "Mercado", 50000, "Alexandre")
    _lanc(con, uid, "Débito", "Pessoal", 30000, "Parceira")
    a = resumos.acerto(con, uid, date(2026, 11, 1), date(2026, 11, 30))
    assert a["de"] == "Parceira"
    assert a["para"] == "Alexandre"
    assert a["valor"] == 42000 - 10000


def test_historico_registra_alteracoes(con, uid):
    lid = _lanc(con, uid, "Pix", "Mercado", 1000, "Alexandre", status="pendente")
    db.atualizar_lancamento(con, lid, acao="confirmado", status="confirmado")
    acoes = [r["acao"] for r in con.execute("SELECT acao FROM historico WHERE lancamento_id = ?", (lid,))]
    assert acoes == ["criado", "confirmado"]
