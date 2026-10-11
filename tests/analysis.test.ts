import { describe, expect, it } from "vitest";
import { ApiError, parsePlantAnalysis } from "../src/api";
import { DISCLAIMER } from "../src/types";

const analyzed = {
  ok: true,
  status: "analyzed",
  message: "Encontrei alguns pontos de atenção.",
  species: {
    id: "succulent",
    common_name: "Suculenta",
    scientific_name: "Crassulaceae",
    confidence: 0.9,
    known: true,
  },
  alternatives: [],
  parts: [
    { part: "leaf", label: "Folhas", observations: [{ code: "leaf_yellow_lower", label: "Folhas de baixo amareladas", confidence: 0.8 }] },
    { part: "trunk", label: "Tronco", observations: [] },
  ],
  conditions: [
    {
      code: "overwatering",
      label: "Excesso de água",
      explanation: "Terra úmida por tempo demais.",
      confidence: 0.85,
      evidence: ["Terra encharcada"],
      suggestions: ["Espere a terra secar"],
    },
    { code: "mosaic_virus", label: "Vírus do mosaico", explanation: "", confidence: 0.99, evidence: [], suggestions: [] },
  ],
  care: [{ topic: "light", label: "Luz", text: "Sol direto" }],
  is_diagnosis: false,
  retry: false,
};

describe("plant analysis contract", () => {
  it("parses a full analysis", () => {
    const result = parsePlantAnalysis(analyzed);
    expect(result.species?.common_name).toBe("Suculenta");
    expect(result.conditions.map((item) => item.code)).toEqual(["overwatering"]);
    expect(result.care).toHaveLength(1);
    expect(result.is_diagnosis).toBe(false);
  });

  it("drops conditions and parts outside the fixed lists", () => {
    const result = parsePlantAnalysis(analyzed);
    expect(result.conditions.some((item) => item.code === ("mosaic_virus" as string))).toBe(false);
    expect(result.parts.map((item) => item.part)).toEqual(["leaf"]);
  });

  it("forces is_diagnosis false and retry on non-analyzed statuses", () => {
    const result = parsePlantAnalysis({ ...analyzed, status: "not_plant", is_diagnosis: true, retry: false });
    expect(result.is_diagnosis).toBe(false);
    expect(result.retry).toBe(true);
  });

  it("clamps confidence into [0, 1]", () => {
    const result = parsePlantAnalysis({ ...analyzed, species: { ...analyzed.species, confidence: 7 } });
    expect(result.species?.confidence).toBe(1);
  });

  it("rejects unknown statuses", () => {
    expect(() => parsePlantAnalysis({ ...analyzed, status: "diagnosed" })).toThrow(ApiError);
    expect(() => parsePlantAnalysis(null)).toThrow(ApiError);
  });
});

describe("disclaimer", () => {
  it("always states it is not a diagnosis", () => {
    expect(DISCLAIMER.toLowerCase()).toContain("não é diagnóstico");
  });
});
