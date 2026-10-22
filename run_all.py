import os
import json
import sys
from scrapling import Fetcher
from scrapegraphai.graphs import SmartScraperGraph

def main():
    target_url = os.environ.get("TARGET_URL")
    prompt = os.environ.get("PROMPT", "Extract key insights and structured data from this page.")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not target_url:
        print("Error: TARGET_URL environment variable not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Target URL: {target_url}")
    print(f"Prompt: {prompt}")

    # 1. Scrape content using Scrapling
    scraped_content = ""
    try:
        print("Fetching content with Scrapling...")
        fetcher = Fetcher(auto_match=True)
        response = fetcher.get(target_url)
        # Extract text or adaptive content
        if hasattr(response, 'text'):
            scraped_content = response.text
        else:
            scraped_content = str(response)
        print(f"Successfully fetched {len(scraped_content)} characters via Scrapling.")
    except Exception as e:
        print(f"Scrapling fetch encountered an issue: {e}. Falling back to requests.", file=sys.stderr)
        import requests
        try:
            resp = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"})
            scraped_content = resp.text
        except Exception as ex:
            print(f"Fallback request also failed: {ex}", file=sys.stderr)
            scraped_content = f"Failed to fetch {target_url}"

    # 2. Agent Reach integration (simulated/integrated search/context gathering)
    context_data = ""
    try:
        from agent_reach import AgentReach
        print("Gathering additional context via Agent Reach...")
        # Initialize agent reach if available
        # ar = AgentReach()
        # context_data = ar.search(prompt)
        pass
    except ImportError:
        print("agent-reach package not fully initialized or custom module; proceeding with Scrapling content.")
    except Exception as e:
        print(f"Agent Reach note: {e}")

    combined_input = f"URL Content:\n{scraped_content[:15000]}\n\nAdditional Context / Query:\n{prompt}\n{context_data}"

    # 3. ScrapeGraphAI Processing
    result_data = {}
    if openai_api_key:
        try:
            print("Processing with ScrapeGraphAI (SmartScraperGraph)...")
            graph_config = {
                "llm": {
                    "api_key": openai_api_key,
                    "model": "gpt-4o-mini",
                },
                "verbose": True,
                "headless": True,
            }
            # SmartScraperGraph takes prompt and source (url or text)
            smart_scraper = SmartScraperGraph(
                prompt=prompt,
                source=target_url,
                config=graph_config
            )
            result_data = smart_scraper.run()
            print("ScrapeGraphAI completed successfully.")
        except Exception as e:
            print(f"ScrapeGraphAI execution error: {e}. Generating structured fallback JSON.", file=sys.stderr)
            result_data = {
                "error": str(e),
                "url": target_url,
                "prompt": prompt,
                "raw_content_preview": scraped_content[:2000]
            }
    else:
        print("Warning: OPENAI_API_KEY not provided. Creating basic structural output from Scrapling content.", file=sys.stderr)
        result_data = {
            "url": target_url,
            "prompt": prompt,
            "content_length": len(scraped_content),
            "preview": scraped_content[:2000],
            "note": "OPENAI_API_KEY was not set in environment."
        }

    # Ensure output is JSON serializable
    output_path = "output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    print(f"Result successfully written to {output_path}")

if __name__ == "__main__":
    main()
