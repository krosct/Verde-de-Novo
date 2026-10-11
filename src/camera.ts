import { canvasToJpegBlob } from "./image";

const VIDEO_READY_TIMEOUT_MS = 5000;
const FRAME_TIMEOUT_MS = 2500;

export interface CameraSession {
  stream: MediaStream;
  stop: () => void;
}

export async function openCamera(video: HTMLVideoElement): Promise<CameraSession> {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Não consegui acessar a câmera neste navegador. Use o botão da galeria.");
  }

  const stream = await navigator.mediaDevices.getUserMedia({
    audio: false,
    video: {
      facingMode: { ideal: "environment" },
      width: { ideal: 1280 },
      height: { ideal: 1280 },
    },
  });

  try {
    await attachStream(video, stream);
  } catch (error) {
    stream.getTracks().forEach((track) => track.stop());
    throw error;
  }

  return {
    stream,
    stop: () => {
      stream.getTracks().forEach((track) => track.stop());
      video.srcObject = null;
    },
  };
}

async function attachStream(video: HTMLVideoElement, stream: MediaStream): Promise<void> {
  video.muted = true;
  video.playsInline = true;
  video.setAttribute("playsinline", "true");
  video.autoplay = true;
  video.srcObject = stream;

  await waitForMetadata(video);
  await startPlayback(video);
  await ensureFrames(video);
}

function waitForMetadata(video: HTMLVideoElement): Promise<void> {
  if (video.readyState >= HTMLMediaElement.HAVE_METADATA) {
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      video.removeEventListener("loadedmetadata", finish);
      video.removeEventListener("error", finish);
      clearTimeout(timer);
      resolve();
    };
    const timer = setTimeout(finish, VIDEO_READY_TIMEOUT_MS);
    video.addEventListener("loadedmetadata", finish);
    video.addEventListener("error", finish);
  });
}

async function startPlayback(video: HTMLVideoElement): Promise<void> {
  try {
    await video.play();
    return;
  } catch {
    // Retry once after a paint; the first attempt can be interrupted while the
    // element is still settling into the layout.
  }
  await nextFrame();
  try {
    await video.play();
  } catch {
    throw new Error("Não consegui iniciar a câmera. Confira a permissão e toque em Tirar foto de novo.");
  }
}

function nextFrame(): Promise<void> {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

async function ensureFrames(video: HTMLVideoElement): Promise<void> {
  const deadline = Date.now() + FRAME_TIMEOUT_MS;
  while (Date.now() < deadline) {
    if (video.videoWidth > 0 && video.videoHeight > 0) {
      return;
    }
    await nextFrame();
  }
  throw new Error(
    "A câmera abriu, mas não retornou imagem. Feche outros apps que usam a câmera e toque em Tirar foto de novo.",
  );
}

export function captureFrame(video: HTMLVideoElement): Promise<Blob> {
  const width = video.videoWidth;
  const height = video.videoHeight;
  if (!width || !height) {
    return Promise.reject(new Error("A câmera ainda não está pronta."));
  }
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return Promise.reject(new Error("Não foi possível capturar a foto."));
  }
  ctx.drawImage(video, 0, 0, width, height);
  return canvasToJpegBlob(canvas, 0.92);
}

export function pickImageFile(): Promise<File | null> {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.setAttribute("capture", "environment");
    input.style.display = "none";

    const finish = (file: File | null) => {
      input.remove();
      resolve(file);
    };

    input.addEventListener("change", () => finish(input.files?.[0] ?? null));
    input.addEventListener("cancel", () => finish(null));

    document.body.appendChild(input);
    input.click();
  });
}
