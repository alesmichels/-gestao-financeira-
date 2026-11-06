"""Cálculos de resumo usados pelo bot e pelo painel."""
import calendar
import html
from collections import defaultdict
from datetime import date, timedelta

from app import db


def brl(centavos: int) -> str:
    sinal = "-" if centavos < 0 else ""
    reais, cent = divmod(abs(int(centavos)), 100)
    return f"{sinal}R$ {reais:,}".replace(",", ".") + f",{cent:02d}"


def periodo(nome: str, hoje: date) -> tuple[date, date]:
    if nome == "hoje":
        return hoje, hoje
    if nome == "semana":
        return hoje - timedelta(days=hoje.weekday()), hoje
    if nome == "mes":
        return hoje.replace(day=1), hoje
    raise ValueError(nome)


def mes_inteiro(ano: int, mes: int) -> tuple[date, date]:
    return date(ano, mes, 1), date(ano, mes, calendar.monthrange(ano, mes)[1])


def resumo_periodo(con, unidade_id, inicio: date, fim: date) -> dict:
    linhas = db.lancamentos_periodo(con, unidade_id, inicio, fim)
    entradas = sum(l["valor_centavos"] for l in linhas if l["tipo"] == "entrada")
    saidas = sum(l["valor_centavos"] for l in linhas if l["tipo"] == "saida")
    por_categoria = defaultdict(int)
    por_conta = defaultdict(int)
    for l in linhas:
        if l["tipo"] == "saida":
            por_categoria[l["categoria"] or "Sem categoria"] += l["valor_centavos"]
            por_conta[l["conta"] or "Sem forma"] += l["valor_centavos"]
    return {
        "inicio": inicio, "fim": fim, "entradas": entradas, "saidas": saidas,
        "saldo": entradas - saidas, "qtd": len(linhas),
        "categorias": sorted(por_categoria.items(), key=lambda x: -x[1]),
        "contas": sorted(por_conta.items(), key=lambda x: -x[1]),
        "pendentes": len(db.pendentes(con, unidade_id)),
    }


def _dia_seguro(ano, mes, dia):
    return date(ano, mes, min(dia, calendar.monthrange(ano, mes)[1]))


