from typing import Any, TypedDict
from dotenv import load_dotenv
import os

import reflex as rx

from core.settings import MODEL_LIST, DEFAULT_MODEL
from core.services import AgentService

load_dotenv()

if not os.getenv("OPENROUTER_API_KEY"):
    raise Exception("Please set OPENROUTER_API_KEY environment variable.")

class QA(TypedDict):
    question: str
    answer: str


class State(rx.State):
    _chats: dict[str, list[QA]] = {
        "Intros": [],
    }

    current_chat = "Intros"

    processing: bool = False

    is_modal_open: bool = False

    current_model: str = DEFAULT_MODEL
    model_list: list[str] = MODEL_LIST

    @rx.event
    def set_model(self, model: str):
        self.current_model = model

    @rx.event
    def create_chat(self, form_data: dict[str, Any]):
        new_chat_name = form_data["new_chat_name"]
        self.current_chat = new_chat_name
        self._chats[new_chat_name] = []
        self.is_modal_open = False

    @rx.event
    def set_is_modal_open(self, is_open: bool):
        self.is_modal_open = is_open

    @rx.var
    def selected_chat(self) -> list[QA]:
        return (
            self._chats[self.current_chat] if self.current_chat in self._chats else []
        )

    @rx.event
    def delete_chat(self, chat_name: str):
        if chat_name not in self._chats:
            return
        del self._chats[chat_name]
        if len(self._chats) == 0:
            self._chats = {
                "Intros": [],
            }
        if self.current_chat not in self._chats:
            self.current_chat = list(self._chats.keys())[0]

    @rx.event
    def set_chat(self, chat_name: str):
        self.current_chat = chat_name

    @rx.event
    def set_new_chat_name(self, new_chat_name: str):
        self.new_chat_name = new_chat_name

    @rx.var
    def chat_titles(self) -> list[str]:
        return list(self._chats.keys())

    @rx.event
    async def process_question(self, form_data: dict[str, Any]):
        question = form_data["question"]
        if not question:
            return
        async for value in self.agno_process_question(question):
            yield value

    @rx.event
    async def agno_process_question(self, question: str):
        qa = QA(question=question, answer="")
        self._chats[self.current_chat].append(qa)
        self.processing = True
        yield

        async for chunk in AgentService.run(question, self.current_model):
            self._chats[self.current_chat][-1]["answer"] += chunk
            yield

        self.processing = False
