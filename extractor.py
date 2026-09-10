"""
extractor.py - LLM-based structured extraction using Instructor + Groq
"""
import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
import instructor
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Pydantic Schemas (Structured Output) ───────────────────────────────────

class LeadershipMember(BaseModel):
    name: str = Field(description="Full name of the person")
    role: str = Field(description="Job title or role")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL if found")

class CompanyIntelligence(BaseModel):
    company_overview: str = Field(description="Concise 2-sentence summary of what the company does")
    target_audience: str = Field(description="Who the product is built for (ICP)")
    contact_emails: List[str] = Field(default_factory=list, description="Public/generic emails found (contact@, sales@, support@)")
    key_leadership: List[LeadershipMember] = Field(default_factory=list, description="Names, roles, LinkedIn URLs of leadership")
    data_confidence_score: float = Field(ge=0.0, le=1.0, description="Estimated quality/completeness of extracted data (0.0-1.0)")

# ─── LLM Extractor ───────────────────────────────────────────────────────────

class LLMExtractor:
    def __init__(self, model="openai/gpt-oss-120b"):
        self.model = model
        self.client = instructor.from_groq(
            Groq(api_key=os.getenv("GROQ_API_KEY")),
            mode=instructor.Mode.JSON
        )
    def extract(self, domain: str, pages: List[dict]) -> tuple: # <--- Updated return type
        combined_content = self._combine_pages(domain, pages)
        
        # 🪙 COST TRACKING: Estimate tokens (approx 1 token per 4 characters)
        estimated_input_tokens = len(combined_content) // 4
        estimated_output_tokens = 250  # rough estimate for JSON output
        total_tokens = estimated_input_tokens + estimated_output_tokens
        
        # Groq pricing is ~$0.10 per 1M tokens (or free on your tier)
        estimated_cost = (total_tokens / 1_000_000) * 0.10 
        
        logger.info(f"🤖 Sending {len(combined_content)} chars (~{estimated_input_tokens} input tokens) to LLM for {domain}...")

        try:
            result = self.client.chat.completions.create(
                model=self.model,
                response_model=CompanyIntelligence,
                max_retries=2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert business intelligence analyst. "
                            "Extract structured company information from the provided website content. "
                            "Be accurate and concise. If information is not found, leave fields empty. "
                            "Set data_confidence_score based on how much information you could extract: "
                            "0.9+ if you found overview, emails, AND leadership; "
                            "0.6-0.8 if partial; below 0.5 if very little found."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Website content from {domain}:\n\n{combined_content}"
                    }
                ]
            )

            logger.info(f"   ✅ Extraction complete. Confidence: {result.data_confidence_score}")
            logger.info(f"   🪙 Token Usage: ~{total_tokens} tokens | Est. Cost: ${estimated_cost:.5f}")
            
            # Return both the data and the cost metrics
            return result, {"tokens": total_tokens, "cost": estimated_cost}

        except Exception as e:
            logger.error(f"   ❌ LLM extraction failed for {domain}: {str(e)}")
            fallback = CompanyIntelligence(
                company_overview=f"Failed to extract data for {domain}",
                target_audience="Unknown", contact_emails=[], key_leadership=[], data_confidence_score=0.0
            )
            return fallback, {"tokens": 0, "cost": 0.0}

    def _combine_pages(self, domain: str, pages: List[dict]) -> str:
        """Combine all scraped pages into a single document, capped for token safety."""
        combined = f"=== DOMAIN: {domain} ===\n\n"

        for page in pages:
            combined += f"--- Page: {page['url']} ---\n{page['content']}\n\n"

        # Token safety: cap total content at 8000 chars
        if len(combined) > 8000:
            combined = combined[:8000] + "\n\n[Content truncated for token optimization]"

        return combined