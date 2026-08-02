from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from utils import get_logger

logger = get_logger(__name__)

class SumySummarizer:
    def __init__(self):
        self.summarizer = LexRankSummarizer()

    def summarize(self, text: str, sentences_count: int = 4) -> str:
        if not text or len(text.strip()) < 50:
            return ""
            
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            summary = self.summarizer(parser.document, sentences_count)
            return " ".join(str(sentence) for sentence in summary)
        except Exception as e:
            logger.error(f"Error during Sumy summarization: {e}")
            return ""
