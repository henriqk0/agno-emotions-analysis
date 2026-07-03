import os
import json
import asyncio
from dotenv import load_dotenv

from core.agent import AgentFactory
from core.youtube_comment_tools import YouTubeCommentsTools
from core.settings import MODEL_LIST, AGENT_INSTRUCTIONS, EmotionAnalysisReport

load_dotenv()

youtube_api_key = os.getenv("YOUTUBE_DATA_API_KEY")

# Exemplo do JSON que a LLM deve retornar.
# Incluído no prompt para reduzir ambiguidade sobre o schema esperado.
SCHEMA_EXAMPLE = json.dumps(
    {
        "summary": "Resumo da análise em português",
        "emotion_distribution": {"positivo": 0.45, "negativo": 0.30, "neutro": 0.25},
        "detailed_emotions": {"alegria": 0.30, "raiva": 0.15, "tristeza": 0.10, "surpresa": 0.08, "medo": 0.05},
        "key_insights": ["Insight principal 1", "Insight principal 2"],
        "top_comments": [
                {"text": "Ótimo vídeo, muito informativo!", "emotion": "alegria"},
                {"text": "Isso me deixou bem irritado.", "emotion": "raiva"},
                {"text": "Fiquei surpreso com os dados apresentados.", "emotion": "surpresa"},
                {"text": "Triste ver isso acontecendo.", "emotion": "tristeza"},
                {"text": "Isso me deixou com medo do futuro.", "emotion": "medo"},
        ],
    },
    indent=2,
)


def _extract_json(text: str) -> str:
    """Extrai o primeiro objeto JSON válido de uma string.

    A LLM ocasionalmente adiciona texto antes/depois do JSON.
    Esta função localiza o bloco JSON procurando por '{"summary"'
    como âncora (fallback para o primeiro '{' encontrado).

    Args:
        text: String bruta retornada pela LLM.

    Returns:
        String JSON extraída, ou '' se nenhum JSON for encontrado.
    """
    start = text.find('{"summary"')
    if start == -1:
        start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def _tool_args_summary(args_str: str) -> str:
    """Extrai um resumo legível dos argumentos de uma tool call.

    Args:
        args_str: JSON string com os argumentos da tool.

    Returns:
        String amigável para exibir na timeline (ex: '"games", 5 resultados').
    """
    try:
        args = json.loads(args_str)
        query = args.get("query", "")
        video_id = args.get("video_id", "")
        max_results = args.get("max_results", "")
        parts = []
        if query:
            parts.append(f'"{query}"')
        if max_results:
            parts.append(f"{max_results} resultados")
        if video_id and not query:
            parts.append(video_id[:12])
        return ", ".join(parts) if parts else args_str[:60]
    except Exception:
        return args_str[:60]


def _tool_args_summary_from_dict(args: dict | None) -> str:
    """Extrai um resumo legível de argumentos de tool já parseados."""
    if not args:
        return ""
    query = args.get("query", "")
    video_id = args.get("video_id", "")
    max_results = args.get("max_results", "")
    parts = []
    if query:
        parts.append(f'"{query}"')
    if max_results:
        parts.append(f"{max_results} resultados")
    if video_id and not query:
        parts.append(video_id[:12])
    return ", ".join(parts) if parts else json.dumps(args, ensure_ascii=False)[:60]


def _tool_label(name: str, args_summary: str) -> str:
    """Gera o label amigável de uma tool call para a timeline da UI.

    Args:
        name: Nome da tool (search_videos, get_video_comments).
        args_summary: Resumo dos argumentos (via _tool_args_summary).

    Returns:
        String com ícone e descrição para exibir na timeline.
    """
    labels = {
        "search_videos": f"🔍 Buscando vídeos sobre {args_summary}",
        "get_video_comments": f"💬 Coletando comentários ({args_summary})",
    }
    return labels.get(name, f"🔧 {name}: {args_summary}")


def _extract_tool_steps(response) -> list[tuple[str, str]]:
    """Extrai tool calls reais das mensagens do agente.

    Returns:
        Lista de tuplas (tool_name, label) para exibir na timeline.
    """
    steps = []
    for tool in getattr(response, "tools", None) or []:
        name = getattr(tool, "tool_name", None)
        if name:
            args_summary = _tool_args_summary_from_dict(getattr(tool, "tool_args", None))
            steps.append((name, _tool_label(name, args_summary)))

    if steps:
        return steps

    for msg in response.messages or []:
        tool_calls = getattr(msg, "tool_calls", None) or []
        for tc in tool_calls:
            fn = getattr(tc, "function", None)
            if fn:
                args_summary = _tool_args_summary(fn.arguments or "{}")
                label = _tool_label(fn.name, args_summary)
                steps.append((fn.name, label))
    return steps


def _used_required_youtube_tools(response) -> bool:
    """Confirma que a resposta foi baseada em busca e comentários reais."""
    tool_names = {name for name, _ in _extract_tool_steps(response)}
    return {"search_videos", "get_video_comments"}.issubset(tool_names)


