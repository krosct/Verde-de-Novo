import { DISCLAIMER, type PlantAnalysis } from "./types";

export type ViewResult = "idle" | "found" | "warn" | "error";
export type CameraState = "off" | "on" | "busy";

export interface AppRefs {
  consent: HTMLElement;
  consentCheck: HTMLInputElement;
  consentAccept: HTMLButtonElement;
  main: HTMLElement;
  video: HTMLVideoElement;
  snapshot: HTMLImageElement;
  hud: HTMLElement;
  hudText: HTMLElement;
  status: HTMLElement;
  statusDetail: HTMLElement;
  toggle: HTMLButtonElement;
  gallery: HTMLButtonElement;
  restart: HTMLButtonElement;
  speciesMeta: HTMLElement;
  speciesScientific: HTMLElement;
  speciesConfidence: HTMLElement;
  alternatives: HTMLElement;
  conditions: HTMLElement;
  conditionsList: HTMLElement;
  observed: HTMLElement;
  observedList: HTMLElement;
  care: HTMLElement;
  careList: HTMLElement;
}

const READY_DETAIL = "Enquadre a planta inteira: folhas, caule e terra, com boa luz.";

const RETRY_TITLES: Record<string, string> = {
  not_plant: "Não encontrei uma planta",
  bad_image: "A foto não ficou boa",
  unavailable: "Não deu certo",
};

function requireElement<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Elemento #${id} não encontrado.`);
  }
  return element as T;
}

function el(tag: string, className = "", text = ""): HTMLElement {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text) {
    node.textContent = text;
  }
  return node;
}

function percent(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

function bulletList(items: string[]): HTMLElement {
  const ul = el("ul", "consent-list");
  ul.append(...items.map((item) => el("li", "", item)));
  return ul;
}

export function getRefs(): AppRefs {
  document.querySelectorAll(".disclaimer, #hint").forEach((node) => {
    node.textContent = DISCLAIMER;
  });
  return {
    consent: requireElement("consent"),
    consentCheck: requireElement<HTMLInputElement>("consent-check"),
    consentAccept: requireElement<HTMLButtonElement>("consent-accept"),
    main: requireElement("main"),
    video: requireElement<HTMLVideoElement>("preview"),
    snapshot: requireElement<HTMLImageElement>("snapshot"),
    hud: requireElement("hud"),
    hudText: requireElement("hud-text"),
    status: requireElement("status"),
    statusDetail: requireElement("status-detail"),
    toggle: requireElement<HTMLButtonElement>("toggle"),
    gallery: requireElement<HTMLButtonElement>("gallery"),
    restart: requireElement<HTMLButtonElement>("restart"),
    speciesMeta: requireElement("species-meta"),
    speciesScientific: requireElement("species-scientific"),
    speciesConfidence: requireElement("species-confidence"),
    alternatives: requireElement("alternatives"),
    conditions: requireElement("conditions"),
    conditionsList: requireElement("conditions-list"),
    observed: requireElement("observed"),
    observedList: requireElement("observed-list"),
    care: requireElement("care"),
    careList: requireElement("care-list"),
  };
}

export function showConsent(refs: AppRefs, visible: boolean): void {
  refs.consent.classList.toggle("hidden", !visible);
  refs.main.classList.toggle("hidden", visible);
}

export function setCamera(refs: AppRefs, state: CameraState, text: string): void {
  refs.hud.dataset.camera = state;
  refs.hudText.textContent = text;
}

export function setStatus(refs: AppRefs, result: ViewResult, title: string, detail = ""): void {
  refs.status.dataset.result = result;
  refs.hud.dataset.result = result;
  refs.status.textContent = title;
  refs.statusDetail.textContent = detail;
}

export function setSnapshot(refs: AppRefs, source: Blob | null): void {
  if (refs.snapshot.src) {
    URL.revokeObjectURL(refs.snapshot.src);
    refs.snapshot.removeAttribute("src");
  }
  if (source) {
    refs.snapshot.src = URL.createObjectURL(source);
  }
  refs.snapshot.classList.toggle("hidden", !source);
}

export function clearResult(refs: AppRefs): void {
  for (const node of [refs.speciesMeta, refs.alternatives, refs.conditions, refs.observed, refs.care]) {
    node.classList.add("hidden");
  }
  refs.conditionsList.replaceChildren();
  refs.observedList.replaceChildren();
  refs.careList.replaceChildren();
}

export function showReady(refs: AppRefs): void {
  clearResult(refs);
  setStatus(refs, "idle", "Pronto para começar", READY_DETAIL);
}

export function showError(refs: AppRefs, message: string): void {
  clearResult(refs);
  setStatus(refs, "error", "Não deu certo", message);
}

export function showAnalysis(refs: AppRefs, analysis: PlantAnalysis): void {
  clearResult(refs);
  if (analysis.status !== "analyzed") {
    const tone = analysis.status === "unavailable" ? "error" : "warn";
    setStatus(refs, tone, RETRY_TITLES[analysis.status], analysis.message);
    return;
  }

  const species = analysis.species;
  const tone: ViewResult = analysis.conditions.length > 0 ? "warn" : "found";
  setStatus(refs, tone, species ? species.common_name : "Espécie não identificada", analysis.message);

  if (species) {
    refs.speciesScientific.textContent = species.scientific_name || "—";
    refs.speciesConfidence.textContent = percent(species.confidence);
    refs.speciesMeta.classList.remove("hidden");
  }
  if (analysis.alternatives.length > 0) {
    const names = analysis.alternatives.map((item) => `${item.common_name} (${percent(item.confidence)})`);
    refs.alternatives.textContent = `${species ? "Também pode ser" : "Pode ser"}: ${names.join(", ")}`;
    refs.alternatives.classList.remove("hidden");
  }

  if (analysis.conditions.length > 0) {
    refs.conditionsList.append(
      ...analysis.conditions.map((condition) => {
        const item = el("div", "item");
        const title = el("h3", "group-title");
        title.append(el("span", "", condition.label), el("span", "pill", percent(condition.confidence)));
        item.append(title, el("p", "", condition.explanation));
        if (condition.evidence.length > 0) {
          item.append(el("p", "evidence", `Sinais: ${condition.evidence.join("; ")}`));
        }
        item.append(bulletList(condition.suggestions));
        return item;
      }),
    );
    refs.conditions.classList.remove("hidden");
  }

  const parts = analysis.parts.filter((part) => part.observations.length > 0);
  if (parts.length > 0) {
    refs.observedList.append(
      ...parts.map((part) => {
        const item = el("div", "item");
        item.append(el("h3", "group-title", part.label), bulletList(part.observations.map((obs) => obs.label)));
        return item;
      }),
    );
    refs.observed.classList.remove("hidden");
  }

  if (analysis.care.length > 0) {
    refs.careList.append(
      ...analysis.care.map((tip) => {
        const item = el("div", "item");
        item.append(el("span", "care-label", tip.label), el("span", "care-text", tip.text));
        return item;
      }),
    );
    refs.care.classList.remove("hidden");
  }

  (analysis.conditions.length > 0 ? refs.conditions : refs.care).scrollIntoView({
    behavior: "smooth",
    block: "nearest",
  });
}
