# Agno Emotions Analysis

Agente em Python para buscar comentarios publicos do YouTube e analisar emocoes/reacoes da audiencia usando Agno, OpenRouter e Reflex.

## Stack

- Python 3.12+
- Agno
- OpenRouter
- YouTube Data API v3
- Reflex

## Dependencias

Este projeto usa o `requirements.txt` como fonte oficial de dependencias.

Instale com o gerenciador de pacotes `uv`:

```bash
uv venv .venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

No macOS/Linux:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Se ainda nao tiver o `uv` instalado:

```bash
pip install uv
```

## Configuracao

Crie um arquivo `.env` na raiz do projeto com base no `.env.example`:

```env
OPENROUTER_API_KEY=<YOUR_OPENROUTER_API_KEY>
YOUTUBE_DATA_API_KEY=<YOUR_YOUTUBE_DATA_API_KEY>
```

Onde conseguir as chaves:

- `OPENROUTER_API_KEY`: crie uma chave em https://openrouter.ai/
- `YOUTUBE_DATA_API_KEY`: crie uma chave no Google Cloud Console com a **YouTube Data API v3** ativada.

Para a chave do YouTube, use acesso a **dados publicos**. Nao e necessario OAuth nem conta de servico para ler comentarios publicos.

## Rodando a UI

```bash
reflex run
```

Depois abra o endereco exibido no terminal, normalmente:

```text
http://localhost:3000
```

## Rodando via CLI

```bash
python main.py
```

Digite um tema quando o terminal pedir entrada. Exemplo:

```text
python programming
```

O agente vai procurar videos populares relacionados ao tema, buscar comentarios e analisar as emocoes expressas.

## Arquitetura

```text
main.py                     # entrada via terminal
rxconfig.py                 # configuracao do Reflex
src/chat/                   # UI e estado da aplicacao Reflex
src/core/                   # ferramentas e integracoes de dominio
docs/PROMPTS.md             # notas e prompts do projeto
requirements.txt            # fonte oficial de dependencias
```

## Quota da YouTube Data API

A YouTube Data API usa quota diaria por projeto no Google Cloud. As chamadas de busca e leitura de comentarios consomem unidades dessa quota.

Boas praticas:

- limite a quantidade de videos buscados;
- limite a quantidade de comentarios por video;
- evite rodar loops longos durante desenvolvimento;
- acompanhe o consumo em **Google Cloud Console > APIs e servicos > YouTube Data API v3 > Quotas**.

Dependendo do volume de uso, pode haver custos ou necessidade de pedir aumento de quota no Google Cloud.

## Git

O `.env` nao deve ser commitado. Use `.env.example` para documentar as variaveis esperadas.

Arquivos de lock do Reflex, como `reflex.lock/bun.lock` e `reflex.lock/package.json`, devem ser versionados para ajudar a reproduzir o frontend gerado.