def _collected_comment_texts(response) -> set[str]:
    """Retorna os textos reais coletados por get_video_comments."""
    return {comment["text"].strip() for comment in _collected_comments(response) if comment.get("text")}


def _collected_comments(response) -> list[dict]:
    """Retorna comentários reais coletados pelas tools em uma lista plana."""
    comments = []
    for tool in getattr(response, "tools", None) or []:
        if getattr(tool, "tool_name", None) != "get_video_comments":
            continue
        video_id = (getattr(tool, "tool_args", None) or {}).get("video_id", "")
        try:
            tool_comments = json.loads(getattr(tool, "result", "") or "[]")
        except json.JSONDecodeError:
            continue
        if not isinstance(tool_comments, list):
            continue
        for comment in tool_comments:
            if isinstance(comment, dict) and comment.get("text"):
                comments.append({
                    "video_id": video_id,
                    "text": comment.get("text", ""),
                    "likes": comment.get("likes", 0),
                    "published_at": comment.get("published_at", ""),
                })
    return comments


def _top_comments_are_from_tools(raw: str, response) -> bool:
    """Garante que os comentários destacados vieram da API do YouTube."""
    collected_texts = _collected_comment_texts(response)
    if not collected_texts:
        return False

    try:
        report = json.loads(raw)
    except json.JSONDecodeError:
        return False

    top_comments = report.get("top_comments", [])
    if not top_comments:
        return True

    collected_normalized = {text.casefold() for text in collected_texts}
    for comment in top_comments:
        text = comment.get("text", "").strip() if isinstance(comment, dict) else ""
        if text.casefold() not in collected_normalized:
            return False
    return True


def _build_analysis_prompt(question: str, comments: list[dict]) -> str:
    """Monta prompt de análise a partir dos comentários já coletados."""
    comments_json = json.dumps(comments[:120], ensure_ascii=False, indent=2)
    return (
        f"Tema analisado: {question}\n\n"
        "Abaixo estão comentários reais coletados da API do YouTube. "
        "Analise somente estes comentários, sem inventar dados externos.\n\n"
        f"COMENTÁRIOS COLETADOS:\n{comments_json}\n\n"
        "Retorne APENAS um objeto JSON válido, sem markdown, sem bloco de código e sem texto extra. "
        f"Use exatamente esta estrutura:\n{SCHEMA_EXAMPLE}\n\n"
        "Use apenas a estrutura do exemplo; não copie os valores do exemplo. "
        "Em top_comments, escolha até 5 comentários representativos da lista acima e mantenha o campo text "
        "exatamente igual ao comentário coletado, sem traduzir, resumir ou reescrever. "
        "Escreva summary, key_insights e nomes de emotion em Português do Brasil."
    )


def _error_report(msg: str) -> str:
    """Cria uma mensagem de resultado de erro no formato que o frontend espera.

    Em vez de retornar JSON inválido ou quebrar o schema, preenche um
    EmotionAnalysisReport vazio com a mensagem de erro no campo summary.
    O frontend detecta summary começando com 'Erro' ou 'A API' e exibe
    o card de erro amigável.

    Args:
        msg: Mensagem de erro descritiva.

    Returns:
        JSON string no formato {"type": "result", "data": {...}}.
    """
    return json.dumps({
        "type": "result",
        "data": EmotionAnalysisReport(
            summary=msg,
            emotion_distribution={},
            detailed_emotions={},
            key_insights=[],
            top_comments=[],
        ).model_dump(),
    })


