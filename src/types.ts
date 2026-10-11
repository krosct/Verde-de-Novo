export const ANALYSIS_STATUSES = ["analyzed", "not_plant", "bad_image", "unavailable"] as const;
export type AnalysisStatus = (typeof ANALYSIS_STATUSES)[number];

export const PARTS = ["leaf", "stem", "soil", "roots"] as const;
export type PlantPart = (typeof PARTS)[number];

export const CONDITION_CODES = [
  "overwatering",
  "underwatering",
  "low_light",
  "too_much_sun",
  "low_humidity",
  "fungus",
  "pest",
  "root_rot_risk",
  "pot_bound",
  "poor_soil",
  "nutrient_need",
] as const;
export type ConditionCode = (typeof CONDITION_CODES)[number];

export interface Species {
  id: string | null;
  common_name: string;
  scientific_name: string;
  confidence: number;
  known: boolean;
}

export interface Observation {
  code: string;
  label: string;
  confidence: number;
}

export interface PartReport {
  part: PlantPart;
  label: string;
  observations: Observation[];
}

export interface Condition {
  code: ConditionCode;
  label: string;
  explanation: string;
  confidence: number;
  evidence: string[];
  suggestions: string[];
}

export interface CareTip {
  topic: string;
  label: string;
  text: string;
}

export interface PlantAnalysis {
  ok: boolean;
  status: AnalysisStatus;
  message: string;
  species: Species | null;
  alternatives: Species[];
  parts: PartReport[];
  conditions: Condition[];
  care: CareTip[];
  is_diagnosis: false;
  retry: boolean;
}

export const MAX_UPLOAD_BYTES = Math.round(2.5 * 1024 * 1024);

export const UPLOAD_TIMEOUT_MS = 45_000;

export const DISCLAIMER = "Não é diagnóstico; é uma pista para você verificar.";
