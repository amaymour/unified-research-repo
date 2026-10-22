#!/usr/bin/env python3
import sys
import json
import subprocess
import os

def send_json(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "initialize":
            send_json({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "research-workflow-mcp",
                        "version": "1.0.0"
                    }
                }
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            send_json({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "run_research_workflow",
                            "description": "Execute the unified research workflow combining Scrapling and ScrapeGraphAI on a target URL with a prompt.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "type": "string",
                                        "description": "The target URL to scrape and research."
                                    },
                                    "prompt": {
                                        "type": "string",
                                        "description": "The research prompt or instructions for structured data extraction."
                                    }
                                },
                                "required": ["url", "prompt"]
                            }
                        }
                    ]
                }
            })
        elif method == "tools/call":
            params = msg.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})

            if name == "run_research_workflow":
                url = arguments.get("url")
                prompt = arguments.get("prompt")

                env = os.environ.copy()
                if url:
                    env["TARGET_URL"] = url
                if prompt:
                    env["PROMPT"] = prompt

                try:
                    script_path = os.path.join(os.path.dirname(__file__), "run_all.py")
                    result = subprocess.run(
                        [sys.executable, script_path],
                        capture_output=True,
                        text=True,
                        env=env,
                        timeout=120
                    )

                    output_json_path = os.path.join(os.path.dirname(__file__), "output.json")
                    workflow_output = {}
                    if os.path.exists(output_json_path):
                        with open(output_json_path, "r", encoding="utf-8") as f:
                            workflow_output = json.load(f)

                    content = [
                        {
                            "type": "text",
                            "text": f"Workflow executed successfully.\nStdout:\n{result.stdout}\n\nOutput JSON:\n{json.dumps(workflow_output, indent=2)}"
                        }
                    ]
                except Exception as e:
                    content = [
                        {
                            "type": "text",
                            "text": f"Workflow execution failed: {str(e)}"
                        }
                    ]

                send_json({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": content
                    }
                })
            else:
                send_json({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {name}"
                    }
                })
        else:
            if msg_id is not None:
                send_json({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32603,
                        "message": f"Method not supported: {method}"
                    }
                })

if __name__ == "__main__":
    main()
