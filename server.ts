import express, { Request, Response } from 'express';
import http from 'http';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';

const app = express();
const PORT = 3000;
const FLASK_PORT = 5001;

let flaskProcess: ChildProcess | null = null;

function startFlask() {
  console.log('[Server] Iniciando aplicación Python Flask en el puerto', FLASK_PORT);
  
  flaskProcess = spawn('python3', ['gestion_productos/run.py', '--port', String(FLASK_PORT)], {
    stdio: ['ignore', 'inherit', 'inherit'],
    cwd: process.cwd(),
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  flaskProcess.on('exit', (code, signal) => {
    console.log(`[Server] Proceso Python Flask finalizó con código ${code} / señal ${signal}`);
  });
}

startFlask();

process.on('SIGINT', () => {
  if (flaskProcess) flaskProcess.kill('SIGINT');
  process.exit();
});

process.on('SIGTERM', () => {
  if (flaskProcess) flaskProcess.kill('SIGTERM');
  process.exit();
});

// Proxy inverso transparente hacia Flask
app.use((req: Request, res: Response) => {
  const options: http.RequestOptions = {
    hostname: '127.0.0.1',
    port: FLASK_PORT,
    path: req.originalUrl || req.url,
    method: req.method,
    headers: {
      ...req.headers,
      host: `127.0.0.1:${FLASK_PORT}`,
    },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on('error', (err) => {
    console.error('[Proxy Error]:', err.message);
    res.status(502).send(`
      <!DOCTYPE html>
      <html>
        <head><title>Conectando al Gestor de Productos...</title><meta http-equiv="refresh" content="2"></head>
        <body style="font-family: system-ui, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background: #0f172a; color: white;">
          <div style="text-align: center;">
            <h2>Iniciando servidor Gestor de Productos...</h2>
            <p style="color: #94a3b8;">La aplicación Flask se está inicializando. Esta página se recargará automáticamente.</p>
          </div>
        </body>
      </html>
    `);
  });

  req.pipe(proxyReq, { end: true });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`[Server] Servidor puente activo en http://0.0.0.0:${PORT} retransmitiendo a Flask :${FLASK_PORT}`);
});
