import { MAX_UPLOAD_BYTES } from "./types";

const MAX_EDGE = 1600;
const JPEG_QUALITY = 0.8;

export function canvasToJpegBlob(canvas: HTMLCanvasElement, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("Falha ao gerar a imagem."))),
      "image/jpeg",
      quality,
    );
  });
}

export async function prepareImage(source: Blob): Promise<Blob> {
  const image = await loadImage(source);
  const target = fitWithin(image.width, image.height, MAX_EDGE);
  const canvas = document.createElement("canvas");
  canvas.width = target.width;
  canvas.height = target.height;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Não foi possível preparar a imagem.");
  }
  ctx.drawImage(image, 0, 0, target.width, target.height);
  closeImage(image);
  const blob = await canvasToJpegBlob(canvas, JPEG_QUALITY);
  if (blob.size > MAX_UPLOAD_BYTES) {
    throw new Error("A foto ficou grande demais. Tente de novo.");
  }
  return blob;
}

type LoadedImage = HTMLImageElement | ImageBitmap;

async function loadImage(source: Blob): Promise<LoadedImage> {
  if (typeof createImageBitmap === "function") {
    return createImageBitmap(source, { imageOrientation: "from-image" });
  }
  return loadWithImageElement(source);
}

function loadWithImageElement(source: Blob): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(source);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Não foi possível ler a imagem."));
    };
    img.src = url;
  });
}

function closeImage(image: LoadedImage): void {
  if (typeof ImageBitmap !== "undefined" && image instanceof ImageBitmap) {
    image.close();
  }
}

function fitWithin(width: number, height: number, maxEdge: number): { width: number; height: number } {
  const longest = Math.max(width, height);
  if (longest <= maxEdge) {
    return { width, height };
  }
  const scale = maxEdge / longest;
  return { width: Math.round(width * scale), height: Math.round(height * scale) };
}