def _somar_mes(d: date, n: int, dia: int) -> date:
    m = d.month - 1 + n
    return _dia_seguro(d.year + m // 12, m % 12 + 1, dia)


def ciclo_fatura(dia_fechamento: int, hoje: date) -> tuple[date, date]:
    """Compras com data em [inicio, fechamento) entram na fatura que fecha em `fechamento`."""
    fechamento = _dia_seguro(hoje.year, hoje.month, dia_fechamento)
    if hoje >= fechamento:
        fechamento = _somar_mes(hoje, 1, dia_fechamento)
    inicio = _somar_mes(fechamento, -1, dia_fechamento)
    return inicio, fechamento


def faturas(con, unidade_id, hoje: date) -> list[dict]:
    resultado = []
    for c in db.contas(con, unidade_id):
        if c["tipo"] != "credito" or not c["dia_fechamento"]:
            continue
        inicio, fechamento = ciclo_fatura(c["dia_fechamento"], hoje)
        linhas = db.lancamentos_periodo(con, unidade_id, inicio, fechamento - timedelta(days=1))
        total = sum(l["valor_centavos"] for l in linhas if l["conta_id"] == c["id"] and l["tipo"] == "saida")
        vencimento = None
        if c["dia_vencimento"]:
            vencimento = _dia_seguro(fechamento.year, fechamento.month, c["dia_vencimento"])
            if vencimento <= fechamento:
                vencimento = _somar_mes(fechamento, 1, c["dia_vencimento"])
        resultado.append({"conta": c["nome"], "total": total, "fechamento": fechamento,
                          "vencimento": vencimento, "dias_para_fechar": (fechamento - hoje).days})
    return sorted(resultado, key=lambda f: f["fechamento"])


def acerto(con, unidade_id, inicio: date, fim: date) -> dict:
    """Quanto cada pessoa pagou e quanto deveria ter pago nos gastos compartilhados.

    - 'individual': fica fora do acerto.
    - 'proporcional': divide pelo peso de cada pessoa; '50/50': divide igual.
    - Quem pagou = titular da conta; se a conta não tem titular, quem lançou.
    - Cartão de crédito sem titular (conjunto) fica fora: a conta conjunta já é dividida.
    """
    pess = db.pessoas(con, unidade_id)
    soma_pesos = sum(p["peso_divisao"] for p in pess) or 1
    pesos = {p["id"]: p["peso_divisao"] / soma_pesos for p in pess}
    nomes = {p["id"]: p["nome"] for p in pess}
    pagou = defaultdict(int)
    deveria = defaultdict(float)
    for l in db.lancamentos_periodo(con, unidade_id, inicio, fim):
        if l["tipo"] != "saida" or l["regra_divisao"] == "individual":
            continue
        if l["conta_tipo"] == "credito" and l["conta_titular_id"] is None:
            continue
        pagador = l["conta_titular_id"] or l["autor_id"]
        if pagador not in nomes:
            continue
        pagou[pagador] += l["valor_centavos"]
        for pid in nomes:
            fatia = pesos[pid] if l["regra_divisao"] == "proporcional" else 1 / len(nomes)
            deveria[pid] += l["valor_centavos"] * fatia
    saldos = {pid: round(pagou[pid] - deveria[pid]) for pid in nomes}
    devedor = min(saldos, key=saldos.get) if saldos else None
    credor = max(saldos, key=saldos.get) if saldos else None
    valor = -saldos[devedor] if devedor is not None else 0
    return {
        "pessoas": [{"nome": nomes[pid], "pagou": pagou[pid], "deveria": round(deveria[pid]),
                     "saldo": saldos[pid]} for pid in nomes],
        "de": nomes.get(devedor), "para": nomes.get(credor), "valor": max(valor, 0),
    }


# ---------- textos para o chat (HTML do Telegram) ----------

def texto_periodo(r: dict, titulo: str) -> str:
    linhas = [f"<b>{esc(titulo)}</b>",
              f"Receitas: {brl(r['entradas'])}",
              f"Gastos: {brl(r['saidas'])}",
              f"Saldo: <b>{brl(r['saldo'])}</b>"]
    if r["categorias"]:
        linhas.append("")
        linhas.append("Maiores categorias:")
        linhas += [f"• {esc(nome)}: {brl(v)}" for nome, v in r["categorias"][:3]]
    if r["qtd"] == 0:
        linhas.append("\nNenhum lançamento confirmado no período.")
    if r["pendentes"]:
        linhas.append(f"\n{r['pendentes']} lançamento(s) aguardando confirmação.")
    return "\n".join(linhas)


def texto_faturas(fs: list[dict]) -> str:
    if not fs:
        return "Nenhum cartão de crédito com dia de fechamento cadastrado."
    linhas = ["<b>Faturas abertas</b>"]
    for f in fs:
        quando = "fecha hoje" if f["dias_para_fechar"] == 0 else f"fecha em {f['dias_para_fechar']} dia(s)"
        venc = f" · vence {f['vencimento']:%d/%m}" if f["vencimento"] else ""
        linhas.append(f"• {esc(f['conta'])}: <b>{brl(f['total'])}</b> · {quando} ({f['fechamento']:%d/%m}){venc}")
    return "\n".join(linhas)


def texto_acerto(a: dict, titulo: str) -> str:
    linhas = [f"<b>{esc(titulo)}</b>"]
    for p in a["pessoas"]:
        linhas.append(f"• {esc(p['nome'])}: pagou {brl(p['pagou'])}, parte dele(a) {brl(p['deveria'])}")
    if a["valor"] >= 1 and a["de"] != a["para"]:
        linhas.append(f"\n{esc(a['de'])} transfere <b>{brl(a['valor'])}</b> para {esc(a['para'])}.")
    else:
        linhas.append("\nTudo acertado, ninguém deve nada.")
    return "\n".join(linhas)


def esc(texto) -> str:
    return html.escape(str(texto), quote=False)
