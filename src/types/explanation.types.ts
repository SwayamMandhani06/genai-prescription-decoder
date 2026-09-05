export type LanguageCode = 'en' | 'hi' | 'mr';

export interface DosageSlot {
  period: 'morning' | 'afternoon' | 'evening' | 'night';
  amount: string; // e.g. "1 Tablet", "1 Capsule"
  isActive: boolean;
  timeRange: string; // e.g. "08:00 AM - 09:00 AM"
  mealRelation: string; // e.g. "भोजन के बाद (After Food)"
}

export interface PatientMedicationExplanation {
  medicineId: string;
  genericName: string;
  brandName: string;
  localizedName: string;
  purpose: string;
  dosageSummary: string;
  schedule: DosageSlot[];
  foodInstruction: string;
  specialPrecaution: string;
  durationString: string;
  missedDoseAdvice: string;
}

export interface MultilingualExplanationPackage {
  language: LanguageCode;
  languageLabel: string;
  nativeLabel: string;
  overallPatientAdvice: string;
  doctorConsultDisclaimer: string;
  medications: PatientMedicationExplanation[];
}
