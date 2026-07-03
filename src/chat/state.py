import json
import os
from typing import Any, TypedDict

import reflex as rx
from dotenv import load_dotenv

from core.services import AgentService
from core.settings import DEFAULT_MODEL, MODEL_LIST, EmotionAnalysisReport

load_dotenv()

if not os.getenv("SAMBANOVA_API_KEY"):
    raise Exception("Please set SAMBANOVA_API_KEY environment variable.")


class Feature(TypedDict):
    id: str
    title: str
    description: str
    icon: str


class State(rx.State):
    current_page: str = "home"
    selected_feature: Feature | None = None
    user_input: str = ""
    processing: bool = False
    processing_stage: str = "idle"
    analysis_result: dict | None = None
    error: str = ""

    current_model: str = DEFAULT_MODEL
    model_list: list[str] = MODEL_LIST

    features: list[Feature] = [
        Feature(
            id="emotion-analysis",
            title="Análise de Emoções em Comentários do YouTube",
            description="Analise as emoções presentes nos comentários dos vídeos mais populares sobre qualquer tema.",
            icon="message-square-heart",
        ),
    ]

    steps: list[dict] = []

    @rx.var
    def distribution_data(self) -> list[dict]:
        if not self.analysis_result:
            return []

        # CHANGED: supports both dict and EmotionAnalysisReport
        if isinstance(self.analysis_result, dict):
            distribution = self.analysis_result.get("emotion_distribution", {})
        else:
            distribution = self.analysis_result.emotion_distribution

        return [
            {"name": k.capitalize(), "value": v}
            for k, v in distribution.items()
        ]

    @rx.var
    def detailed_emotion_data(self) -> list[dict]:
        if not self.analysis_result:
            return []

        # CHANGED: supports both dict and EmotionAnalysisReport
        if isinstance(self.analysis_result, dict):
            emotions = self.analysis_result.get("detailed_emotions", {})
        else:
            emotions = self.analysis_result.detailed_emotions

        return [
            {"name": k.capitalize(), "value": v}
            for k, v in emotions.items()
        ]

    @rx.var
    def result_summary(self) -> str:
        if not self.analysis_result:
            return ""
        if isinstance(self.analysis_result, dict):
            return self.analysis_result.get("summary", "")
        return self.analysis_result.summary

    @rx.var
    def result_key_insights(self) -> list[str]:
        if not self.analysis_result:
            return []
        if isinstance(self.analysis_result, dict):
            return self.analysis_result.get("key_insights", [])
        return self.analysis_result.key_insights

    @rx.var
    def result_top_comments(self) -> list[dict]:
        if not self.analysis_result:
            return []
        if isinstance(self.analysis_result, dict):
            return self.analysis_result.get("top_comments", [])
        return self.analysis_result.top_comments

    @rx.var
    def is_processing(self) -> bool:
        return self.processing_stage == "processing"

    @rx.event
    def set_model(self, model: str):
        self.current_model = model

    @rx.event
    def go_home(self):
        self.current_page = "home"
        self.selected_feature = None
        self.reset_analysis()

    @rx.event
    def select_feature(self, feature_id: str):
        for f in self.features:
            if f["id"] == feature_id:
                self.selected_feature = f
                self.current_page = "analysis"
                break

    @rx.event
    def set_input(self, value: str):
        self.user_input = value

    @rx.event
    def reset_analysis(self):
        self.user_input = ""
        self.processing = False
        self.processing_stage = "idle"
        self.analysis_result = None
        self.error = ""
        self.steps = []

    @rx.event
    async def start_analysis(self, form_data: dict[str, Any] | None = None):
        if not self.user_input.strip():
            return

        print(f"[State] Iniciando análise para: {self.user_input}")
        print(f"[State] Modelo: {self.current_model}")

        self.processing = True
        self.processing_stage = "processing"
        self.analysis_result = None
        self.error = ""
        self.steps = []
        yield

        try:
            print("[State] Chamando AgentService.run()...")
            async for raw in AgentService.run(self.user_input, self.current_model):
                msg = json.loads(raw)

                if msg["type"] == "step":
                    if msg["step_type"] == "tool_call" and msg["status"] == "running":
                        self.steps = [
                            s for s in self.steps
                            if s.get("status") != "running"
                        ]
                        self.steps.append(msg)

                    elif msg["step_type"] == "tool_call" and msg["status"] == "done":
                        for i, s in enumerate(self.steps):
                            if s.get("tool") == msg.get("tool"):
                                self.steps[i] = msg
                                break
                        else:
                            self.steps.append(msg)

                    elif msg["step_type"] == "reasoning":
                        self.steps.append(msg)

                    yield

                elif msg["type"] == "result":
                    print("[State] Resultado recebido")

                    report = EmotionAnalysisReport(**msg["data"])

                    has_error = (
                        report.summary.startswith("Erro")
                        or report.summary.startswith("A API")
                    ) if report.summary else False

                    if has_error:
                        print(f"[State] Relatório contém erro: {report.summary}")
                        self.error = report.summary
                        self.processing_stage = "idle"

                    else:
                        self.analysis_result = report.model_dump()
                        print("[State] Análise concluída com sucesso")
                        self.processing_stage = "complete"

                    break

        except Exception as e:
            print(f"[State] ERRO na análise: {e}")
            self.error = str(e)
            self.processing_stage = "idle"

        self.processing = False