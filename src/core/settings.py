from pydantic import BaseModel, Field

# Lista de modelos OpenRouter disponíveis para o usuário escolher na UI.
# O primeiro da lista é o padrão.
MODEL_LIST = [
    "DeepSeek-V3.1",
    "gemma-4-31B-it",
]

# Modelo selecionado por padrão quando a UI abre.
DEFAULT_MODEL = MODEL_LIST[0]

AGENT_INSTRUCTIONS = [
    "Você é um especialista em análise de conteúdo do YouTube.",
    "Sua tarefa é: (1) buscar vídeos com as ferramentas, (2) coletar comentários reais, (3) ANALISAR os comentários coletados.",
    "Sempre utilize as ferramentas do YouTube para obter dados reais. NUNCA invente comentários, emoções ou distribuições.",
    "Após receber os comentários reais pela ferramenta, analise APENAS o conteúdo desses comentários.",
    "Para cada comentário real, identifique a emoção predominante (alegria, raiva, tristeza, surpresa, medo, etc.).",
    "Calcule a distribuição de emoções com base APENAS nos comentários que você recebeu.",
    "Extraia insights reais dos padrões observados nos comentários.",
    "Selecione comentários reais como exemplos nos top_comments, com o texto exato do comentário.",
    "Todas as respostas devem estar em Português do Brasil.",
    "CRÍTICO: NÃO crie ou invente dados. Se não houver comentários suficientes, reporte o que existe.",
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
