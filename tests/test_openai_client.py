"""Kiem thu client OpenAI (khong goi API that): server gia lap /chat/completions tren localhost.
Chay: python tests/test_openai_client.py"""
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vsql.llm import OpenAICompatLLM, find_api_key  # noqa: E402

SEEN = []
MODE = {"v": "new_model"}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append((self.headers.get("Authorization"), body))
        if MODE["v"] == "quota":
            return self._send(429, {"error": {"code": "insufficient_quota", "message": "You exceeded your current quota"}})
        if MODE["v"] == "badkey":
            return self._send(401, {"error": {"message": "Incorrect API key provided"}})
        if MODE["v"] == "new_model" and "max_tokens" in body:      # kieu gpt-5.x / o-series
            return self._send(400, {"error": {"message": "Unsupported parameter: 'max_tokens' is not supported with this "
                                              "model. Use 'max_completion_tokens' instead."}})
        if MODE["v"] == "new_model" and body.get("temperature") not in (None, 1):
            return self._send(400, {"error": {"message": "Unsupported value: 'temperature' does not support 0 with this "
                                              "model. Only the default (1) value is supported."}})
        self._send(200, {"choices": [{"message": {"content": "```sql\nSELECT 1\n```"}, "finish_reason": "stop"}],
                         "usage": {"prompt_tokens": 11, "completion_tokens": 3}})


srv = HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_port}/v1"
tmp = Path(tempfile.mkdtemp())

# 1. model moi: tu doi max_tokens -> max_completion_tokens, bo temperature; khoa cache khong doi
llm = OpenAICompatLLM("gpt-x", url, "sk-test", str(tmp / "c.sqlite"))
r = llm.chat("q1")
assert r["text"].startswith("```sql") and r["prompt_tokens"] == 11
last = SEEN[-1][1]
assert SEEN[-1][0] == "Bearer sk-test" and "max_completion_tokens" in last and "max_tokens" not in last
assert "temperature" not in last and last["max_completion_tokens"] == 800
n = len(SEEN)
assert llm.chat("q1") == r and len(SEEN) == n                       # cache: khong goi lai
llm.chat("q2")
assert len(SEEN) == n + 1                                           # da ghi nho cach doi tham so: 1 lan goi
# 2. model cu (gpt-4o-mini...): giu temperature=0, max_tokens=800 nhu paper
MODE["v"] = "old_model"
llm2 = OpenAICompatLLM("gpt-old", url, "sk-test", str(tmp / "c2.sqlite"))
llm2.chat("q1")
assert SEEN[-1][1]["temperature"] == 0.0 and SEEN[-1][1]["max_tokens"] == 800
# 3. het tien / key sai: dung ngay, khong thu lai 8 lan
for mode in ["quota", "badkey"]:
    MODE["v"] = mode
    n = len(SEEN)
    try:
        llm2.chat("q-" + mode)
        raise AssertionError("phai dung")
    except SystemExit as e:
        assert len(SEEN) == n + 1, mode
        assert ("het tien" in str(e)) if mode == "quota" else ("401" in str(e))
# 4. reasoning_effort nam trong khoa cache
MODE["v"] = "old_model"
a = OpenAICompatLLM("m", url, "k", str(tmp / "c3.sqlite"))
b = OpenAICompatLLM("m", url, "k", str(tmp / "c3.sqlite"), extra={"reasoning_effort": "low"})
assert a._key("p") != b._key("p")
b.chat("p")
assert SEEN[-1][1]["reasoning_effort"] == "low"
# 5. tim API key: bien moi truong > .env
d = tmp / "repo"
d.mkdir()
(d / ".env").write_text("# cmt\nexport OPENAI_API_KEY='sk-from-dotenv'\n")
os.environ.pop("ZZ_KEY", None)
assert find_api_key("OPENAI_API_KEY_KHONG_CO", dotenv_dirs=(d,)) == ""
os.environ.pop("OPENAI_API_KEY", None)
assert find_api_key("OPENAI_API_KEY", dotenv_dirs=(d,)) == "sk-from-dotenv"
os.environ["OPENAI_API_KEY"] = "sk-env"
assert find_api_key("OPENAI_API_KEY", dotenv_dirs=(d,)) == "sk-env"
srv.shutdown()
print("DAT: client OpenAI")
