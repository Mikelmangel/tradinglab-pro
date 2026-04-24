"""TradingLab Pro — AI Assistant (Claude API integration)."""
from __future__ import annotations
import json, re
import requests

SYSTEM_PROMPT = """Eres TradingLab AI, un asistente experto en trading algorítmico, análisis técnico y backtesting integrado en TradingLab Pro.

Tienes acceso a los resultados del backtest actual (métricas, trades, rendimiento anual).
Ayudas a:
1. Analizar estrategias: identificar debilidades (low Sharpe, high DD, over-optimization, etc.)
2. Generar código Python de estrategias completas listas para copiar en el editor
3. Sugerir mejoras concretas: filtros, stops, position sizing
4. Explicar indicadores técnicos y cuándo usarlos
5. Interpretar resultados de walk-forward y Monte Carlo
6. Detectar overfitting y look-ahead bias

Cuando generes código de estrategia, usa SIEMPRE este formato exacto:
```python
def generate_signals(data, fast_period=10, slow_period=30, **params):
    # data: DataFrame con Open, High, Low, Close, Volume
    # Retorna: pd.Series con 1=compra, -1=venta, 0=mantener
    import pandas as pd
    import numpy as np
    # ... código ...
    return signals
```

Sé conciso, práctico y directo. Responde en español."""

class AIAssistant:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.history = []

    def set_api_key(self, key: str):
        self.api_key = key

    def set_context(self, metrics: dict = None, annual: dict = None, code: str = ""):
        """Inject current backtest context."""
        ctx_parts = []
        if metrics:
            ctx_parts.append("=== MÉTRICAS DEL BACKTEST ACTUAL ===")
            for k,v in list(metrics.items())[:25]:
                if not k.startswith('──'): ctx_parts.append(f"  {k}: {v}")
        if annual:
            ctx_parts.append("\n=== RENDIMIENTO ANUAL ===")
            for row in annual:
                ctx_parts.append(f"  {row}")
        if code:
            ctx_parts.append(f"\n=== CÓDIGO ESTRATEGIA ACTUAL ===\n{code[:1500]}")
        if ctx_parts:
            ctx_msg = "\n".join(ctx_parts)
            self.history = [h for h in self.history if not h.get('_ctx')]
            self.history.insert(0, {
                "role": "user", "content": f"Contexto del backtest:\n{ctx_msg}", "_ctx": True
            })
            self.history.insert(1, {"role": "assistant", "content": "Entendido. Tengo acceso al contexto del backtest actual. ¿En qué puedo ayudarte?", "_ctx": True})

    def chat(self, user_msg: str) -> str:
        if not self.api_key:
            return "⚠️ Configura tu API key de Anthropic en Configuración → API Key para usar el asistente IA.\n\nObténla gratis en: https://console.anthropic.com"

        self.history.append({"role": "user", "content": user_msg})

        messages = [{"role": m["role"], "content": m["content"]}
                    for m in self.history if m.get("role") in ("user","assistant")]

        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-opus-4-6",
                    "max_tokens": 2048,
                    "system": SYSTEM_PROMPT,
                    "messages": messages,
                },
                timeout=60,
            )
            if resp.status_code != 200:
                err = resp.json().get('error', {}).get('message', resp.text)
                self.history.pop()
                return f"❌ Error API ({resp.status_code}): {err}"

            content = resp.json()['content'][0]['text']
            self.history.append({"role": "assistant", "content": content})
            return content
        except requests.exceptions.Timeout:
            self.history.pop()
            return "⏱️ Timeout. Intenta de nuevo."
        except Exception as e:
            self.history.pop()
            return f"❌ Error: {e}"

    def clear_history(self):
        self.history = [h for h in self.history if h.get('_ctx')]

    def extract_code(self, text: str) -> str | None:
        m = re.search(r'```python\n(.*?)```', text, re.DOTALL)
        return m.group(1).strip() if m else None
