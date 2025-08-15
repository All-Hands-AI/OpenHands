#!/usr/bin/env node
/*
Minimal @google/genai script to mirror Gemini CLI baseline and log raw request payloads.

Usage:
  node experiments/genai_minimal.js \
    --model gemini-2.5-pro \
    --api-key $GEMINI_API_KEY \
    --prompt "Hello" \
    --system "You are a helpful assistant." \
    --with-tools \
    --temperature 0 \
    --top-p 1 \
    --max-output-tokens 1024 \
    --log-dir /tmp/gemini-node-logs

Notes:
- If model starts with "gemini-2.5", we set thinkingConfig: { includeThoughts: true }.
- Tools are passed using functionDeclarations under tools: [{ functionDeclarations: [...] }].
- Logs HTTP request: method, url, headers (Authorization masked), and JSON body into log-dir.
*/

const fs = require('fs');
const path = require('path');
const { randomUUID } = require('crypto');

async function main() {
  // Simple arg parsing
  const args = process.argv.slice(2);
  const arg = (name, def = undefined) => {
    const i = args.findIndex((a) => a === `--${name}`);
    if (i !== -1 && i + 1 < args.length) return args[i + 1];
    return def;
  };
  const hasFlag = (name) => args.includes(`--${name}`);

  const model = arg('model', process.env.MODEL || 'gemini-2.5-pro');
  const apiKey = arg('api-key', process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY);
  const prompt = arg('prompt', 'Say hello.');
  const system = arg('system', 'You are a helpful assistant.');
  const withTools = hasFlag('with-tools');
  const temperature = parseFloat(arg('temperature', '0'));
  const topP = parseFloat(arg('top-p', '1'));
  const maxOutputTokens = parseInt(arg('max-output-tokens', '1024'), 10);
  const logDir = arg('log-dir', null);

  if (!apiKey) {
    console.error('Missing --api-key or GEMINI_API_KEY/GOOGLE_API_KEY');
    process.exit(2);
  }

  if (logDir) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  // Ensure global fetch exists (Node 18+). If not, polyfill via undici.
  try {
    if (typeof globalThis.fetch !== 'function') {
      const undici = require('undici');
      globalThis.fetch = undici.fetch;
    }
  } catch (_) {
    // ignore
  }

  // Intercept fetch to log request payload
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input, init = {}) => {
    const url = typeof input === 'string' ? input : (input && input.url ? input.url : String(input));
    const method = (init.method || 'GET').toUpperCase();
    const headers = Object.fromEntries(Object.entries(init.headers || {}).map(([k, v]) => [k.toLowerCase(), String(v)]));
    if (headers['authorization']) headers['authorization'] = 'Bearer ***';

    let bodyText = undefined;
    if (init.body && typeof init.body === 'string') {
      bodyText = init.body;
    } else if (init.body && Buffer.isBuffer(init.body)) {
      bodyText = init.body.toString('utf8');
    }

    const shouldLog = logDir && method === 'POST' && url.includes('generateContent');
    const reqId = randomUUID();

    if (shouldLog) {
      const out = {
        ts: Date.now(),
        reqId,
        method,
        url,
        headers,
        body: (() => { try { return bodyText ? JSON.parse(bodyText) : null; } catch { return bodyText; } })(),
      };
      fs.writeFileSync(path.join(logDir, `genai_request_${reqId}.json`), JSON.stringify(out, null, 2));
    }

    const t0 = Date.now();
    const res = await originalFetch(input, init);
    const dt = Date.now() - t0;

    if (shouldLog) {
      let text = null;
      try { text = await res.clone().text(); } catch { /* ignore */ }
      const out = {
        ts: Date.now(),
        reqId,
        status: res.status,
        duration_ms: dt,
        headers: Object.fromEntries(res.headers.entries()),
        body: (() => { try { return text ? JSON.parse(text) : null; } catch { return text; } })(),
      };
      fs.writeFileSync(path.join(logDir, `genai_response_${reqId}.json`), JSON.stringify(out, null, 2));
    }

    return res;
  };

  // Dynamically import ESM @google/genai
  const { GoogleGenAI } = await import('@google/genai');

  const genAI = new GoogleGenAI({
    apiKey,
    httpOptions: { headers: { 'User-Agent': 'OpenHandsGenAI-Minimal/1.0' } },
  });

  // Build request
  const contents = [
    system ? { role: 'user', parts: [{ text: `SYSTEM: ${system}` }] } : null,
    { role: 'user', parts: [{ text: prompt }] },
  ].filter(Boolean);

  const config = {
    temperature,
    topP,
    maxOutputTokens,
  };

  if (/^gemini-2\.5/.test(model) || /gemini-2\.5/.test(model)) {
    config.thinkingConfig = { includeThoughts: true };
  }

  if (system) {
    // Prefer explicit systemInstruction like CLI
    config.systemInstruction = system;
  }

  let tools = undefined;
  if (withTools) {
    tools = [
      {
        functionDeclarations: [
          {
            name: 'echo',
            description: 'Echo the provided text',
            parameters: {
              type: 'OBJECT',
              properties: {
                text: { type: 'STRING' },
              },
              required: ['text'],
            },
          },
        ],
      },
    ];
  }

  const req = { model, contents, config };
  if (tools) {
    req.tools = tools;
  }

  const t0 = Date.now();
  const resp = await genAI.models.generateContent(req);
  const dt = (Date.now() - t0) / 1000;
  const text = resp?.candidates?.[0]?.content?.parts?.map((p) => p.text).filter(Boolean).join('\n');
  console.log(JSON.stringify({ model, latency_sec: dt, text: String(text || '').slice(0, 200) }));
}

main().catch((err) => {
  console.error('Error:', err?.stack || String(err));
  process.exit(1);
});
