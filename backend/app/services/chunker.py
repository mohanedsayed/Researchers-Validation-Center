import httpx

from app.config import settings


class SemanticChunker:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_chunker_model

    async def generate_chunks(self, text: str) -> list[dict]:
        """
        Uses Ollama to split the text into semantic chunks.
        For Phase 1 MVP, we will simulate a simple semantic chunking by 
        splitting by double newlines, but in real scenario we'd call Ollama.
        """
        # Call to Ollama for embedding/chunking logic goes here.
        # MVP: Fallback to basic paragraph chunking if Ollama is not fully configured for this.
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        for i, para in enumerate(paragraphs):
            chunks.append(
                {
                    "paragraph_index": i,
                    "text": para,
                    "chapter_title": None,
                    "section_title": None,
                }
            )
        return chunks

chunker = SemanticChunker()
