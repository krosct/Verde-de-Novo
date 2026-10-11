import {
  ANALYSIS_STATUSES,
  CONDITION_CODES,
  PARTS,
  UPLOAD_TIMEOUT_MS,
  type AnalysisStatus,
  type CareTip,
  type Condition,
  type ConditionCode,
  type Observation,
  type PartReport,
  type PlantAnalysis,
  type PlantPart,
  type Species,
} from "./types";

export type ApiErrorKind = "timeout" | "network" | "server" | "bad_response";

export class ApiError extends Error {
  constructor(
    public readonly kind: ApiErrorKind,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function analyzePlant(image: Blob): Promise<PlantAnalysis> {
  const form = new FormData();
  form.append("image", image, "plant.jpg");

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch("/api/plant", { method: "POST", body: form, signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("timeout", "A análise demorou demais. Tente de novo.");
    }
    throw new ApiError("network", "Sem conexão com o servidor. Verifique a internet e tente de novo.");
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    throw new ApiError("server", await readErrorMessage(response));
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError("bad_response", "Resposta inesperada do servidor.");
  }
  return parsePlantAnalysis(payload);
}

type Json = Record<string, unknown>;

const isObject = (value: unknown): value is Json => typeof value === "object" && value !== null;
const text = (value: unknown): string => (typeof value === "string" ? value : "");
const ratio = (value: unknown): number =>
  typeof value === "number" && Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
const strings = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
const list = <T>(value: unknown, parse: (item: Json) => T | null): T[] =>
  Array.isArray(value)
    ? value.flatMap((item) => {
        const parsed = isObject(item) ? parse(item) : null;
        return parsed === null ? [] : [parsed];
      })
    : [];

const includes = <T extends string>(values: readonly T[], value: unknown): value is T =>
  typeof value === "string" && (values as readonly string[]).includes(value);

function parseSpecies(data: Json): Species | null {
  const commonName = text(data.common_name);
  if (!commonName) {
    return null;
  }
  return {
    id: typeof data.id === "string" ? data.id : null,
    common_name: commonName,
    scientific_name: text(data.scientific_name),
    confidence: ratio(data.confidence),
    known: data.known === true,
  };
}

function parseObservation(data: Json): Observation | null {
  const label = text(data.label);
  return label ? { code: text(data.code), label, confidence: ratio(data.confidence) } : null;
}

function parsePart(data: Json): PartReport | null {
  if (!includes<PlantPart>(PARTS, data.part)) {
    return null;
  }
  return { part: data.part, label: text(data.label), observations: list(data.observations, parseObservation) };
}

function parseCondition(data: Json): Condition | null {
  if (!includes<ConditionCode>(CONDITION_CODES, data.code)) {
    return null;
  }
  return {
    code: data.code,
    label: text(data.label),
    explanation: text(data.explanation),
    confidence: ratio(data.confidence),
    evidence: strings(data.evidence),
    suggestions: strings(data.suggestions),
  };
}

function parseCare(data: Json): CareTip | null {
  const value = text(data.text);
  return value ? { topic: text(data.topic), label: text(data.label), text: value } : null;
}

export function parsePlantAnalysis(payload: unknown): PlantAnalysis {
  if (!isObject(payload) || !includes<AnalysisStatus>(ANALYSIS_STATUSES, payload.status)) {
    throw new ApiError("bad_response", "Resposta inesperada do servidor.");
  }
  const status = payload.status;
  return {
    ok: payload.ok === true,
    status,
    message: text(payload.message),
    species: isObject(payload.species) ? parseSpecies(payload.species) : null,
    alternatives: list(payload.alternatives, parseSpecies),
    parts: list(payload.parts, parsePart),
    conditions: list(payload.conditions, parseCondition),
    care: list(payload.care, parseCare),
    is_diagnosis: false,
    retry: payload.retry === true || status !== "analyzed",
  };
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string" && body.detail.length > 0) {
      return body.detail;
    }
  } catch {
    /* fall through to status-based message */
  }
  if (response.status === 429) {
    return "Muitas tentativas em pouco tempo. Espere um instante.";
  }
  if (response.status === 413) {
    return "A foto é grande demais. Tente uma menor.";
  }
  if (response.status === 400) {
    return "Não reconheci um arquivo de imagem válido.";
  }
  return "Não foi possível analisar agora. Tente de novo em instantes.";
}
