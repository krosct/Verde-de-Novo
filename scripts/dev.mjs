import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import net from "node:net";

const viteBin = join(process.cwd(), "node_modules", ".bin", "vite");
const pythonBin = join(homedir(), ".venv", "bin", "python");
const API_START_PORT = 8000;
const PORT_ATTEMPTS = 20;

function findFreePort(startPort, attempts) {
  return new Promise((resolve, reject) => {
    let port = startPort;
    const attempt = () => {
      if (port >= startPort + attempts || port > 65535) {
        reject(new Error(`No free port found between ${startPort} and ${startPort + attempts - 1}.`));
        return;
      }
      const probe = net.createServer();
      probe.unref();
      probe.once("error", () => {
        port += 1;
        attempt();
      });
      probe.listen(port, "127.0.0.1", () => {
        const chosen = port;
        probe.close(() => resolve(chosen));
      });
    };
    attempt();
  });
}

const children = [];

function start(command, args, extraEnv) {
  const child = spawn(command, args, { stdio: "inherit", env: { ...process.env, ...extraEnv } });
  children.push(child);
  child.on("exit", (code) => shutdown(code ?? 0));
  child.on("error", (error) => {
    console.error(`Failed to start ${command}:`, error.message);
    shutdown(1);
  });
  return child;
}

function shutdown(code) {
  for (const child of children) {
    if (!child.killed) {
      child.kill("SIGTERM");
    }
  }
  process.exit(code);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

const apiPort = await findFreePort(API_START_PORT, PORT_ATTEMPTS);
if (apiPort !== API_START_PORT) {
  console.log(`Port ${API_START_PORT} is busy; using ${apiPort} instead.`);
}
const apiTarget = `http://127.0.0.1:${apiPort}`;
console.log(`Backend API: ${apiTarget}`);
console.log("Frontend:    http://localhost:5173");

start(viteBin, [], { VITE_API_TARGET: apiTarget });
start(pythonBin, [
  "-m",
  "uvicorn",
  "server.main:app",
  "--reload",
  "--host",
  "127.0.0.1",
  "--port",
  String(apiPort),
]);
