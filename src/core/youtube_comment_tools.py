import json
from googleapiclient.discovery import build
from agno.tools import Toolkit


class YouTubeCommentsTools(Toolkit):
    """Toolkit Agno que expõe a YouTube Data API v3 como ferramentas para a LLM.

    A LLM decide quando e como chamar estas ferramentas durante a execução.
    Os resultados retornam como JSON strings.

    Args:
        api_key: Chave de API do Google Cloud com YouTube Data API v3 ativada.
    """

    def __init__(self, api_key: str, **kwargs):
        print(f"[YouTubeTools] Inicializando com API key: {api_key[:8]}...")
        self.youtube = build("youtube", "v3", developerKey=api_key)
        tools = [self.search_videos, self.get_video_comments]
        super().__init__(name="youtube_comments_tools", tools=tools, **kwargs)
        print("[YouTubeTools] Inicializado com sucesso")

    def search_videos(self, query: str, max_results: int = 5, order: str = "viewCount") -> str:
        """Busca vídeos no YouTube por palavra-chave.

        Chamado pela LLM para encontrar vídeos relevantes sobre o tema.

        Args:
            query: Termo de busca.
            max_results: Máximo de vídeos a retornar (1-50).
            order: Critério de ordenação (viewCount, relevance, date, rating).

        Returns:
            JSON string com lista de vídeos: video_id, title, channel.
        """
        print(f"[YouTubeTools] search_videos(query='{query}', max_results={max_results}, order='{order}')")
        try:
            res = self.youtube.search().list(
                part="snippet", q=query, type="video", order=order, maxResults=max_results
            ).execute()
            videos = [
                {"video_id": i["id"]["videoId"], "title": i["snippet"]["title"], "channel": i["snippet"]["channelTitle"]}
                for i in res.get("items", [])
            ]
            print(f"[YouTubeTools] Encontrados {len(videos)} vídeos para '{query}'")
            return json.dumps(videos, indent=2)
        except Exception as e:
            print(f"[YouTubeTools] ERRO ao buscar vídeos: {e}")
            return json.dumps({"error": str(e)})

    def get_video_comments(self, video_id: str, max_results: int = 50, order: str = "relevance") -> str:
        """Coleta comentários públicos de um vídeo específico.

        Chamado pela LLM após a busca para obter o conteúdo dos comentários.

        Args:
            video_id: ID do vídeo no YouTube.
            max_results: Máximo de comentários a retornar (1-100).
            order: Ordenação (relevance ou time).

        Returns:
            JSON string com lista de comentários: author, text, likes, published_at.
        """
        print(f"[YouTubeTools] get_video_comments(video_id='{video_id}', max_results={max_results})")
        try:
            res = self.youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=max_results,
                order=order, textFormat="plainText"
            ).execute()
        except Exception as e:
            print(f"[YouTubeTools] ERRO nos comentários do vídeo {video_id}: {e}")
            return json.dumps({"error": f"Error fetching comments: {e}"})

        comments = [
            {
                "author": c["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                "text": c["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                "likes": c["snippet"]["topLevelComment"]["snippet"]["likeCount"],
                "published_at": c["snippet"]["topLevelComment"]["snippet"]["publishedAt"],
            }
            for c in res.get("items", [])
        ]
        print(f"[YouTubeTools] {len(comments)} comentários encontrados para vídeo {video_id}")
        return json.dumps(comments, indent=2)
