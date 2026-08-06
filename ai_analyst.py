import os
import json
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from models import AIAnalysis
from config import Config
from utils import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a senior Indian equity research analyst.
You analyse NSE corporate announcements.
Your analysis will be used by investors.
You must never invent facts.
Every statement must come directly from the supplied announcement.
Preserve every financial figure exactly.
Preserve every percentage exactly.
Preserve every date exactly.
If information does not exist, state that it is unavailable.
Never guess.

Read the entire announcement.
Determine:
1. Document Type (e.g., Quarterly Results, Government Contract, Railway Contract, Dividend, Buyback, Bonus Issue, Merger, Scheme of Amalgamation, Capacity Expansion, Rights Issue, Investor Presentation, Board Meeting, Compliance, AGM, General Disclosure, etc.)
2. Primary Event (Only ONE.)
3. Secondary Events (Only if clearly supported.)
4. Market Importance (Very High, High, Medium, Low, Very Low)
5. Catalyst Score (Return 0–100. The score should consider Revenue impact, Future earnings, Business significance, Size of transaction, Regulatory impact, Shareholder impact, Financial impact, Long-term impact, Execution risk, Probability of completion)
6. Explain the Catalyst Score (Provide a complete breakdown.)
7. Key Financial Numbers (Extract Revenue, PAT, EBITDA, Margins, Contract Value, Dividend, Buyback, Bonus Ratio, Split Ratio, Fund Raising, Acquisition Value, Market Impact, Everything important.)
8. Risk Analysis (Explain Execution Risk, Regulatory Risk, Financial Risk, Operational Risk, Customer Concentration, Approval Risk, Litigation Risk. Only if supported.)
9. Opportunities (Explain positive outcomes.)
10. Investment Impact (Choose Very Bullish, Bullish, Neutral, Bearish, Very Bearish. Explain why.)
11. One Sentence Summary (Maximum 25 words.)
12. Executive Summary (Maximum 250 words. Written for retail investors. Simple English.)

Return STRICT JSON.
Every field should be structured.
No markdown.
No explanations.
No free text outside JSON."""

class AIAnalyst:
    def __init__(self):
        token = Config.NVIDIA_API_KEY
        if not token:
            logger.warning("NVIDIA_API_KEY is not set. AI Analyst will fail.")
            
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=token
        )
        self.model_name = "nvidia/nemotron-3-ultra-550b-a55b"

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        reraise=True
    )
    def analyze_announcement(self, text: str) -> AIAnalysis:
        logger.info(f"Sending document to {self.model_name} for analysis ({len(text)} chars)...")
        
        try:
            # Provide the schema structure to guide the model
            schema_example = AIAnalysis.model_json_schema()
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT + f"\n\nJSON Schema to follow exactly:\n{json.dumps(schema_example)}"},
                    {"role": "user", "content": f"Analyze the following NSE announcement:\n\n{text}"}
                ],
                temperature=0.0,
                top_p=0.95,
                max_tokens=16384,
                extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":16384},
                stream=True
            )
            
            raw_content = ""
            reasoning_content = ""
            for chunk in completion:
                if not chunk.choices:
                    continue
                reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                if reasoning:
                    reasoning_content += reasoning
                
                content = chunk.choices[0].delta.content
                if content is not None:
                    raw_content += content
                    
            if reasoning_content:
                logger.info(f"Model reasoning length: {len(reasoning_content)} characters")
                
            raw_content = raw_content.strip()
            
            # Remove markdown formatting if present
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            elif raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
                
            raw_content = raw_content.strip()
            
            parsed_data = json.loads(raw_content)
            analysis = AIAnalysis(**parsed_data)
            return analysis
        except Exception as e:
            logger.error(f"Error calling GitHub Models API: {e}")
            raise
