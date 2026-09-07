export interface ResearchMetric {
  id: string;
  metric: string;
  definition: string;
  traditionalOcr: string; // e.g. "Simulated Baseline"
  generalVlm: string; // e.g. "Simulated Baseline"
  auraRxModel: string; // e.g. "Design Target"
  improvement: string;
  isLowerBetter: boolean;
  isIllustrative?: boolean;
}

export interface DatasetSummary {
  name: string;
  sampleCount: number | string;
  origin: string;
  doctorSpecialties: string[];
  handwritingStyles: string;
  statusTag?: string;
}
