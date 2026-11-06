"""Client LLM co cache: Ollama (model chay local, vd tren GPU Colab), API tuong thich OpenAI (Groq, Gemini, OpenRouter,
vLLM...), va MockLLM cho kiem thu."""
import hashlib
import json
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request


class LLMError(Exception):
    def __init__(self, code, msg):
        super().__init__(f"{code}: {msg}")
        self.code, self.msg = code, msg


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

    def _post(self, path, body, tries=3):
        """Goi Ollama; loi 5xx (vd model runner bi dung) -> thu lai sau 5s, 15s. Loi ket noi -> cho may chu khoi dong lai."""
        data = json.dumps(body).encode()
        for i in range(tries):
            req = urllib.request.Request(self.host + path, data, {"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=1800) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                msg = e.read().decode("utf-8", "replace")[:300]
                if e.code < 500 or i == tries - 1:
                    raise LLMError(e.code, msg) from None
                print(f"[Ollama {e.code}] {msg} -> thu lai ({i + 1}/{tries - 1})", flush=True)
            except urllib.error.URLError as e:
                if i == tries - 1:
                    raise                                   # may chu Ollama khong chay: dung, khong ghi cache
                print(f"[Ollama] khong ket noi duoc ({e.reason}) -> thu lai", flush=True)
                time.sleep(25)
            time.sleep(5 + 10 * i)

    def _key(self, prompt, opts=None):
        # opts rong -> giu nguyen khoa cu (tuong thich cache cua cac lan chay truoc)
        k = [self.model, self.options, self.think, prompt] + ([_norm(opts)] if opts else [])
        return hashlib.sha256(json.dumps(k).encode()).hexdigest()

    def cached(self, prompt, **opts):
        with self.lock:
            row = self.db.execute("SELECT v FROM cache WHERE k=?", (self._key(prompt, opts),)).fetchone()
        return json.loads(row[0]) if row else None

    def chat(self, prompt, meta=None, **opts):
        """opts (tuy chon, theo tung loi goi): temperature, seed, top_p, stop, num_predict, system."""
        key = self._key(prompt, opts)
        hit = self.cached(prompt, **opts)
        if hit:
            return hit
        o = dict(opts)
        system = o.pop("system", None)
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        body = {"model": self.model, "stream": False, "options": {**self.options, **o}, "think": self.think,
                "messages": msgs}
        t0 = time.perf_counter()
        try:
            try:
                r = self._post("/api/chat", body)
            except LLMError as e:
                if e.code != 400:
                    raise
                body.pop("think")                  # Ollama cu hoac model khong ho tro tham so think
                if not self.think:
                    body["messages"][-1]["content"] = prompt + "\n/no_think"
                r = self._post("/api/chat", body)
        except LLMError as e:
            # prompt nay lam Ollama loi lap lai: ghi nhan cau tra loi rong (phuong phap tinh sai cau nay), khong dung ca lan chay.
            # Ghi vao cache de ket qua tai lap; chay lai voi --retry-llm-errors de thu lai cac prompt nay.
            print(f"[LOI LLM] Ollama {e.code}: {e.msg[:200]} -> ghi nhan cau tra loi rong", flush=True)
            out = {"text": "", "prompt_tokens": 0, "tokens_estimated": True, "completion_tokens": 0,
                   "seconds": time.perf_counter() - t0, "llm_error": f"{e.code}: {e.msg[:300]}"}
            with self.lock:
                self.db.execute("INSERT OR REPLACE INTO cache VALUES (?,?)", (key, json.dumps(out)))
                self.db.commit()
            return out
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

    def forget_errors(self):
        """Xoa cac cau tra loi loi da ghi (de thu lai). Tra ve so dong da xoa."""
        with self.lock:
            n = self.db.execute("DELETE FROM cache WHERE v LIKE '%\"llm_error\"%'").rowcount
            self.db.commit()
        return n

    def embed(self, model, texts):
        """Embedding qua Ollama, co cache theo (model, van ban)."""
        self.db.execute("CREATE TABLE IF NOT EXISTS emb (k TEXT PRIMARY KEY, v TEXT)")
        keys = [hashlib.sha256(json.dumps([model, t]).encode()).hexdigest() for t in texts]
        out = {}
        with self.lock:
            for k in keys:
                row = self.db.execute("SELECT v FROM emb WHERE k=?", (k,)).fetchone()
                if row:
                    out[k] = json.loads(row[0])
        miss = [(k, t) for k, t in zip(keys, texts) if k not in out]
        for i in range(0, len(miss), 64):
            part = miss[i:i + 64]
            vecs = self._post("/api/embed", {"model": model, "input": [t for _, t in part]})["embeddings"]
            with self.lock:
                for (k, _), v in zip(part, vecs):
                    out[k] = v
                    self.db.execute("INSERT OR REPLACE INTO emb VALUES (?,?)", (k, json.dumps(v)))
                self.db.commit()
        return [out[k] for k in keys]


def _norm(opts):
    return sorted((k, v) for k, v in opts.items())


class OpenAICompatLLM:
    """Goi API /chat/completions kieu OpenAI. Cung giao dien voi OllamaLLM (chat, cached) va cung co che cache SQLite,
    nen chay lai se khong goi lai API. Tu cho khi bi gioi han toc do (HTTP 429) va gian cach theo --rpm."""

    def __init__(self, model, base_url, api_key=None, cache_path="llm_cache.sqlite", max_tokens=800, temperature=0.0,
                 rpm=0, seed=0, extra=None):
        self.model, self.base_url = model, base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.options = {"temperature": temperature, "max_tokens": max_tokens, "seed": seed}
        self.extra = extra or {}
        self.min_gap = 60.0 / rpm if rpm else 0.0
        self._last = 0.0
        self.db = sqlite3.connect(cache_path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT)")
        self.lock = threading.Lock()
        self.truncated = 0

    def _key(self, prompt, opts=None):
        k = ["openai", self.base_url, self.model, self.options, prompt] + ([_norm(opts)] if opts else [])
        return hashlib.sha256(json.dumps(k).encode()).hexdigest()

    def cached(self, prompt, **opts):
        with self.lock:
            row = self.db.execute("SELECT v FROM cache WHERE k=?", (self._key(prompt, opts),)).fetchone()
        return json.loads(row[0]) if row else None

    def _post(self, body, tries=8):
        req = lambda: urllib.request.Request(self.base_url + "/chat/completions", json.dumps(body).encode(),
                                             {"Content-Type": "application/json",
                                              "Authorization": f"Bearer {self.api_key}"})
        wait = 5.0
        for i in range(tries):
            if self.min_gap:
                time.sleep(max(0.0, self._last + self.min_gap - time.time()))
            self._last = time.time()
            try:
                with urllib.request.urlopen(req(), timeout=600) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                msg = e.read().decode("utf-8", "replace")[:300]
                if e.code == 400 and "seed" in body:            # mot so nha cung cap khong nhan tham so seed
                    body = {k: v for k, v in body.items() if k != "seed"}
                    continue
                if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                    ra = e.headers.get("Retry-After")
                    delay = float(ra) if ra and ra.replace(".", "").isdigit() else wait
                    print(f"[API {e.code}] cho {delay:.0f}s roi thu lai... {msg[:120]}")
                    time.sleep(delay)
                    wait = min(wait * 2, 120)
                    continue
                raise RuntimeError(f"API loi {e.code}: {msg}") from None
            except urllib.error.URLError as e:
                if i < tries - 1:
                    time.sleep(wait)
                    wait = min(wait * 2, 120)
                    continue
                raise

    def chat(self, prompt, meta=None, **opts):
        hit = self.cached(prompt, **opts)
        if hit:
            return hit
        o = dict(opts)
        system = o.pop("system", None)
        if "num_predict" in o:
            o["max_tokens"] = o.pop("num_predict")
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        body = {"model": self.model, "messages": msgs, **self.options, **self.extra, **o}
        t0 = time.perf_counter()
        r = self._post(body)
        dt = time.perf_counter() - t0
        msg = r["choices"][0]["message"]
        text = msg.get("content") or ""
        usage = r.get("usage") or {}
        out = {"text": text, "prompt_tokens": usage.get("prompt_tokens") or len(prompt) // 4,
               "tokens_estimated": not usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens") or 0,
               "seconds": dt}
        if r["choices"][0].get("finish_reason") == "length":
            self.truncated += 1
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO cache VALUES (?,?)", (self._key(prompt, opts), json.dumps(out)))
            self.db.commit()
        return out

    def embed(self, model, texts):
        raise NotImplementedError("Dung --retriever bm25 khi chay qua API")


class MockLLM:
    """Tra loi theo kich ban {(qid, stage): sql} - chi de kiem thu duong ong, khong phai mo hinh."""

    def __init__(self, script):
        self.script = script

    def chat(self, prompt, meta=None, **opts):
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
