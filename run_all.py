import os
import json
import sys
from openai import OpenAI

def main():
    target_url = os.environ.get("TARGET_URL")
    prompt = os.environ.get("PROMPT", "Extract key insights and structured data from this page.")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not target_url:
        print("Error: TARGET_URL environment variable not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Target URL: {target_url}")
    print(f"Prompt: {prompt}")

    # 1. Fetch content using Scrapling (with requests fallback)
    scraped_content = ""
    try:
        print("Fetching content with Scrapling...")
        from scrapling import Fetcher
        fetcher = Fetcher(auto_match=True)
        response = fetcher.get(target_url)
        if hasattr(response, 'text'):
            scraped_content = response.text
        else:
            scraped_content = str(response)
        print(f"Successfully fetched {len(scraped_content)} characters via Scrapling.")
    except Exception as e:
        print(f"Scrapling fetch note: {e}. Falling back to requests.", file=sys.stderr)
        import requests
        try:
            resp = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            scraped_content = resp.text
            print(f"Successfully fetched {len(scraped_content)} characters via requests fallback.")
        except Exception as ex:
            print(f"Fallback request also failed: {ex}", file=sys.stderr)
            scraped_content = f"Failed to fetch {target_url}: {ex}"

    # 2. Process with OpenAI API directly
    result_data = {}
    if openai_api_key:
        try:
            print("Processing with OpenAI API...")
            client = OpenAI(api_key=openai_api_key)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert web research and data extraction assistant. Analyze the provided webpage content according to the user prompt and return clean, structured JSON or Markdown insights."},
                    {"role": "user", "content": f"URL: {target_url}\n\nPrompt: {prompt}\n\nPage Content:\n{scraped_content[:12000]}"}
                ],
                response_format={"type": "json_object"}
            )
            content_res = completion.choices[0].message.content
            try:
                result_data = json.loads(content_res)
            except Exception:
                result_data = {"raw_analysis": content_res}
            print("OpenAI processing completed successfully.")
        except Exception as e:
            print(f"OpenAI API execution error: {e}", file=sys.stderr)
            result_data = {
                "error": str(e),
                "url": target_url,
                "prompt": prompt,
                "raw_content_preview": scraped_content[:2000]
            }
    else:
        print("Warning: OPENAI_API_KEY not provided. Providing structural output from scraped content.", file=sys.stderr)
        result_data = {
            "url": target_url,
            "prompt": prompt,
            "content_length": len(scraped_content),
            "preview": scraped_content[:2000],
            "note": "OPENAI_API_KEY was not set in environment."
        }

    output_path = "output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    print(f"Result successfully written to {output_path}")

if __name__ == "__main__":
    main()
