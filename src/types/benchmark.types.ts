export interface ResearchMetric {
  id: string;
  metric: string;
  definition: string;
  traditionalOcr: string; // e.g. "Tesseract 5.3"
  generalVlm: string; // e.g. "Zero-shot Multimodal LLM"
  auraRxModel: string; // e.g. "AURA-Rx (Proposed Grounded Pipeline)"
  improvement: string;
  isLowerBetter: boolean;
}

export interface DatasetSummary {
  name: string;
  sampleCount: number;
  origin: string;
  doctorSpecialties: string[];
  handwritingStyles: string;
}
