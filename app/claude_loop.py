import httpx

from .config import settings
from .prompts import build_system_prompt
from .tools import TOOLS


def run_loop(
    ticket: dict,
    sops: list[dict],
    max_turns: int = 4,
) -> tuple[list[dict], dict | None]:
    system_prompt = build_system_prompt(ticket, sops)
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Process this ticket."},
    ]

    collected_tool_calls: list[dict] = []
    final_draft: dict | None = None

    with httpx.Client(timeout=120.0) as client:
        for _ in range(max_turns):
            response = client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_llm_model,
                    "messages": messages,
                    "tools": TOOLS,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()

            assistant_msg = data["message"]
            tool_calls_raw = assistant_msg.get("tool_calls") or []

            tool_result_msgs: list[dict] = []
            for tc in tool_calls_raw:
                fn = tc["function"]
                # Ollama returns arguments as a dict (not a JSON string)
                args = fn["arguments"] if isinstance(fn["arguments"], dict) else {}
                collected_tool_calls.append({"tool": fn["name"], "input": args})
                if fn["name"] == "draft_response":
                    final_draft = args
                tool_result_msgs.append({"role": "tool", "content": "ok"})

            if final_draft or not tool_calls_raw:
                break

            messages.append(assistant_msg)
            messages.extend(tool_result_msgs)

    return collected_tool_calls, final_draft