class AgentService:
    """Orquestra a execução do agente Agno e retorna resultados para o frontend.

    É um async generator: cada yield envia uma mensagem JSON para o state do Reflex.
    O frontend recebe primeiro os steps (tool calls executadas) e por fim o resultado.
    """

    @staticmethod
    async def run(question: str, model_id: str):
        """Executa a análise completa: LLM → tools → validação → resultado.

        Fluxo:
        1. Valida chave da API do YouTube
        2. Monta prompt com schema explícito
        3. Tenta modelo atual com retry (3x, backoff exponencial)
        4. Se falhar, tenta próximo modelo da lista
        5. Extrai steps (tool calls) de response.messages e envia para UI
        6. Extrai JSON, valida contra EmotionAnalysisReport
        7. Envia resultado final ou erro amigável

        Args:
            question: Tema digitado pelo usuário.
            model_id: Modelo OpenRouter selecionado.

        Yields:
            JSON strings com type="step" (timeline) ou type="result" (final).
        """
        print(f"[AgentService] Iniciando análise para: {question[:80]}")
        print(f"[AgentService] Modelo selecionado: {model_id}")

        if not youtube_api_key:
            print("[AgentService] ERRO: YOUTUBE_DATA_API_KEY não configurada")
            yield _error_report("Erro: chave da API do YouTube não configurada.")
            return

        prompt = (
            f"Tema solicitado pelo usuário: {question}\n\n"
            "Execute obrigatoriamente este fluxo antes de responder:\n"
            "1. Chame a ferramenta search_videos para encontrar os vídeos mais populares e relevantes sobre o tema.\n"
            "2. A partir dos video_id retornados, chame a ferramenta get_video_comments para coletar comentários reais.\n"
            "3. Analise as emoções expressas somente nos comentários retornados pelas ferramentas.\n"
            "4. Só depois das tool calls, retorne a resposta final.\n\n"
            "A resposta final deve ser APENAS um objeto JSON válido, sem markdown, sem bloco de código "
            f"e sem texto extra. Use exatamente esta estrutura:\n{SCHEMA_EXAMPLE}\n\n"
            "Use apenas a estrutura do exemplo; não copie os valores do exemplo. "
            "Gere distribuições de emoção, insights e comentários representativos com base nos dados coletados. "
            "Inclua até 5 top_comments representativos, cada um com text e emotion. "
            "Em top_comments, mantenha o campo text exatamente como retornado pela ferramenta, sem traduzir ou reescrever. "
            "Se houver menos comentários disponíveis, retorne apenas os encontrados. "
            "Escreva summary, key_insights e nomes de emotion em Português do Brasil."
        )

        # Tenta o modelo atual primeiro; se esgotar retries, tenta os demais.
        models_to_try = [model_id] + [m for m in MODEL_LIST if m != model_id]
        last_error = ""
        response = None
        raw = ""

        for model in models_to_try:
            if model != model_id:
                print(f"[AgentService] Modelo {model_id} falhou, tentando {model}")

            print("[AgentService] Criando agente...")
            agent = AgentFactory.create_agent(
                model_id=model,
                agent_instructions=AGENT_INSTRUCTIONS,
                available_tools=[YouTubeCommentsTools(api_key=youtube_api_key)],
            )

            for attempt in range(3):
                print(f"[AgentService] Tentativa {attempt + 1}/3 com {model}...")
                try:
                    response = agent.run(prompt, stream=False)
                    raw = _extract_json(response.content or "")
                    if (
                        raw
                        and _used_required_youtube_tools(response)
                        and _top_comments_are_from_tools(raw, response)
                    ):
                        break
                    if raw:
                        if _used_required_youtube_tools(response):
                            collected_comments = _collected_comments(response)
                            if collected_comments:
                                print(
                                    "[AgentService] Reanalisando comentários coletados sem tool calling..."
                                )
                                analysis_agent = AgentFactory.create_agent(
                                    model_id=model,
                                    agent_instructions=(
                                        "Você é um analista de emoções. "
                                        "Receba comentários reais já coletados e retorne apenas JSON válido. "
                                        "Não use markdown e não invente comentários."
                                    ),
                                    available_tools=[],
                                )
                                analysis_response = analysis_agent.run(
                                    _build_analysis_prompt(question, collected_comments),
                                    stream=False,
                                )
                                analysis_raw = _extract_json(analysis_response.content or "")
                                if (
                                    analysis_raw
                                    and _top_comments_are_from_tools(analysis_raw, response)
                                ):
                                    raw = analysis_raw
                                    break

                        last_error = (
                            "Modelo retornou JSON sem evidência suficiente de dados reais do YouTube."
                        )
                        print(f"[AgentService] {last_error}")
                        raw = ""
                        await asyncio.sleep(2 ** attempt)
                        continue
                    last_error = response.content[:200]
                    print(f"[AgentService] Sem JSON na resposta, aguardando {2 ** attempt}s...")
                    await asyncio.sleep(2 ** attempt)
                except Exception as e:
                    last_error = str(e)
                    print(f"[AgentService] Exceção: {e}, aguardando {2 ** attempt}s...")
                    await asyncio.sleep(2 ** attempt)

            if raw:
                break
            print(f"[AgentService] Modelo {model} esgotou tentativas")

        if not raw:
            yield _error_report(
                "A API de IA está temporariamente sobrecarregada. "
                "Tente novamente em alguns instantes."
            )
            return

        # Extrai tool calls reais da mensagens do agente para exibir na timeline.
        steps = [label for _, label in _extract_tool_steps(response)]

        print(f"[AgentService] Steps detectados: {len(steps)}")
        for label in steps:
            yield json.dumps({"type": "step", "step_type": "tool_call", "label": label, "status": "done"})
            await asyncio.sleep(0.15)

        print(f"[AgentService] JSON extraído: {len(raw)} chars (de {len(response.content or '')} brutos)")

        try:
            report = EmotionAnalysisReport.model_validate_json(raw)
            print(f"[AgentService] Relatório validado com sucesso")
            print(f"[AgentService] Distribuição: {report.emotion_distribution}")
            print(f"[AgentService] Insights: {len(report.key_insights)} encontrados")
            print(f"[AgentService] Comentários em destaque: {len(report.top_comments)}")
            yield json.dumps({"type": "result", "data": report.model_dump()})
        except Exception as e:
            print(f"[AgentService] ERRO ao validar JSON: {e}")
            print(f"[AgentService] JSON extraído (início): {raw[:300]}...")
            yield _error_report(
                "Erro ao processar resposta da IA. Tente novamente com um tema diferente."
            )
