# Verde de Novo

> Photograph a whole houseplant — leaves, stem, soil — and get its likely species,
> what looks off, and what to do so it grows better. Not a diagnosis.
> Fotografe a planta inteira e veja a espécie provável, o que merece atenção e o
> que fazer para ela crescer melhor. Não é diagnóstico.

---

## 1. Purpose

Home plant owners do not know what their plant needs. They search the internet,
get ten contradictory answers, and act on a guess.

**One-liner:** one photo of the whole plant in; species, conditions per part, and
concrete care suggestions out.

---

## 2. Main Pain

- "My plant is not growing / looks sad and I don't know why."
- Care advice depends on the species, and people often don't know which one
  they have.
- Internet search is noisy; the person acts on a guess and makes it worse.

---

## 3. Persona

**Primary — Camila, 41, apartment plant hobbyist.** 8–15 potted plants, little
botanical knowledge, waters by habit. Mid-range Android, Chrome up to date.
Values honesty: a wrong confident answer erodes trust fast.

**Secondary — the office plant "responsible".**

**Anti-persona.** A farmer or agronomist needing a real diagnosis.

---

## 4. Features

### MVP (v1)
- Take a photo (camera) or pick from the gallery, framing the **whole plant**.
- Step-by-step analysis (section 6) returning:
  - likely **species** with confidence, plus up to two alternatives;
  - **observations per visible part** (leaves, stem, soil, roots);
  - **conditions** inferred from the observations, each with its evidence and
    suggestions;
  - **care tips** from the species profile ("Para ela crescer melhor").
- Stop early and ask for another photo when there is no plant, or the photo is
  dark, blurry, or too far.
- Always show the disclaimer "não é diagnóstico; é uma pista para você verificar".
- Works on desktop browser, Android Chrome, and Android TWA.

### Later (v1.1+)
- Let the user confirm or correct the species before the care tips.
- Two or three quick questions (watering frequency, distance to a window) to
  refine the rules.
- Stream progress per step to the UI.
- Share result as an image.

### Out of scope
- Any claim of medical, agricultural, or scientific diagnosis.
- Free-form disease names. Only the fixed lists below.
- Pesticide or chemical dosing instructions.
- Accounts, cloud history, iOS, video.

---

## 5. Platforms & Compatibility

| Platform | Supported | Notes |
|---|---|---|
| Desktop browser (Chrome/Edge/Firefox) | Yes | Camera or file picker |
| Android Chrome | Yes | Main mobile target |
| Android TWA (installed app) | Yes | Same web app wrapped |
| iOS Safari / iPhone | No | Out of scope |

HTTPS mandatory; camera permission only after a tap; file-picker fallback; test
down to 360px wide.

---

## 6. Analysis Pipeline

Small steps, each answering one narrow question with fixed codes. Models only
**observe**; deterministic rules **decide**. Every answer traces back to evidence.

```
photo
  │
  ├─ 1. Gate ............ is there a plant? is the photo usable (dark/blurry/far)?
  │                        no → stop, ask for another photo
  ├─ 2. Species ......... top guesses + confidence → species profile
  │                        (light, water, humidity, growth tip)
  │                        below threshold → species unknown, generic care
  ├─ 3. Parts ........... which of leaf / stem / soil / roots are visible + boxes
  ├─ 4. Per-part ........ crop each part, list observations from the fixed
  │                        vocabulary (runs in parallel)
  ├─ 5. Rules ........... observations × species profile → conditions
  │                        (weighted evidence, contradictions, species factors)
  └─ 6. Suggestions ..... fixed pt-BR copy per condition + species care tips
```

- Steps 1–4 live behind the vision adapter (`server/vendor.py`). Steps 5–6 are
  plain code (`server/decision.py`) and never call a model.
- Each step has a confidence threshold (`CONFIDENCE_THRESHOLD`, default 0.6).
  Observations need ≥ 0.5. Anything below is dropped, never forced.
- Codes outside the fixed vocabularies are discarded on the server and again on
  the client.
- The current vendor is a deterministic **stub**: same photo, same answer; it
  does not look at the plant. A real vendor (plant-specific API and/or a
  multimodal model with structured output) replaces it behind the same protocol.

### Fixed vocabularies (`server/catalog.py`)
- **Parts:** `leaf | stem | soil | roots`.
- **Observations:** ~30 codes, each tied to one part (e.g. `leaf_yellow_lower`,
  `soil_wet`, `stem_leggy`, `roots_brown_mushy`).
- **Conditions:** `overwatering | underwatering | low_light | too_much_sun |
  low_humidity | fungus | pest | root_rot_risk | pot_bound | poor_soil |
  nutrient_need`.
- **Species profiles:** a curated table of common houseplants. A species outside
  the table may be shown by name, but care tips fall back to generic ones.

---

## 7. Architecture & Stack

```
[ Browser (Vite + TS PWA) ] --HTTPS, compressed JPEG--> [ FastAPI proxy ]
                                                          │ key, rate limit,
                                                          │ strips EXIF, no storage
                                                          ├─ vision adapter (steps 1–4)
                                                          └─ rules (steps 5–6)
```

- Frontend: Vite + TypeScript, vite-plugin-pwa, vanilla TS, `getUserMedia` +
  file-input fallback, `<canvas>` for rotation/resize/JPEG.
