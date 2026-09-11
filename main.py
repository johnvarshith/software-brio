"""
main.py - Orchestrates the full pipeline: Scrape → Extract → Save
"""
import json
import logging
import time
from datetime import datetime
from scraper import WebScraper
from extractor import LLMExtractor
from search_enrichment import SearchEnricher

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────────────────────
TARGET_DOMAINS = [
    "postman.com",
    "supabase.com",
    "vapi.ai"
]

OUTPUT_FILE = "output/output.json"

# ─── Main Pipeline ───────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=" * 60)
    logger.info("AI Lead Enrichment Agent - Starting")
    logger.info("=" * 60)

    results = []
    extractor = LLMExtractor(model="openai/gpt-oss-120b")
    enricher = SearchEnricher()  # <--- NEW: Initialize the search enricher

    # Use scraper as context manager (handles browser cleanup)
    with WebScraper(headless=True, max_subpages=4) as scraper:

        for domain_index, domain in enumerate(TARGET_DOMAINS):
            logger.info(f"\n{'─' * 40}")
            logger.info(f"Processing: {domain}")
            logger.info(f"{'─' * 40}")

            try:
                # Step 1: Scrape
                scrape_result = scraper.scrape_domain(domain)

                if scrape_result["error"]:
                    logger.warning(f"   ⚠️ Scrape error: {scrape_result['error']}")
                    results.append({"domain": domain, "error": scrape_result["error"], "data": None})
                    continue

                # Step 2: Extract with LLM
                intelligence, usage_stats = extractor.extract(domain, scrape_result["pages"])

                # Step 2.5: BONUS - Search Enrichment
                logger.info(f"Running Search Enrichment for {domain}...")
                intelligence = enricher.enrich_leadership(intelligence, domain)

                # Step 3: Store result
                results.append({
                    "domain": domain,
                    "error": None,
                    "data": intelligence.model_dump(),
                    "usage": usage_stats
                })

                logger.info(f"   ✅ {domain} completed successfully")

            except Exception as e:
                logger.error(f"   ❌ Unexpected error for {domain}: {str(e)}")
                results.append({"domain": domain, "error": str(e), "data": None})
            finally:
                if domain_index < len(TARGET_DOMAINS) - 1:
                    time.sleep(1)

    # ─── Save Results ────────────────────────────────────────────────────────
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_domains": len(TARGET_DOMAINS),
        "successful": sum(1 for r in results if r["data"] is not None),
        "failed": sum(1 for r in results if r["data"] is None),
        "results": results
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Summary: {output['successful']}/{output['total_domains']} domains processed")
    logger.info(f"Results saved to: {OUTPUT_FILE}")
    logger.info(f"{'=' * 60}")
if __name__ == "__main__":
    main()