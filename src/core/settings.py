from pydantic import BaseModel, Field

# Lista de modelos OpenRouter disponíveis para o usuário escolher na UI.
# O primeiro da lista é o padrão.
MODEL_LIST = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "poolside/laguna-m.1:free",
]

# Modelo selecionado por padrão quando a UI abre.
DEFAULT_MODEL = MODEL_LIST[0]

# Instruções de sistema passadas para o agente Agno.
# A LLM recebe isso como comportamento esperado.
AGENT_INSTRUCTIONS = [
    "Você é um especialista em análise de conteúdo do YouTube.",
    "Sua tarefa é encontrar vídeos relevantes no YouTube, coletar seus comentários e analisar as emoções presentes neles.",
    "Sempre utilize as ferramentas disponíveis do YouTube para pesquisar vídeos e obter comentários. Não invente ou assuma dados quando uma ferramenta estiver disponível.",
    "Utilize apenas informações obtidas pelas ferramentas para realizar a análise.",
    "Analise os comentários identificando a distribuição das emoções predominantes e os principais insights.",
    "Selecione comentários representativos e associe a emoção predominante de cada um.",
    "Todas as respostas devem estar em Português do Brasil.",
    "A resposta FINAL deve ser APENAS um objeto JSON válido.",
    "O JSON deve seguir exatamente o schema EmotionAnalysisReport.",
    "Não inclua markdown.",
    "Não utilize blocos de código.",
    "Não adicione explicações, introduções, conclusões ou qualquer texto fora do JSON.",
    "Todos os campos obrigatórios do schema devem estar presentes.",
    "Se alguma informação não puder ser obtida, utilize valores vazios apropriados ao tipo do campo (string vazia, lista vazia ou objeto vazio), mantendo o schema válido."
]


class EmotionAnalysisReport(BaseModel):
    """Schema Pydantic que valida a resposta JSON da LLM.

    Cada campo corresponde a uma seção do relatório exibida na UI:
    - summary: resumo em texto livre da análise
    - emotion_distribution: proporção geral (positivo/negativo/neutro)
    - detailed_emotions: detalhamento de cada emoção identificada
    - key_insights: lista de descobertas relevantes
    - top_comments: comentários em destaque com a emoção associada
    """
    summary: str = Field(..., description="Resumo da análise em português.")
    emotion_distribution: dict[str, float] = Field(
        ..., description="Distribuição das emoções nos comentários (ex: positivo, negativo, neutro)."
    )
    detailed_emotions: dict[str, float] = Field(
        ..., description="Detalhamento de cada emoção identificada (ex: alegria, raiva, tristeza)."
    )
    key_insights: list[str] = Field(..., description="Insights principais extraídos da análise.")
    top_comments: list[dict] = Field(
        ...,
        description="Comentários em destaque com o texto e a emoção identificada.",
    )
