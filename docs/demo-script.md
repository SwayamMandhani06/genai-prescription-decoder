# DawaAI Live Demonstration Script & Walkthrough Guide
## 10-Minute Comprehensive Evaluation Walkthrough for Examiners

**System:** DawaAI — Explainable Multimodal AI for Handwritten Prescription Understanding  
**Document Classification:** Interactive Demonstration Protocol  
**System Classification:** Deployment-Ready Assistive Research Prototype for Academic Demonstration  
**Version:** 1.0 (Frozen Protocol)  
**Date:** March 2026

---

## 1. Demonstration Overview & Objectives

This walkthrough script guides the presenter through an end-to-end interactive demonstration of DawaAI during academic evaluation or viva defense. The 10-minute demonstration is divided into six structured acts showcasing:
1. **Brand Identity & Patient Accessibility:** DawaAI visual language, plum/pink palette, and multilingual readiness.
2. **Document Intake & Processing Pipeline:** Adaptive image loading and multi-stage telemetry.
3. **Dual-Pane Stroke Grounding:** Spatial bounding box explainability and CDSCO formulary reconciliation.
4. **LASA Screening & Collision Mitigation:** ISMP Tall Man lettering and clinical alerts.
5. **Calibrated Selective Abstention:** Refusal to produce unsupported predictions on degraded cursive under Chow's rule.
6. **Pharmacist-in-the-Loop Verification & Vernacular Audio:** Section 42 regulatory considerations, Hindi/Marathi posology, and live speech synthesis.

---

## 2. Pre-Flight Setup & Environment Verification

Before inviting examiners to view the screen, ensure both backend and frontend servers are active:

```bash
# Terminal 1: Backend Server (Port 8000)
python backend/run.py

# Terminal 2: Frontend Server (Port 5173)
npm run dev
```

### Quick Sanity Checks:
- Open browser at `http://localhost:5173/`.
- Ensure page title reads: `DawaAI — Your Prescription, Made Clear.`
- Favicon displays the official plum-and-rose cross/pill icon.
- Audio volume is set to 60–70% for the Web Speech demonstration.

---

## 3. Step-by-Step Demonstration Walkthrough (10 Minutes)

### Act 1: Brand Experience & Patient Landing (0:00 – 1:30)
- **Action:** Open `http://localhost:5173/` on the main screen.
- **Visual Focus:** Point out the official DawaAI header logo with plum serif typography (*"Dawa"*) and vibrant rose sans-serif (*"AI"*), the tagline *"Your Prescription, Made Clear."*, and the calm `#F8F2F6` canvas.
- **Presenter Dialogue:**
  > *"Welcome to DawaAI. As you can see on our landing page, our identity is built around clinical calm and patient accessibility. Notice the vernacular tabs in the header and hero section: with a single click, we switch from English to Hindi ('आपकी दवा की जानकारी') and Marathi ('तुमच्या औषधाची माहिती'). Notice our core philosophy banner: DawaAI is strictly an assistive research prototype that incorporates regulatory considerations under Section 42 of the Indian Pharmacy Act. We never autonomously dispense medications."*
- **Interaction:**
  - Click on the **हिंदी** tab in the language section to demonstrate dynamic Devanagari rendering.
  - Click on the **मराठी** tab.
  - Return to English and click the primary CTA button: **"Analyze a Prescription"**.

---

### Act 2: Document Intake & Processing Pipeline (1:30 – 3:00)
- **Action:** Transition to the intake workspace (`/upload` or workspace modal).
- **Visual Focus:** Drag-and-drop intake zone, camera capture options, and the pre-loaded curated clinical sample cards.
- **Presenter Dialogue:**
  > *"Here in the intake workspace, users can upload an image or select from our curated outpatient development cohort. Let us select Sample 1, which represents an outpatient prescription for Acute Bronchitis featuring handwritten Amoxicillin-Clavulanate, Paracetamol, and Cetirizine."*
- **Interaction:**
  - Click on **"Sample 1: Acute Bronchitis Regimen"**.
  - Click **"Process Prescription"**.
  - Point to the live processing visualizer showing the pipeline stages advancing:
    1. *Document Preprocessing & Sauvola Binarization*
    2. *Multimodal Vision Token Extraction*
    3. *CDSCO & RxNorm Formulary Grounding*
    4. *Confidence Estimation & Abstention Gating*
  - Observe the scanning beam traversing the uploaded document.

---

### Act 3: Clinical Dual-Pane Workspace & Stroke Grounding (3:00 – 5:00)
- **Action:** Results load into the dual-pane clinical workspace.
- **Visual Focus:** Original document canvas on the left; structured extracted entities on the right.
- **Presenter Dialogue:**
  > *"Here is DawaAI's explainability interface. On the left is the preserved original prescription image. On the right are our extracted clinical entities. Notice that extracted fields display explicit status tags. Now observe what happens when I click on 'Amoxicillin and Clavulanate Potassium 625mg'."*
