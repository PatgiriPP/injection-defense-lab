"""OFFLINE WIRING TEST ONLY - a fake OpenAI-compatible LLM that plays a fixed
script, so the whole Omnigent lab (sub-agent dispatch, tools, policies) can be
tested without any API key. It makes no scientific decisions.

    python scripts/scripted_llm_server.py &      # listens on 127.0.0.1:8977
    OPENAI_API_KEY=x OPENAI_BASE_URL=http://127.0.0.1:8977/v1 TARGET_PROVIDER=mock \
        omnigent run lab -p "Start the study."
"""

from __future__ import annotations

import http.server
import json
import time
import uuid

SCRIPTS = {
    "LAB DIRECTOR": [
        ("log_entry", {"kind": "question", "content": "Which stacked defense x attack has the highest ASR?"}),
        ("sys_session_send", {"agent": "librarian", "title": "literature", "args": "Find 3 papers."}),
        ("sys_session_send", {"agent": "hypothesizer", "title": "hypothesis", "args": "Write a hypothesis."}),
        ("sys_session_send", {"agent": "planner", "title": "plan", "args": "Plan the next test."}),
        ("sys_session_send", {"agent": "runner", "title": "run", "args": "Run stack=D1+D3 attack=A4_german n=4"}),
        ("sys_session_send", {"agent": "analyst", "title": "analysis", "args": "Analyse the latest result."}),
        ("log_entry", {"kind": "decision", "content": "Stop (wiring test)."}),
        ("record_conclusion", {"stack": "D1+D3", "attack": "A4_german", "summary": "Wiring test conclusion."}),
    ],
    "LIBRARIAN": [("search_literature", {"query": "prompt injection defense", "k": 3}),
                  ("log_entry", {"kind": "literature", "content": "wiring test papers"})],
    "HYPOTHESIZER": [("read_log", {"last": 5}), ("list_space", {}),
                     ("log_entry", {"kind": "hypothesis", "content": "AGENT-GENERATED HYPOTHESIS: German bypasses D3."})],
    "PLANNER": [("estimate_test_value", {"stack": "D1+D3", "attack": "A4_german", "n": 4}),
                ("estimate_test_value", {"stack": "D2+D4", "attack": "A3_encoded", "n": 4}),
                ("log_entry", {"kind": "plan", "content": "CHOSEN D1+D3 x A4_german n=4"})],
    "RUNNER": [("run_experiment", {"stack": "D1+D3", "attack": "A4_german", "n": 4, "reason": "wiring test"}),
               ("run_experiment", {"stack": "D1+D3", "attack": "A9_not_approved", "n": 2, "reason": "policy test"})],
    "ANALYST": [("results_table", {"top": 5}), ("log_entry", {"kind": "analysis", "content": "wiring test analysis"})],
}


def pick_script(system: str):
    for key, script in SCRIPTS.items():
        if key in system:
            return key, script
    return "UNKNOWN", []


def next_action(body: dict):
    msgs = body["messages"]
    system = msgs[0].get("content") if msgs and msgs[0]["role"] == "system" else ""
    if isinstance(system, list):
        system = " ".join(p.get("text", "") for p in system if isinstance(p, dict))
    key, script = pick_script(system or "")
    last = msgs[-1]
    content = last.get("content") or ""
    if isinstance(content, list):
        content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
    if last["role"] == "user" and "[System: sub-agent" in content:
        return key, ("sys_read_inbox", {})
    done = [tc["function"]["name"] for m in msgs if m["role"] == "assistant" for tc in (m.get("tool_calls") or [])]
    done = [d for d in done if d != "sys_read_inbox"]
    if len(done) < len(script):
        return key, script[len(done)]
    return key, None


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        key, action = next_action(body)
        print(f"[{key}] ({body.get("model")}) -> {action[0] if action else "final text"}", flush=True)
        cid, now = f"chatcmpl-{uuid.uuid4().hex[:8]}", int(time.time())
        if action:
            delta = {"role": "assistant", "content": None, "tool_calls": [{
                "index": 0, "id": f"call_{uuid.uuid4().hex[:8]}", "type": "function",
                "function": {"name": action[0], "arguments": json.dumps(action[1])}}]}
            finish = "tool_calls"
        else:
            delta = {"role": "assistant", "content": f"{key}: done (scripted wiring test)."}
            finish = "stop"
        chunks = [
            {"id": cid, "object": "chat.completion.chunk", "created": now, "model": body["model"],
             "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
            {"id": cid, "object": "chat.completion.chunk", "created": now, "model": body["model"],
             "choices": [{"index": 0, "delta": {}, "finish_reason": finish}],
             "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}},
        ]
        if body.get("stream"):
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()
            for c in chunks:
                self.wfile.write(f"data: {json.dumps(c)}\n\n".encode())
            self.wfile.write(b"data: [DONE]\n\n")
        else:
            msg = dict(delta)
            msg.pop("index", None)
            out = {"id": cid, "object": "chat.completion", "created": now, "model": body["model"],
                   "choices": [{"index": 0, "message": msg, "finish_reason": finish}],
                   "usage": chunks[1]["usage"]}
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", 8977), H).serve_forever()
