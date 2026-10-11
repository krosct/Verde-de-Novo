import "./style.css";
import { ApiError, analyzePlant } from "./api";
import { captureFrame, openCamera, pickImageFile, type CameraSession } from "./camera";
import { prepareImage } from "./image";
import {
  getRefs,
  setCamera,
  setSnapshot,
  setStatus,
  showConsent,
  showError,
  showAnalysis,
  showReady,
  type AppRefs,
} from "./ui";

const OFFLINE_MESSAGE = "Você está offline. Conecte-se para analisar a foto.";

const refs: AppRefs = getRefs();
let session: CameraSession | null = null;
let busy = false;

function refreshControls(): void {
  const cameraOn = session !== null;
  refs.toggle.textContent = cameraOn ? "Capturar" : "Tirar foto";
  refs.toggle.dataset.state = cameraOn ? "camera" : "idle";
  refs.toggle.disabled = busy;
  refs.gallery.disabled = busy;
  refs.restart.disabled = busy || (!cameraOn && refs.status.dataset.result === "idle");
}

function setBusy(value: boolean): void {
  busy = value;
  refreshControls();
}

async function openCameraFlow(): Promise<void> {
  showReady(refs);
  setSnapshot(refs, null);
  setBusy(true);
  setCamera(refs, "busy", "Abrindo câmera…");
  refs.video.classList.remove("hidden");
  try {
    session = await openCamera(refs.video);
    setCamera(refs, "on", "Câmera ligada");
  } catch (error) {
    closeCamera();
    showError(refs, messageOf(error));
  } finally {
    setBusy(false);
  }
}

function closeCamera(): void {
  session?.stop();
  session = null;
  refs.video.classList.add("hidden");
  setCamera(refs, "off", "Câmera desligada");
}

async function captureFlow(): Promise<void> {
  if (!session) {
    return;
  }
  try {
    const frame = await captureFrame(refs.video);
    closeCamera();
    await send(frame);
  } catch (error) {
    closeCamera();
    showError(refs, messageOf(error));
    refreshControls();
  }
}

async function galleryFlow(): Promise<void> {
  const file = await pickImageFile();
  if (!file) {
    return;
  }
  closeCamera();
  await send(file);
}

async function send(source: Blob): Promise<void> {
  setSnapshot(refs, source);
  if (!navigator.onLine) {
    showError(refs, OFFLINE_MESSAGE);
    refreshControls();
    return;
  }
  setBusy(true);
  setCamera(refs, "busy", "Analisando…");
  setStatus(refs, "idle", "Preparando a foto…");
  try {
    const prepared = await prepareImage(source);
    setStatus(refs, "idle", "Analisando a planta…", "Identificando a espécie e olhando cada parte.");
    showAnalysis(refs, await analyzePlant(prepared));
  } catch (error) {
    showError(refs, messageOf(error));
  } finally {
    setCamera(refs, "off", "Câmera desligada");
    setBusy(false);
  }
}

function messageOf(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return "Algo deu errado. Tente de novo.";
}

function reset(): void {
  closeCamera();
  setSnapshot(refs, null);
  showReady(refs);
  refreshControls();
}

function init(): void {
  refs.consentCheck.addEventListener("change", () => {
    refs.consentAccept.disabled = !refs.consentCheck.checked;
  });
  refs.consentAccept.addEventListener("click", () => {
    showConsent(refs, false);
  });
  refs.toggle.addEventListener("click", () => {
    void (session ? captureFlow() : openCameraFlow());
  });
  refs.gallery.addEventListener("click", () => void galleryFlow());
  refs.restart.addEventListener("click", reset);
  window.addEventListener("offline", () => {
    if (!busy) {
      setStatus(refs, "error", "Sem conexão", OFFLINE_MESSAGE);
      refreshControls();
    }
  });
  window.addEventListener("online", () => {
    if (!busy && refs.status.dataset.result === "error") {
      reset();
    }
  });
  showConsent(refs, true);
  showReady(refs);
  refreshControls();
}

init();
