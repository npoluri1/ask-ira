// Vercel serverless function — proxies /api/* to Railway backend
const BACKEND = process.env.API_BACKEND_URL || 'https://ask-ira-production.up.railway.app';

export default async function handler(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const target = `${BACKEND}${url.pathname}${url.search}`;

  try {
    const opts = {
      method: req.method,
      headers: { ...req.headers, host: undefined },
    };

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      opts.body = await new Promise(resolve => {
        const chunks = [];
        req.on('data', c => chunks.push(c));
        req.on('end', () => resolve(Buffer.concat(chunks)));
      });
    }

    const resp = await fetch(target, opts);
    const text = await resp.text();
    const outHeaders = {};
    for (const [k, v] of resp.headers) {
      if (!['transfer-encoding', 'content-encoding', 'connection'].includes(k.toLowerCase())) {
        outHeaders[k] = v;
      }
    }
    res.writeHead(resp.status, outHeaders).end(text);
  } catch (err) {
    console.error('Proxy error:', err.message);
    res.status(502).json({ error: 'Bad Gateway', detail: err.message });
  }
}
