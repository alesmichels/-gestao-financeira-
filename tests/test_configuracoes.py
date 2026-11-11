import pytest

from app import db
from app.cadastros import garantir_cadastros


def test_primeira_execucao_cria_cadastros(tmp_path):
    con = db.conectar(tmp_path / "novo.db")
    uid = garantir_cadastros(con)
    assert [p["nome"] for p in db.pessoas(con, uid)] == ["Alexandre", "Parceira"]
    assert len(db.contas(con, uid)) == 8
    assert garantir_cadastros(con) == uid  # segunda vez não duplica
    assert len(db.contas(con, uid)) == 8


def test_salvar_pessoas_renomeia_e_adiciona(con, uid):
    linhas = [dict(p) for p in db.pessoas(con, uid)]
    linhas[1]["nome"] = "Bruna"
    linhas.append({"id": None, "nome": "Pai", "peso_divisao": 0, "telegram_id": None, "ativo": True})
    db.salvar_pessoas(con, uid, linhas)
    assert [p["nome"] for p in db.pessoas(con, uid)] == ["Alexandre", "Bruna", "Pai"]


def test_salvar_pessoas_rejeita_nome_repetido(con, uid):
    linhas = [dict(p) for p in db.pessoas(con, uid)]
    linhas[1]["nome"] = "Alexandre"
    with pytest.raises(ValueError, match="repetidos"):
        db.salvar_pessoas(con, uid, linhas)


def test_salvar_contas_com_titular_e_apelidos(con, uid):
    linhas = [{"id": c["id"], "nome": c["nome"], "tipo": c["tipo"], "titular": None,
               "dia_fechamento": c["dia_fechamento"], "dia_vencimento": c["dia_vencimento"],
               "apelidos": db.apelidos_para_texto(c["apelidos"]), "ativo": True}
              for c in db.contas(con, uid)]
    linhas.append({"id": None, "nome": "Crédito Nubank", "tipo": "credito", "titular": "Parceira",
                   "dia_fechamento": 3, "dia_vencimento": 10, "apelidos": "nubank, roxinho", "ativo": True})
    db.salvar_contas(con, uid, linhas)
    nova = next(c for c in db.contas(con, uid) if c["nome"] == "Crédito Nubank")
    assert db.apelidos_para_texto(nova["apelidos"]) == "nubank, roxinho"
    parceira = next(p for p in db.pessoas(con, uid) if p["nome"] == "Parceira")
    assert nova["titular_id"] == parceira["id"]


def test_salvar_contas_valida_dia(con, uid):
    with pytest.raises(ValueError, match="Dia inválido"):
        db.salvar_contas(con, uid, [{"id": None, "nome": "X", "tipo": "credito", "dia_fechamento": 40}])


def test_categoria_inativa_some_das_opcoes(con, uid):
    linhas = [{"id": c["id"], "nome": c["nome"], "tipo": c["tipo"], "regra_divisao": c["regra_divisao"],
               "apelidos": db.apelidos_para_texto(c["apelidos"]), "ativo": c["nome"] != "Lazer"}
              for c in db.categorias(con, uid, incluir_inativos=True)]
    db.salvar_categorias(con, uid, linhas)
    assert "Lazer" not in [c["nome"] for c in db.categorias(con, uid)]
    assert "Lazer" in [c["nome"] for c in db.categorias(con, uid, incluir_inativos=True)]
