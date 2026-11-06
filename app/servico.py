"""Regras da conversa do bot, sem depender do Telegram.

Cada função recebe o que chegou e devolve uma `Resposta` (texto + botões).
O arquivo bot.py só traduz isso para a API do Telegram. Assim dá para testar
toda a conversa sem internet.
"""
from dataclasses import dataclass, field
from datetime import date

from app import db, resumos
from app.parser import interpretar
from app.resumos import brl, esc

BOTAO_RESUMOS = "Resumos"
BOTAO_LANCAR = "Lançar"
BOTAO_DESFAZER = "Desfazer último"
TECLADO_FIXO = [[BOTAO_RESUMOS, BOTAO_LANCAR, BOTAO_DESFAZER]]

DIVISOES = {"p": "proporcional", "m": "50/50", "i": "individual"}
NOME_DIVISAO = {"proporcional": "divisão proporcional", "50/50": "divisão 50/50", "individual": "só de quem lançou"}

AJUDA = (
    "Para lançar, escreva o gasto numa linha, por exemplo:\n"
    "• <code>mercado 87,50 crédito picpay</code>\n"
    "• <code>farmácia 42,90 pix ontem</code>\n"
    "• <code>gasolina 180 cartão conjunto</code>\n"
    "• <code>roupa 120 débito só meu</code>\n"
    "• <code>recebi salário 5.200</code>\n\n"
    "Eu mostro o que entendi e você confirma ou corrige."
)


@dataclass
class Resposta:
    texto: str
    botoes: list = field(default_factory=list)  # linhas de (rótulo, dado_callback)
    editar: bool = False  # True: substitui a mensagem com os botões; False: nova mensagem


# ---------- mensagens de texto ----------

def processar_texto(con, uid, pessoa, texto: str, hoje: date, em_grupo: bool) -> Resposta | None:
    texto = (texto or "").strip()
    if texto == BOTAO_RESUMOS:
        return menu_resumos()
    if texto == BOTAO_LANCAR:
        return Resposta(AJUDA)
    if texto == BOTAO_DESFAZER:
        return pedir_desfazer(con, pessoa)

    r = interpretar(texto, hoje, db.contas(con, uid), db.categorias(con, uid))
    if r.valor_centavos is None:
        # no grupo, conversa normal sem valor é ignorada
        return None if em_grupo else Resposta("Não achei o valor nessa mensagem.\n\n" + AJUDA)

    lid = db.criar_lancamento(
        con, unidade_id=uid, data=r.data, tipo=r.tipo, valor_centavos=r.valor_centavos,
        descricao=r.descricao, categoria_id=r.categoria["id"] if r.categoria else None,
        conta_id=r.conta["id"] if r.conta else None, autor_id=pessoa["id"],
        regra_divisao=r.regra_divisao, origem="telegram", mensagem_origem=texto)

    if r.tipo == "saida" and r.conta is None:
        pergunta = "Qual cartão?" if r.cartao_ambiguo else "Como foi pago?"
        contas = [c for c in db.contas(con, uid) if not r.cartao_ambiguo or c["tipo"] == "credito"]
        return Resposta(
            cartao(con, lid, aviso=pergunta, confirmar=False),
            _grade([(c["nome"], f"scon:{lid}:{c['id']}") for c in contas]) + [[("Cancelar", f"cx:{lid}")]])

    aviso = "Não reconheci a categoria; use Corrigir se quiser mudar." if r.categoria_incerta else None
    return Resposta(cartao(con, lid, aviso=aviso), botoes_confirmacao(lid))


# ---------- botões (callbacks) ----------