- **Interaction:**
  - Click the **Amoxicillin / Clavulanate** card.
  - **Visual Result:** An interactive SVG bounding box highlights the physician's handwritten cursive strokes on the prescription slip.
  - Point out the **CDSCO Grounded** badge and the **RxNorm RxCUI** reference.
  - Click the **Paracetamol** card: the bounding box smoothly shifts to line 2.
  - Highlight the contrast controls and zoom tools on the prescription canvas.

---

### Act 4: Safety Invariants & LASA Collision Handling (5:00 – 6:30)
- **Action:** Click "Try Another Sample" and select **"Sample 3: LASA Challenge (Prednisone)"**.
- **Visual Focus:** Amber alert banner and ISMP Tall Man lettering.
- **Presenter Dialogue:**
  > *"Now let us demonstrate how DawaAI handles Look-Alike Sound-Alike drug names. Sample 3 features an ambiguous cursive script for Prednisone. In outpatient dispensing, Prednisone is frequently confused with Prednisolone—a look-alike sound-alike drug with dosage differences. Our system is designed to reduce the risk of unsupported medication identification by escalating uncertain cases."*
- **Interaction:**
  - Process Sample 3.
  - Point out the prominent amber safety banner:  
    `⚠️ LASA Conflict Alert: Confusable pair detected between predniSONE and prednisoLONE.`
  - Point out the **ISMP Tall Man lettering**: **predniSONE** displayed with capitalized distinguishing letters.
  - Show the examiner that the interface requires pharmacist review of the confusable pair before releasing posology.

---

### Act 5: Epistemic Uncertainty & Selective Abstention (6:30 – 8:00)
- **Action:** Click "Try Another Sample" and select **"Sample 5: Degraded Ink & Bleed-Through"**.
- **Visual Focus:** Full-document selective abstention state.
- **Presenter Dialogue:**
  > *"This demonstrates our uncertainty handling. Sample 5 is a stress case featuring crumpled paper, stains, and ink bleed-through. When evaluated on ungrounded models, ink smears can lead to hallucinated drug names. Notice what DawaAI does instead."*
- **Interaction:**
  - Process Sample 5.
  - Point out the **`STATUS: ABSTAINED`** badge.
  - Highlight the low confidence signal and notice that the sample size safeguard reports `calibration_status = "insufficient_data"`.
  - Point to the explicit diagnostic message:  
    `"Automated Output Halted under Chow's Rule: Severe ink bleed-through and stroke ambiguity. Escalated to Registered Pharmacist."`
  - Emphasize to the committee:
    > *"On this curated evaluation case, DawaAI abstains rather than producing an unsupported medication prediction. By refusing to guess, the system routes ambiguous cases to human verification."*

---

### Act 6: Pharmacist Verification & Vernacular Audio (8:00 – 10:00)
- **Action:** Return to Sample 1 or open the Verification Gate modal.
- **Visual Focus:** Human verification workflow, Hindi/Marathi posology cards, and Web Speech synthesis.
- **Presenter Dialogue:**
  > *"To finalize the prescription and prepare patient guidance, Section 42 regulatory considerations require registered pharmacist verification. Let us complete the verification."*
- **Interaction:**
  - Open the verification workflow.
  - Review the posology fields and submit verification.
  - Transition to the **Patient Posology Card**.
  - Select the **हिन्दी (Hindi)** tab: Show the 4 daily slots (सुबह, दोपहर, शाम, रात).
  - Click the **"Play Audio" (आवाज सुनें)** button:  
    *The browser Web Speech synthesizer speaks the Hindi instructions clearly.*
  - Select the **मराठी (Marathi)** tab and trigger audio playback.
  - Conclude the demonstration:
    > *"From raw paper ink to spatial stroke grounding, pharmacist-in-the-loop verification, and vernacular voice guidance for the patient, DawaAI demonstrates an explainable assistive research prototype designed with patient safety and transparency at its core. Thank you."*

---

## 4. Troubleshooting & Fallback Procedures

| Issue | Immediate Fix |
| :--- | :--- |
| **Backend connection refused** | Verify `python backend/run.py` is running on port 8000; check terminal for port conflict. |
| **Web Speech audio silent** | Check system volume; ensure Chrome/Edge browser permissions allow audio playback on localhost. |
| **Sample image fails to render** | Refresh browser (`Ctrl+F5`); verify `public/brand/` SVGs and static uploads exist. |
| **Examiner requests custom file upload** | Use the drag-and-drop zone with any JPEG/PNG prescription slip; system will process live. |
