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
            f"Analyze the emotions expressed in the top comments "
            f"of the most popular {question} videos.\n\n"
            f"Return ONLY a JSON object with this exact structure "
            f"(no markdown, no extra text):\n{SCHEMA_EXAMPLE}\n\n"
            "Use only the example structure; do not copy the example values. "
            "Generate actual emotion distribution values and insights based on the current topic. "
            "Include up to 5 representative `top_comments` (each with `text` and `emotion`). "
            "If fewer comments are available, return as many as found. Use Portuguese for text values."
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
                    if raw:
                        break
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
        steps = []
        for msg in response.messages or []:
            tool_calls = getattr(msg, "tool_calls", None) or []
            for tc in tool_calls:
                fn = getattr(tc, "function", None)
                if fn:
                    args_summary = _tool_args_summary(fn.arguments or "{}")
                    label = _tool_label(fn.name, args_summary)
                    steps.append(label)

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
