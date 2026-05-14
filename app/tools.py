# OpenAI / Ollama tool format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "classify_ticket",
            "description": "Assign exactly ONE category from the allowed list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["billing", "technical", "account", "shipping", "general"],
                    }
                },
                "required": ["category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_sentiment",
            "description": (
                "Score customer frustration on a 1-5 scale "
                "where 1=calm and 5=very angry."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "score": {"type": "integer", "minimum": 1, "maximum": 5},
                    "evidence": {
                        "type": "string",
                        "description": "Quote or paraphrase justifying the score",
                    },
                },
                "required": ["score", "evidence"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_response",
            "description": (
                "Write the reply to the customer following SOPs and engagement rules. "
                "Call this LAST, after classifying and scoring sentiment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reply_md": {
                        "type": "string",
                        "description": "Markdown reply to the customer",
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["professional_warm", "apologetic", "neutral_factual"],
                    },
                    "sop_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "IDs of SOP chunks that informed this reply",
                    },
                },
                "required": ["reply_md", "tone", "sop_ids"],
            },
        },
    },
]
