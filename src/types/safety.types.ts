import { BoundingBox } from './prescription.types';

export type LasaRiskTier = 'CRITICAL' | 'HIGH' | 'MODERATE';

export interface LasaWarning {
  id: string;
  prescribedDrug: string;
  prescribedDose: string;
  confusableWith: string;
  confusableDose: string;
  orthographicSimilarity: number; // e.g. 0.84 (Levenshtein based)
  phoneticSimilarity: number; // e.g. 0.91 (Double Metaphone based)
  riskTier: LasaRiskTier;
  pharmacologicalDifference: string;
  clinicalDangerNotice: string;
  differentiationKey: string; // e.g. "TALL MAN Lettering: celeCOXIB vs celeXA"
}

export type AbstentionField = 'drug_name' | 'dosage_strength' | 'dosage_unit' | 'frequency' | 'duration';

export interface AbstentionAlert {
  id: string;
  field: AbstentionField;
  rawInkToken: string;
  calibratedEntropy: number; // e.g. 0.78 (high entropy = high uncertainty)
  abstentionThreshold: number; // e.g. 0.65
  reason: string;
  suspectedCandidates: string[];
  mandatoryClinicalAction: string;
  boundingBox: BoundingBox;
}

export interface DrugInteractionAlert {
  id: string;
  primaryDrug: string;
  secondaryDrug: string;
  severity: 'MAJOR' | 'MODERATE' | 'MINOR';
  effectDescription: string;
  mechanism: string;
}
