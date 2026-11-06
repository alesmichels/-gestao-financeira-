"""Interpreta mensagens de lançamento escritas em texto livre, sem IA.

Exemplos que entende:
    mercado 87,50 crédito picpay
    farmácia 42,90 pix ontem
    gasolina 180 cartão conjunto
    almoço 36 vale 03/11
    recebi salário 5.200,00
    roupa 120 débito só meu

Regras (em ordem):
1. Tipo: entrada se começa com "+", "recebi", "entrou", "entrada", "caiu" ou cita uma categoria de entrada.
2. Valor: o número com vírgula/centavos tem preferência; senão o primeiro número.
3. Data: "hoje", "ontem", "anteontem" ou dd/mm[/aaaa]; padrão = hoje.
4. Forma de pagamento: o apelido de conta mais longo encontrado.
5. Categoria: o apelido de categoria mais longo encontrado; se nenhum, "Outros".
6. Divisão: a da categoria, a menos que a mensagem diga "só meu/minha", "pessoal" ou "50/50", "meio a meio".
7. Descrição: o que sobrar da mensagem.
"""
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

RE_VALOR = re.compile(r"^(?:r\$)?(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)(?:reais|r\$)?$")
RE_DATA = re.compile(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2}|\d{4}))?$")
PALAVRAS_ENTRADA = {"+", "recebi", "entrou", "entrada", "caiu"}
PALAVRAS_VAZIAS = {"no", "na", "nos", "nas", "de", "do", "da", "dos", "das", "em", "com", "reais", "rs",
                   "r$", "gastei", "paguei", "comprei", "pago", "foi", "um", "uma", "o", "a", "e", "pelo",
                   "pela", "via", "valor", "recebi", "entrou", "entrada", "caiu", "+", "hoje"}
DIVISAO_INDIVIDUAL = [["so", "meu"], ["so", "minha"], ["so", "meus"], ["so", "minhas"], ["individual"]]
DIVISAO_METADE = [["50/50"], ["meio", "a", "meio"], ["metade", "cada"], ["dividido", "igual"]]


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower().strip()


@dataclass
class Interpretacao:
    tipo: str = "saida"
    valor_centavos: int | None = None
    data: date | None = None
    conta: dict | None = None
    categoria: dict | None = None
    categoria_incerta: bool = False
    regra_divisao: str = "proporcional"
    descricao: str = ""
    cartao_ambiguo: bool = False
    faltando: list = field(default_factory=list)


def _valor_em_centavos(bruto: str) -> int:
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?", bruto):
        bruto = bruto.replace(".", "")
    bruto = bruto.replace(",", ".")
    inteiro, _, frac = bruto.partition(".")
    frac = (frac + "00")[:2]
    return int(inteiro) * 100 + int(frac)


def _apelidos(item) -> list[str]:
    bruto = item["apelidos"]
    lista = json.loads(bruto) if isinstance(bruto, str) else list(bruto)
    return [normalizar(a) for a in lista if a.strip()]


def _achar_sequencia(tokens, alvo, livres):
    n = len(alvo)
    for i in range(len(tokens) - n + 1):
        if tokens[i:i + n] == alvo and all(j in livres for j in range(i, i + n)):
            return list(range(i, i + n))
    return None


def _melhor_apelido(tokens, livres, itens):
    """Retorna (item, posições) do apelido mais longo encontrado."""
    melhor = (None, None, 0)
    for item in itens:
        for apelido in _apelidos(item):
            alvo = apelido.split()
            pos = _achar_sequencia(tokens, alvo, livres)
            if pos and len(" ".join(alvo)) > melhor[2]:
                melhor = (item, pos, len(" ".join(alvo)))
    return melhor[0], melhor[1]