def processar_callback(con, uid, pessoa, dado: str, hoje: date) -> Resposta:
    partes = dado.split(":")
    acao = partes[0]

    if acao == "res":
        return resumo(con, uid, partes[1], hoje)

    lid = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else None
    l = db.lancamento(con, lid) if lid else None
    if lid and (l is None or l["unidade_id"] != uid):
        return Resposta("Lançamento não encontrado.", editar=True)

    if acao == "ok":
        if l["status"] == "cancelado":
            return Resposta("Esse lançamento já tinha sido cancelado.", editar=True)
        if l["tipo"] == "saida" and l["conta_id"] is None:
            return Resposta(cartao(con, lid, aviso="Falta a forma de pagamento.", confirmar=False),
                            _grade([(c["nome"], f"scon:{lid}:{c['id']}") for c in db.contas(con, uid)]),
                            editar=True)
        db.atualizar_lancamento(con, lid, pessoa["id"], acao="confirmado", status="confirmado")
        return Resposta(texto_registrado(con, uid, lid, hoje), editar=True)

    if acao == "cx":
        db.atualizar_lancamento(con, lid, pessoa["id"], acao="cancelado", status="cancelado")
        return Resposta(f"Cancelado: {esc(l['descricao'])} · {brl(l['valor_centavos'])}", editar=True)

    if acao == "fix":
        return Resposta(cartao(con, lid, aviso="O que você quer corrigir?", confirmar=False), [
            [("Categoria", f"fcat:{lid}"), ("Forma de pagamento", f"fcon:{lid}")],
            [("Data", f"fdat:{lid}"), ("Divisão", f"fdiv:{lid}")],
            [("Valor ou descrição", f"fval:{lid}")],
            [("Voltar", f"ver:{lid}")],
        ], editar=True)

    if acao == "ver":
        return Resposta(cartao(con, lid), botoes_confirmacao(lid), editar=True)

    if acao == "fcat":
        cats = db.categorias(con, uid, tipo=l["tipo"])
        return Resposta(cartao(con, lid, aviso="Escolha a categoria:", confirmar=False),
                        _grade([(c["nome"], f"scat:{lid}:{c['id']}") for c in cats]), editar=True)

    if acao == "fcon":
        return Resposta(cartao(con, lid, aviso="Escolha a forma de pagamento:", confirmar=False),
                        _grade([(c["nome"], f"scon:{lid}:{c['id']}") for c in db.contas(con, uid)]), editar=True)

    if acao == "fdiv":
        return Resposta(cartao(con, lid, aviso="Como dividir?", confirmar=False), [
            [("Proporcional à renda", f"sdiv:{lid}:p")], [("50/50", f"sdiv:{lid}:m")],
            [("Só de quem lançou", f"sdiv:{lid}:i")]], editar=True)

    if acao == "fdat":
        from datetime import timedelta
        opcoes = [("Hoje", hoje), ("Ontem", hoje - timedelta(days=1)), ("Anteontem", hoje - timedelta(days=2))]
        return Resposta(cartao(con, lid, aviso="Qual a data? (para outra data, cancele e mande com dd/mm)",
                               confirmar=False),
                        [[(n, f"sdat:{lid}:{d.isoformat()}") for n, d in opcoes]], editar=True)

    if acao == "fval":
        db.atualizar_lancamento(con, lid, pessoa["id"], acao="cancelado", status="cancelado")
        return Resposta("Cancelei esse lançamento. Mande a mensagem de novo com o valor ou a descrição certa.",
                        editar=True)

    if acao == "scat":
        cat = con.execute("SELECT * FROM categorias WHERE id = ? AND unidade_id = ?",
                          (int(partes[2]), uid)).fetchone()
        db.atualizar_lancamento(con, lid, pessoa["id"], categoria_id=cat["id"], regra_divisao=cat["regra_divisao"])
        return Resposta(cartao(con, lid), botoes_confirmacao(lid), editar=True)

    if acao == "scon":
        conta = con.execute("SELECT * FROM contas WHERE id = ? AND unidade_id = ?",
                            (int(partes[2]), uid)).fetchone()
        db.atualizar_lancamento(con, lid, pessoa["id"], conta_id=conta["id"])
        return Resposta(cartao(con, lid), botoes_confirmacao(lid), editar=True)

    if acao == "sdiv":
        db.atualizar_lancamento(con, lid, pessoa["id"], regra_divisao=DIVISOES[partes[2]])
        return Resposta(cartao(con, lid), botoes_confirmacao(lid), editar=True)

    if acao == "sdat":
        db.atualizar_lancamento(con, lid, pessoa["id"], data=date.fromisoformat(partes[2]))
        return Resposta(cartao(con, lid), botoes_confirmacao(lid), editar=True)

    if acao == "desf":
        db.atualizar_lancamento(con, lid, pessoa["id"], acao="desfeito", status="cancelado")
        return Resposta(f"Desfeito: {esc(l['descricao'])} · {brl(l['valor_centavos'])}", editar=True)

    if acao == "manter":
        return Resposta("Ok, mantido.", editar=True)

    return Resposta("Não entendi esse botão.", editar=True)


