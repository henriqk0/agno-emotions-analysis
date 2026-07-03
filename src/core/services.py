import os
import json
import asyncio
import logging

from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.sambanova import Sambanova

from core.agent import AgentFactory
from core.youtube_comment_tools import YouTubeCommentsTools
from core.settings import MODEL_LIST, AGENT_INSTRUCTIONS, EmotionAnalysisReport

for name in ["agno", "agno.agno", "agno.utils", "agno-team", "agno-workflow", "httpx"]:
    logging.getLogger(name).setLevel(logging.WARNING)

load_dotenv()

youtube_api_key = os.getenv("YOUTUBE_DATA_API_KEY")


SCHEMA_EXAMPLE = json.dumps(
    {
        "summary": "Resumo da análise em português",
        "emotion_distribution": {"positivo": 0.45, "negativo": 0.30, "neutro": 0.25},
        "detailed_emotions": {"alegria": 0.30, "raiva": 0.15, "tristeza": 0.10, "surpresa": 0.08, "medo": 0.05},
        "key_insights": ["Insight principal 1", "Insight principal 2"],
        "top_comments": [
                {"text": "Ótimo vídeo, muito informativo!", "emotion": "alegria"},
                {"text": "Isso me deixou bem irritado.", "emotion": "raiva"},
        ],
    },
    indent=2,
)


def _extract_json(text: str) -> str | None:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        stripped = stripped[3:-3].strip()
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find('{"summary"')
    if start == -1:
        start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return stripped[start : end + 1]


def _tool_args_summary(args_str: str) -> str:
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
    labels = {
        "search_videos": f"🔍 Buscando vídeos sobre {args_summary}",
        "get_video_comments": f"💬 Coletando comentários ({args_summary})",
    }
    return labels.get(name, f"🔧 {name}: {args_summary}")


def _error_report(msg: str) -> str:
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


def _extract_actions_from_messages(messages) -> list[str]:
    labels = []
    for msg in messages or []:
        tool_calls = getattr(msg, "tool_calls", None) or []
        for tc in tool_calls:
            fn = tc.get("function") if isinstance(tc, dict) else getattr(tc, "function", None)
            if fn:
                args_str = fn.get("arguments", "{}") if isinstance(fn, dict) else getattr(fn, "arguments", "{}")
                name = fn.get("name") if isinstance(fn, dict) else getattr(fn, "name", "")
                args_summary = _tool_args_summary(args_str)
                labels.append(_tool_label(name, args_summary))
    return labels


def _extract_comments_from_messages(messages) -> list[dict]:
    comments = []
    for msg in messages or []:
        role = getattr(msg, "role", "")
        tool_name = getattr(msg, "tool_name", "")
        if role == "tool" and tool_name == "get_video_comments":
            try:
                data = json.loads(msg.content)
                comments.extend(data)
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass
    return comments


def _format_comments(comments: list[dict], max_comments: int = 50) -> str:
    if not comments:
        return "(nenhum comentário encontrado)"
    truncated = comments[:max_comments]
    lines = []
    for i, c in enumerate(truncated, 1):
        text = c.get("text", "").replace("\n", " ").strip()
        author = c.get("author", "desconhecido")
        likes = c.get("likes", 0)
        lines.append(f"{i}. [{author} | {likes} likes] {text}")
    return "\n".join(lines)


