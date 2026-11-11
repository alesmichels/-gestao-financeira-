# Gestão Financeira

Aplicativo de controle financeiro do casal que roda **no seu computador**, aberto pelo navegador. Sem mensalidade e sem internet obrigatória. Os dados ficam num único arquivo (`dados\financas.db`), que nunca vai para o GitHub.

- **Fase atual:** Fase 1, só o aplicativo local. O bot do Telegram já existe no código, mas está desligado (veja `docs/bot-telegram.md`).
- Os dados **não somem ao fechar o navegador**: cada lançamento é gravado no arquivo na hora em que você clica em Salvar.

## O que o aplicativo faz

| Página | O que tem |
| --- | --- |
| **Visão geral** | Receitas, gastos e saldo do mês · gastos por categoria · formas de pagamento · acerto do casal · faturas abertas |
| **Lançamentos** | Lançamento rápido por frase (`mercado 87,50 crédito picpay`) com conferência antes de salvar · formulário completo · lista do mês, com edição e cancelamento |
| **Configurações** | Pessoas e peso na divisão · cartões com dias de fechamento e vencimento · categorias · palavras reconhecidas · backup |

## Instalação no Windows

### 1. Pré-requisito: Python

No Prompt de Comando (tecla Windows → `cmd` → Enter), confira:

```bat
python --version
```

Se não aparecer `Python 3.11` ou mais novo, instale e **feche e abra o Prompt de novo**:

```bat
winget install --id Python.Python.3.12 -e
```

### 2. Baixar o aplicativo para `C:\Projetos\gestao-financeira`

**Com Git** (recomendado: facilita receber atualizações):

```bat
mkdir C:\Projetos
cd /d C:\Projetos
git clone https://github.com/alesmichels/-gestao-financeira-.git gestao-financeira
```

**Sem Git:** no GitHub, clique em **Code → Download ZIP**, extraia para `C:\Projetos` e renomeie a pasta extraída para `gestao-financeira`.

### 3. Instalar e abrir

Na pasta `C:\Projetos\gestao-financeira`, dê dois cliques em **`abrir-aplicativo.bat`**.

- Na primeira vez, ele instala tudo sozinho (de 1 a 3 minutos).
- Depois, o navegador abre em http://localhost:8501.
- **Deixe a janela preta aberta** enquanto usa. Fechar a janela desliga o aplicativo, e os dados continuam salvos.

### 4. Primeiro uso

1. Em **Configurações**, ajuste o nome da parceira, os pesos da divisão e os dias de fechamento e vencimento dos cartões. Clique em **Salvar** de cada tabela.
2. Em **Lançamentos**, escreva `mercado 10 pix`, aperte Enter, confira e clique em **Salvar lançamento**.
3. Volte em **Visão geral**: o gasto aparece no mês.

Dica: crie um atalho do `abrir-aplicativo.bat` na Área de Trabalho (botão direito → Enviar para → Área de trabalho).

## Como escrever no lançamento rápido

```
mercado 87,50 crédito picpay
farmácia 42,90 pix ontem
gasolina 180 cartão conjunto        → categoria Carro, divisão 50/50
almoço 36 vale 03/11
roupa 120 débito só meu             → fica fora da divisão
recebi salário 5.200
vale caiu 640                       → entrada no dia 1º do mês
```

Antes de salvar, o aplicativo mostra o que entendeu, e dá para ajustar qualquer campo. Se uma palavra que vocês usam não for reconhecida, acrescente-a nos **apelidos** em Configurações.

## Backup

Em **Configurações → Seus dados e backup**:

- **Fazer backup agora:** salva uma cópia em `backups\` (guarda as 30 últimas).
- **Baixar cópia do banco:** baixa o arquivo para você guardar num pen drive ou na nuvem.

Para restaurar: feche o aplicativo e coloque a cópia no lugar de `dados\financas.db`.

## Receber atualizações

Se instalou com Git, rode na pasta do aplicativo:

```bat
git pull
```

Depois abra pelo `abrir-aplicativo.bat`, como sempre. Seus dados não são afetados.

## Para quem for mexer no código

```bat
.venv\Scripts\activate
python -m pytest
```

```
app/
  painel.py        entrada do aplicativo (menu e páginas)
  paginas/         Visão geral, Lançamentos, Configurações
  parser.py        entende as frases do lançamento rápido (regras, sem IA)
  resumos.py       totais, faturas, acerto do casal
  db.py            banco de dados SQLite
  cadastros.py     cadastros iniciais (primeira execução)
  backup.py        cópia de segurança
  bot.py, servico.py   bot do Telegram (opcional)
config/            cadastros iniciais de exemplo
docs/              decisões, diário de cada fase, dicionário de dados
tests/             testes automáticos
```