# ---------- textos ----------

def cartao(con, lid, aviso=None, confirmar=True) -> str:
    l = db.lancamento(con, lid)
    tipo = "Entrada" if l["tipo"] == "entrada" else "Gasto"
    linhas = [f"{tipo}: <b>{brl(l['valor_centavos'])}</b> · {esc(l['categoria'] or 'sem categoria')}"]
    detalhe = []
    if l["tipo"] == "saida":
        detalhe.append(esc(l["conta"]) if l["conta"] else "forma de pagamento?")
    detalhe.append(date.fromisoformat(l["data"]).strftime("%d/%m"))
    if l["tipo"] == "saida":
        detalhe.append(NOME_DIVISAO.get(l["regra_divisao"], l["regra_divisao"]))
    linhas.append(" · ".join(detalhe))
    if l["descricao"] and l["descricao"] != l["categoria"]:
        linhas.append(f"“{esc(l['descricao'])}”")
    if l["autor"]:
        linhas.append(f"Lançado por {esc(l['autor'])}")
    if aviso:
        linhas.append(f"\n{esc(aviso)}")
    elif confirmar:
        linhas.append("\nConfirma?")
    return "\n".join(linhas)


def botoes_confirmacao(lid):
    return [[("Confirmar", f"ok:{lid}"), ("Corrigir", f"fix:{lid}"), ("Cancelar", f"cx:{lid}")]]


def texto_registrado(con, uid, lid, hoje) -> str:
    l = db.lancamento(con, lid)
    texto = f"Registrado: <b>{brl(l['valor_centavos'])}</b> · {esc(l['categoria'] or '')}"
    if l["conta_tipo"] == "credito":
        for f in resumos.faturas(con, uid, hoje):
            if f["conta"] == l["conta"]:
                texto += f"\nFatura {esc(f['conta'])}: {brl(f['total'])}, fecha {f['fechamento']:%d/%m}."
    return texto


def menu_resumos() -> Resposta:
    return Resposta("Qual resumo você quer ver?", [
        [("Hoje", "res:hoje"), ("Semana", "res:semana"), ("Mês", "res:mes")],
        [("Faturas dos cartões", "res:fat")],
        [("Acerto do casal", "res:acerto"), ("Metas", "res:metas")],
    ])


def resumo(con, uid, qual, hoje) -> Resposta:
    if qual in ("hoje", "semana", "mes"):
        titulos = {"hoje": f"Hoje, {hoje:%d/%m}", "semana": "Esta semana",
                   "mes": f"{MESES[hoje.month - 1]}, até dia {hoje.day}"}
        inicio, fim = resumos.periodo(qual, hoje)
        return Resposta(resumos.texto_periodo(resumos.resumo_periodo(con, uid, inicio, fim), titulos[qual]))
    if qual == "fat":
        return Resposta(resumos.texto_faturas(resumos.faturas(con, uid, hoje)))
    if qual == "acerto":
        inicio, fim = resumos.periodo("mes", hoje)
        return Resposta(resumos.texto_acerto(resumos.acerto(con, uid, inicio, fim),
                                             f"Acerto de {MESES[hoje.month - 1].lower()}"))
    if qual == "metas":
        return Resposta("Metas entram na Fase 5. Por enquanto, acompanhe pelo painel.")
    return Resposta("Resumo desconhecido.")


def pedir_desfazer(con, pessoa) -> Resposta:
    l = db.ultimo_do_autor(con, pessoa["id"])
    if l is None:
        return Resposta("Você ainda não tem lançamentos para desfazer.")
    return Resposta(f"Desfazer o último lançamento?\n\n{cartao(con, l['id'], confirmar=False)}",
                    [[("Sim, desfazer", f"desf:{l['id']}"), ("Não", f"manter:{l['id']}")]])


def _grade(itens, colunas=2):
    return [itens[i:i + colunas] for i in range(0, len(itens), colunas)]


MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto",
         "Setembro", "Outubro", "Novembro", "Dezembro"]
