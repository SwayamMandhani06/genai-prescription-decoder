export type AppView = 'home' | 'upload' | 'processing' | 'results';

export interface ImageQualityMetrics {
  width: number;
  height: number;
  fileSizeBytes: number;
  fileSizeFormatted: string;
  mimeType: string;
  aspectRatio: string;
  orientation: 'Portrait' | 'Landscape' | 'Square';
  estimatedDpi: number;
  contrastScore: 'High' | 'Moderate' | 'Low';
  readabilityScore: number; // 0 - 100
  qualityStatus: 'OPTIMAL' | 'ACCEPTABLE' | 'DEGRADED_WARNING';
  statusMessage: string;
}

export interface UploadedPrescriptionFile {
  file: File | null;
  previewUrl: string;
  fileName: string;
  source: 'user_upload' | 'curated_sample';
  sampleId?: string;
  metrics: ImageQualityMetrics;
}
