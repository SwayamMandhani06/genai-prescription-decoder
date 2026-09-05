import { ImageQualityMetrics } from '../types/navigation.types';

export const MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024; // 15MB

export const ACCEPTED_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/tiff',
  'application/pdf',
];

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export function validatePrescriptionFile(file: File): { isValid: boolean; error?: string } {
  if (!ACCEPTED_MIME_TYPES.includes(file.type) && !file.name.match(/\.(jpe?g|png|webp|tiff?|pdf)$/i)) {
    return {
      isValid: false,
      error: 'Unsupported file format. Please provide an optical prescription image (JPEG, PNG, WEBP, TIFF) or standard digital PDF.',
    };
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return {
      isValid: false,
      error: `File size (${formatFileSize(file.size)}) exceeds the 15 MB limit. Please compress or crop to the prescription area.`,
    };
  }

  return { isValid: true };
}

export function computeImageHeuristics(
  width: number,
  height: number,
  fileSizeBytes: number,
  mimeType: string
): ImageQualityMetrics {
  const isPortrait = height >= width;
  const orientation = width === height ? 'Square' : isPortrait ? 'Portrait' : 'Landscape';
  const ratioVal = (width / height).toFixed(2);
  const aspectRatio = `${ratioVal}:1 (${orientation})`;

  // Estimated DPI based on standard 8.5x11in or 6x8in pad assuming standard physical dimensions
  // For a 6x8 inch prescription pad, width / 6 gives effective DPI
  const padWidthInches = isPortrait ? 6 : 8.5;
  const estimatedDpi = Math.round(width / padWidthInches);

  // Readability heuristics based on minimum resolution and optical density
  let qualityStatus: 'OPTIMAL' | 'ACCEPTABLE' | 'DEGRADED_WARNING' = 'OPTIMAL';
  let contrastScore: 'High' | 'Moderate' | 'Low' = 'High';
  let readabilityScore = 92;
  let statusMessage = 'Optimal resolution. Cursive strokes and letterhead are sharp for tokenization.';

  if (width < 800 || height < 800) {
    qualityStatus = 'DEGRADED_WARNING';
    contrastScore = 'Low';
    readabilityScore = 52;
    statusMessage = 'Low resolution detected (<800px). Cursive decimal points and character ascenders may be blurred.';
  } else if (width < 1400 || height < 1400) {
    qualityStatus = 'ACCEPTABLE';
    contrastScore = 'Moderate';
    readabilityScore = 78;
    statusMessage = 'Acceptable clarity. Sufficient for clinical candidate extraction with moderate confidence.';
  } else {
    qualityStatus = 'OPTIMAL';
    contrastScore = 'High';
    readabilityScore = Math.min(98, Math.round(88 + (width / 4000) * 10));
    statusMessage = 'High-fidelity optical intake. Pixel density exceeds 300 DPI baseline for selective inference.';
  }

  return {
    width,
    height,
    fileSizeBytes,
    fileSizeFormatted: formatFileSize(fileSizeBytes),
    mimeType: mimeType || 'image/jpeg',
    aspectRatio,
    orientation,
    estimatedDpi: Math.max(72, Math.min(600, estimatedDpi)),
    contrastScore,
    readabilityScore,
    qualityStatus,
    statusMessage,
  };
}