class AgentService:

    @staticmethod
    async def run(question: str, model_id: str):
        print(f"[AgentService] Iniciando análise para: {question[:80]}")
        print(f"[AgentService] Modelo selecionado: {model_id}")

        if not youtube_api_key:
            print("[AgentService] ERRO: YOUTUBE_DATA_API_KEY não configurada")
            yield _error_report("Erro: chave da API do YouTube não configurada.")
            return

        models_to_try = [model_id] + [m for m in MODEL_LIST if m != model_id]
        last_error = ""
        phase1_response = None
        real_comments = []

        # ── Phase 1: Fetch real comments via tools ──────────────────────
        phase1_prompt = (
            f"Find the most popular YouTube videos about '{question}' "
            f"using search_videos (max_results=10). "
            f"Then use get_video_comments (max_results=100) to fetch "
            f"comments from AT LEAST 3 different videos. "
            f"After collecting all data, summarize what you found."
        )

        for model in models_to_try:
            if model != model_id:
                print(f"[AgentService] Modelo {model_id} falhou, tentando {model}")

            for attempt in range(3):
                print(f"[AgentService] Fase 1 - Tentativa {attempt + 1}/3 com {model}...")
                try:
                    agent = AgentFactory.create_agent(
                        model_id=model,
                        agent_instructions=AGENT_INSTRUCTIONS,
                        available_tools=[YouTubeCommentsTools(api_key=youtube_api_key)],
                    )
                    phase1_response = agent.run(phase1_prompt, stream=False)
                    if phase1_response:
                        real_comments = _extract_comments_from_messages(phase1_response.messages)
                        if real_comments:
                            print(f"[AgentService] {len(real_comments)} comentários reais extraídos")
                            break
                    last_error = "No response from Phase 1"
                    await asyncio.sleep(2 ** attempt)
                except Exception as e:
                    last_error = str(e)
                    print(f"[AgentService] Exceção Fase 1: {e}, aguardando {2 ** attempt}s...")
                    await asyncio.sleep(2 ** attempt)

            if real_comments:
                break
            print(f"[AgentService] Modelo {model} esgotou tentativas na Fase 1")

        # Early exit if no comments found
        if not real_comments:
            print(f"[AgentService] Nenhum comentário real encontrado")
            yield _error_report(
                "Não foi possível coletar comentários do YouTube. "
                "Tente novamente com um tema diferente."
            )
            return

        # ── Yield action steps from Phase 1 ─────────────────────────
        steps = _extract_actions_from_messages(phase1_response.messages)
        print(f"[AgentService] Actions detectadas: {len(steps)}")
        for label in steps:
            yield json.dumps({"type": "step", "step_type": "tool_call", "label": label, "status": "done"})
            await asyncio.sleep(0.15)

        # ── Phase 2: Analyze without tools (no function-calling errors) ──
        yield json.dumps({"type": "step", "step_type": "reasoning", "label": "Analisando sentimentos nos comentários..."})
        comments_text = _format_comments(real_comments)
        phase2_prompt = (
            f"Analyze the emotions expressed in these real YouTube comments "
            f"about '{question}'.\n\n"
            f"REAL COMMENTS:\n{comments_text}\n\n"
            "IMPORTANTE:\n"
            "- Analise APENAS o texto real dos comentários acima.\n"
            "- NÃO invente comentários, emoções ou distribuições.\n"
            "- Cada comentário em top_comments deve estar PRESENTE na lista acima,\n"
            "  com o texto EXATO como aparece.\n"
            "- Use português do Brasil para o resumo e insights.\n\n"
            f"Retorne APENAS um JSON válido com esta estrutura (sem markdown, sem código extra):\n"
            f"{SCHEMA_EXAMPLE}"
        )

        analysis_agent = Agent(
            model=Sambanova(id=model_id),
            instructions=AGENT_INSTRUCTIONS,
        )

        print(f"[AgentService] Fase 2: Analisando {len(real_comments)} comentários...")
        analysis_response = None
        analysis_error = ""

        for attempt in range(3):
            try:
                analysis_response = analysis_agent.run(phase2_prompt, stream=False)
                if analysis_response and analysis_response.content:
                    # Try to parse JSON directly (should work since no tools)
                    raw = _extract_json(analysis_response.content)
                    if raw:
                        # Validate against schema
                        EmotionAnalysisReport.model_validate_json(raw)
                        break
                    else:
                        analysis_error = "JSON não encontrado na resposta"
                        print(f"[AgentService] Tentativa {attempt + 1}: {analysis_error}")
                        await asyncio.sleep(2 ** attempt)
                else:
                    analysis_error = "Resposta vazia"
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                analysis_error = str(e)
                print(f"[AgentService] Exceção Fase 2: {e}, aguardando {2 ** attempt}s...")
                await asyncio.sleep(2 ** attempt)

        if not analysis_response or not analysis_response.content:
            yield _error_report(
                "A API de IA está temporariamente sobrecarregada. "
                "Tente novamente em alguns instantes."
            )
            return

        raw = _extract_json(analysis_response.content)
        if not raw:
            print(f"[AgentService] JSON não encontrado na resposta da Fase 2")
            yield _error_report(
                "Erro ao processar resposta da IA. Tente novamente com um tema diferente."
            )
            return

        try:
            report = EmotionAnalysisReport.model_validate_json(raw)
        except Exception as e:
            print(f"[AgentService] Falha ao validar resposta: {e}")
            yield _error_report(
                "Erro ao processar resposta da IA. Tente novamente com um tema diferente."
            )
            return

        print(f"[AgentService] Relatório validado com sucesso")
        print(f"[AgentService] Distribuição: {report.emotion_distribution}")
        print(f"[AgentService] Insights: {len(report.key_insights)} encontrados")
        print(f"[AgentService] Comentários em destaque: {len(report.top_comments)}")
        yield json.dumps({"type": "result", "data": report.model_dump()})
