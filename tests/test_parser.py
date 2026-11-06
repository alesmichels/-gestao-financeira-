from datetime import date

import pytest

from app import db
from app.parser import interpretar

HOJE = date(2026, 11, 5)


@pytest.fixture
def ler(con, uid):
    contas = db.contas(con, uid)
    cats = db.categorias(con, uid)
    return lambda texto: interpretar(texto, HOJE, contas, cats)


def test_exemplo_basico(ler):
    r = ler("mercado 87,50 crédito picpay")
    assert r.tipo == "saida"
    assert r.valor_centavos == 8750
    assert r.conta["nome"] == "Crédito PicPay"
    assert r.categoria["nome"] == "Mercado"
    assert r.descricao == "Mercado"
    assert r.regra_divisao == "proporcional"
    assert r.data == HOJE
    assert r.faltando == []


@pytest.mark.parametrize("texto,centavos", [
    ("farmácia 42,90 pix", 4290),
    ("aluguel 1.850,00 pix", 185000),
    ("aluguel 1.850 pix", 185000),
    ("lanche 12.5 pix", 1250),
    ("lanche R$12 pix", 1200),
    ("uber 23 pix", 2300),
])
def test_valores(ler, texto, centavos):
    assert ler(texto).valor_centavos == centavos


def test_data_relativa_e_explicita(ler):
    assert ler("farmácia 42,90 pix ontem").data == date(2026, 11, 4)
    assert ler("almoço 36 vale 03/11").data == date(2026, 11, 3)
    assert ler("presente 50 pix 20/12").data == date(2025, 12, 20)  # data futura sem ano = ano passado


def test_carro_divide_50_50(ler):
    r = ler("gasolina 180 cartão conjunto")
    assert r.categoria["nome"] == "Carro"
    assert r.regra_divisao == "50/50"
    assert r.conta["nome"] == "Crédito Conjunto"


def test_divisao_explicita(ler):
    assert ler("roupa 120 débito só meu").regra_divisao == "individual"
    assert ler("mercado 100 pix 50/50").regra_divisao == "50/50"
    assert ler("mercado 100 pix 50/50").valor_centavos == 10000


def test_sem_valor(ler):
    assert "valor" in ler("mercado pix").faltando


def test_sem_forma_de_pagamento(ler):
    r = ler("mercado 40")
    assert "forma de pagamento" in r.faltando
    assert not r.cartao_ambiguo


def test_cartao_sem_nome(ler):
    r = ler("mercado 40 crédito")
    assert r.cartao_ambiguo
    assert "forma de pagamento" in r.faltando
    assert r.descricao == "Mercado"


def test_categoria_desconhecida_vira_outros(ler):
    r = ler("presente aniversário 80 pix")
    assert r.categoria["nome"] == "Outros"
    assert r.categoria_incerta
    assert r.descricao == "Presente aniversário"


def test_entrada_salario(ler):
    r = ler("recebi salário 5.200,00")
    assert r.tipo == "entrada"
    assert r.valor_centavos == 520000
    assert r.categoria["nome"] == "Salário"
    assert r.faltando == []


def test_entrada_vale_vai_para_dia_1(ler):
    r = ler("vale caiu 640")
    assert r.tipo == "entrada"
    assert r.categoria["nome"] == "Vale recebido"
    assert r.data == date(2026, 11, 1)


def test_gasto_no_vale_e_saida(ler):
    r = ler("almoço 36 vale")
    assert r.tipo == "saida"
    assert r.conta["nome"] == "Vale"
    assert r.categoria["nome"] == "Alimentação fora"