- Backend: Python + FastAPI + Pillow (crops). `~/.venv/bin/python` only.
- Packaging: Bubblewrap TWA, Digital Asset Links, camera permission only.
- Visual identity mirrors the Tartaruguinha project (dark navy + teal).

---

## 8. API Contract

**Request** — `POST /api/plant`, `multipart/form-data`:
- `image`: JPEG, max 1600px long edge, max 2.5 MB.

**Response** — JSON:
```json
{
  "ok": true,
  "status": "analyzed",
  "message": "Encontrei alguns pontos de atenção. Veja o que fazer em cada um.",
  "species": {
    "id": "monstera_deliciosa",
    "common_name": "Costela-de-adão",
    "scientific_name": "Monstera deliciosa",
    "confidence": 0.86,
    "known": true
  },
  "alternatives": [
    { "id": "epipremnum_aureum", "common_name": "Jiboia", "scientific_name": "Epipremnum aureum", "confidence": 0.31, "known": true }
  ],
  "parts": [
    { "part": "soil", "label": "Terra", "observations": [
      { "code": "soil_wet", "label": "Terra encharcada ou brilhando de água", "confidence": 0.85 }
    ] }
  ],
  "conditions": [
    {
      "code": "overwatering",
      "label": "Excesso de água",
      "explanation": "Os sinais indicam terra úmida por tempo demais, o que sufoca as raízes.",
      "confidence": 0.82,
      "evidence": ["Terra encharcada ou brilhando de água"],
      "suggestions": ["Espere a terra secar antes de regar de novo"]
    }
  ],
  "care": [
    { "topic": "light", "label": "Luz", "text": "Muita luz indireta; um pouco de sol fraco da manhã ajuda" }
  ],
  "is_diagnosis": false,
  "retry": false
}
```

- `status`: `analyzed | not_plant | bad_image | unavailable`. Anything but
  `analyzed` has empty lists and `retry: true`.
- `species` is `null` when the top guess is below the threshold; guesses still
  appear in `alternatives`.
- `known` is `true` only when the species has a profile in the catalog.
- `confidence` values are in `[0,1]`. They are model scores, not calibrated
  probabilities; thresholds must be tuned on real photos.
- `is_diagnosis` is always `false`.
- Change the contract only together with `src/types.ts`, `src/api.ts`, and the
  tests.

---

## 9. Camera & Image Rules

- Permission only after a tap. One snapshot per action; no video.
- Guide: the whole plant, with leaves, stem and soil visible, good light.
- Before upload: EXIF-rotate, resize long edge ≤ 1600px, JPEG q0.8, reject if
  > 2.5 MB. The server strips metadata again.
- Upload timeout: 45 s (several steps). Rate limit per client.

---

## 10. Privacy & LGPD

- Consent card ("Antes de começar") shown on every visit before any photo is
  sent.
- No image is stored, on device or server; image contents are never logged.
- Service worker caches only the app shell, never POST responses or images.

---

## 11. Failure Modes & Safeguards

| Failure | Safeguard |
|---|---|
| No plant in the photo | `not_plant`, ask for another photo |
| Dark / blurry / too far | `bad_image` with a specific hint |
| No part recognized | `bad_image`, ask for leaves, stem and soil in frame |
| Species uncertain | `species: null`, alternatives shown, generic care |
| Weak signs only | No condition; message says signs were not clear enough |
| Contradictory signs (wet and dry soil) | Rule penalty; condition dropped |
| Model invents a code | Dropped on server and client |
| Camera denied | File-picker fallback |
| Timeout / offline / vendor outage | Friendly message, app stays usable |
| User treats it as a diagnosis | Persistent disclaimer |

---

## 12. Build Order

1. **Freeze** — vocabularies, rules, contract, stub vendor. *(done)*
2. **Camera on real hardware** — desktop and a real Android, against the stub.
3. **Real vendor** — implement the four steps in `server/vendor.py`; build a
   small labeled photo set and measure each step separately.
4. **Tune** — thresholds and rule weights from the photo set.
5. **Harden** — offline, timeout, denied permission, bad photos.
6. **PWA install**, then **TWA**.

---

## 13. Definition of Done (v1)

- [ ] Camera and file picker work on desktop and Android.
- [ ] Non-plant and bad photos stop at the gate with a clear hint.
- [ ] Species shown with confidence; uncertain species falls back to generic care.
- [ ] Observations, conditions, and suggestions only from the fixed lists.
- [ ] Each condition shows the evidence that produced it.
- [ ] Disclaimer visible on every result.
- [ ] No API key in client code or bundles.
- [ ] Offline, denied-permission, and timeout states handled.
- [ ] Consent shown before upload; no image stored.
- [ ] Installs as PWA; TWA builds and camera works inside it.
- [ ] Usable at 360px width; buttons ≥ 48px.

---

## 14. Shared Traps

1. Never expose the API key in the client.
2. Test the camera on a real Android device early.
3. HTTPS from day one.
4. Compress and rotate images before upload.
5. Thresholds per step; prefer "não sei" over a guess.
6. Handle denied permission, offline, and timeout from the start.
7. Do not store photos.
8. TWA only after the site works in Android Chrome.
9. Asset-links fingerprint must match the signing keystore.
10. Models observe, rules decide. Never let a model write user-facing advice.
11. Never invent a disease name; never give pesticide dosing.
12. Always state it is not a diagnosis.
13. iOS is out of scope.