def interpretar(texto: str, hoje: date, contas: list, categorias: list) -> Interpretacao:
    contas = [dict(c) for c in contas]
    categorias = [dict(c) for c in categorias]
    originais = texto.split()
    tokens = [normalizar(t).strip(";:!?()\"'") for t in originais]
    livres = set(range(len(tokens)))
    r = Interpretacao(data=hoje)

    # 1. tipo
    if tokens and (tokens[0] in PALAVRAS_ENTRADA or tokens[0].startswith("+")):
        r.tipo = "entrada"
        if tokens[0].startswith("+") and len(tokens[0]) > 1:
            tokens[0] = tokens[0][1:]
    cats_entrada = [c for c in categorias if c.get("tipo") == "entrada"]
    cat_entrada, pos_entrada = _melhor_apelido(tokens, livres, cats_entrada)
    if cat_entrada:
        r.tipo = "entrada"

    # 6a. divisão explícita (antes do valor, por causa de "50/50")
    divisao_explicita = None
    for padroes, regra in ((DIVISAO_INDIVIDUAL, "individual"), (DIVISAO_METADE, "50/50")):
        for alvo in padroes:
            pos = _achar_sequencia(tokens, alvo, livres)
            if pos and not divisao_explicita:
                divisao_explicita = regra
                livres -= set(pos)
    if divisao_explicita:
        r.regra_divisao = divisao_explicita

    # 3. data
    for i in sorted(livres):
        t = tokens[i]
        if t in ("ontem", "anteontem", "hoje"):
            r.data = hoje - timedelta(days={"hoje": 0, "ontem": 1, "anteontem": 2}[t])
            livres.discard(i)
            break
        m = RE_DATA.match(t)
        if m:
            dia, mes = int(m.group(1)), int(m.group(2))
            ano = int(m.group(3)) if m.group(3) else hoje.year
            if ano < 100:
                ano += 2000
            try:
                d = date(ano, mes, dia)
            except ValueError:
                continue
            if not m.group(3) and d > hoje:
                d = date(ano - 1, mes, dia)
            r.data = d
            livres.discard(i)
            break

    # 2. valor
    candidatos = []
    for i in sorted(livres):
        bruto = tokens[i].rstrip(".,")
        m = RE_VALOR.match(bruto)
        if m:
            numero = m.group(1)
            candidatos.append((("," in numero or re.search(r"\.\d{1,2}$", numero)) is not None, i, numero))
    if candidatos:
        com_centavos = [c for c in candidatos if c[0]]
        _, i, numero = (com_centavos or candidatos)[0]
        valor = _valor_em_centavos(numero)
        if valor > 0:
            r.valor_centavos = valor
            livres.discard(i)
    if r.valor_centavos is None:
        r.faltando.append("valor")

    # 4. forma de pagamento (só para saídas)
    if r.tipo == "saida":
        conta, pos = _melhor_apelido(tokens, livres, contas)
        if conta:
            r.conta = conta
            livres -= set(pos)
        else:
            if any(tokens[i] in ("credito", "cartao") for i in livres):
                r.cartao_ambiguo = True
            r.faltando.append("forma de pagamento")
        for i in list(livres):
            if tokens[i] in ("credito", "cartao"):
                livres.discard(i)

    # 5. categoria
    if r.tipo == "entrada":
        if cat_entrada and pos_entrada and all(p in livres for p in pos_entrada):
            r.categoria = cat_entrada
            livres -= set(pos_entrada)
        else:
            r.categoria = next((c for c in cats_entrada if c["nome"] == "Outras entradas"), None)
            r.categoria_incerta = True
    else:
        cats_saida = [c for c in categorias if c.get("tipo", "saida") == "saida"]
        cat, pos = _melhor_apelido(tokens, livres, cats_saida)
        if cat:
            r.categoria = cat
            # o apelido da categoria também serve de descrição, então não é consumido
        else:
            r.categoria = next((c for c in cats_saida if c["nome"] == "Outros"), None)
            r.categoria_incerta = True

    # 6b. divisão padrão da categoria
    if not divisao_explicita:
        r.regra_divisao = r.categoria["regra_divisao"] if r.categoria else "proporcional"

    # regra da casa: vale recebido conta no dia 1º do mês de uso
    if r.tipo == "entrada" and r.categoria and "vale" in normalizar(r.categoria["nome"]):
        r.data = r.data.replace(day=1)

    # 7. descrição
    palavras = [originais[i] for i in sorted(livres) if tokens[i] not in PALAVRAS_VAZIAS and tokens[i]]
    descricao = " ".join(palavras).strip(" ,.-")
    if not descricao and r.categoria:
        descricao = r.categoria["nome"]
    r.descricao = descricao[:1].upper() + descricao[1:]
    return r
