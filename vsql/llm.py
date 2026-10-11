"""Client Ollama (qwen3 chay local) co cache; va MockLLM cho kiem thu."""
import hashlib
import json
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request


class OllamaLLM:
    def __init__(self, model="qwen3:8b", host="http://localhost:11434", cache_path="llm_cache.sqlite",
                 num_ctx=16384, num_predict=800, think=False, seed=0):
        self.model, self.host = model, host.rstrip("/")
        self.options = {"temperature": 0, "seed": seed, "num_ctx": num_ctx, "num_predict": num_predict}
        self.think = think
        self.db = sqlite3.connect(cache_path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT)")
        self.truncated = 0
        self.lock = threading.Lock()

    def _post(self, path, body):
        req = urllib.request.Request(self.host + path, json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=1800) as r:
            return json.loads(r.read())

    def _key(self, prompt):
        return hashlib.sha256(json.dumps([self.model, self.options, self.think, prompt]).encode()).hexdigest()

    def cached(self, prompt):
        with self.lock:
            row = self.db.execute("SELECT v FROM cache WHERE k=?", (self._key(prompt),)).fetchone()
        return json.loads(row[0]) if row else None

    def chat(self, prompt, meta=None):
        key = self._key(prompt)
        hit = self.cached(prompt)
        if hit:
            return hit
        body = {"model": self.model, "stream": False, "options": self.options, "think": self.think,
                "messages": [{"role": "user", "content": prompt}]}
        t0 = time.perf_counter()
        try:
            r = self._post("/api/chat", body)
        except urllib.error.HTTPError as e:
            if e.code != 400:
                raise
            body.pop("think")                      # Ollama cu hoac model khong ho tro tham so think
            if not self.think:
                body["messages"][0]["content"] = prompt + "\n/no_think"
            r = self._post("/api/chat", body)
        dt = time.perf_counter() - t0
        pt = r.get("prompt_eval_count") or 0
        out = {"text": r["message"]["content"], "prompt_tokens": pt or len(prompt) // 4,
               "tokens_estimated": not pt, "completion_tokens": r.get("eval_count") or 0, "seconds": dt}
        if pt >= self.options["num_ctx"] - 8:
            self.truncated += 1
            print(f"[CANH BAO] prompt cham nguong num_ctx={self.options['num_ctx']}: bi cat. Tang --num-ctx.")
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO cache VALUES (?,?)", (key, json.dumps(out)))
            self.db.commit()
        return out

    def embed(self, model, texts):
        return self._post("/api/embed", {"model": model, "input": texts})["embeddings"]


class MockLLM:
    """Tra loi theo kich ban {(qid, stage): sql} - chi de kiem thu duong ong, khong phai mo hinh."""

    def __init__(self, script):
        self.script = script

    def chat(self, prompt, meta=None):
        sql = self.script.get((meta["qid"], meta["stage"]), "")
        return {"text": f"```sql\n{sql}\n```", "prompt_tokens": len(prompt) // 4, "tokens_estimated": True,
                "completion_tokens": len(sql) // 4, "seconds": 0.0}


def extract_sql(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.findall(r"```(?:sql|sqlite)?\s*(.*?)```", text, flags=re.S | re.I)
    sql = m[-1] if m else text
    m = re.search(r"\b(WITH|SELECT)\b", sql, re.I)
    if not m:
        return ""
    return sql[m.start():].strip().rstrip(';').strip()
