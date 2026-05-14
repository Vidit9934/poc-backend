from app.tools import TOOLS

REQUIRED_NAMES = {"classify_ticket", "score_sentiment", "draft_response"}


def test_all_tools_present():
    names = {t["function"]["name"] for t in TOOLS}
    assert names == REQUIRED_NAMES


def test_tools_have_required_fields():
    for tool in TOOLS:
        assert "type" in tool
        assert tool["type"] == "function"
        fn = tool["function"]
        assert "name" in fn
        assert "description" in fn
        assert "parameters" in fn
        params = fn["parameters"]
        assert "required" in params
        assert "properties" in params


def test_classify_ticket_enum():
    fn = next(t["function"] for t in TOOLS if t["function"]["name"] == "classify_ticket")
    enum = fn["parameters"]["properties"]["category"]["enum"]
    assert set(enum) == {"billing", "technical", "account", "shipping", "general"}


def test_score_sentiment_bounds():
    fn = next(t["function"] for t in TOOLS if t["function"]["name"] == "score_sentiment")
    score_schema = fn["parameters"]["properties"]["score"]
    assert score_schema["minimum"] == 1
    assert score_schema["maximum"] == 5


def test_draft_response_required_fields():
    fn = next(t["function"] for t in TOOLS if t["function"]["name"] == "draft_response")
    assert set(fn["parameters"]["required"]) == {"reply_md", "tone", "sop_ids"}
