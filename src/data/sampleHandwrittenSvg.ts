export interface HandwrittenStrokeLine {
  id: string;
  label: string;
  medicineId: string;
  svgPath: string;
  inkColor: string;
  boundingBox: { x: number; y: number; width: number; height: number };
  pixelCoords: string;
}

export interface PrescriptionSvgCanvasData {
  id: string;
  accessionId: string;
  doctorHeader: {
    name: string;
    qualifications: string;
    regNo: string;
    clinicName: string;
    clinicAddress: string;
    phone: string;
  };
  patientInfo: {
    name: string;
    ageGender: string;
    date: string;
    vitals: string;
    weight: string;
  };
  rxSymbolPath: string;
  strokes: HandwrittenStrokeLine[];
  paperType: 'standard_pad' | 'hospital_stationery';
  doctorSignaturePath: string;
  clinicStampText: string;
}

export const SAMPLE_PRESCRIPTION_CANVASES: Record<string, PrescriptionSvgCanvasData> = {
  'rx-sample-1': {
    id: 'rx-sample-1',
    accessionId: 'DOC-PUN-2025-0842-A',
    doctorHeader: {
      name: 'Dr. Arvind Deshmukh, M.D. (Internal Medicine)',
      qualifications: 'F.C.P.S. (Mumbai), Senior Consulting Physician',
      regNo: 'Reg: MMC / 2014 / 08 / 3412',
      clinicName: 'PULSE CARE CLINICAL CONSULTANCY',
      clinicAddress: '402, Shivajinagar Medical Enclave, Pune - 411005',
      phone: '+91 20 2553 4910',
    },
    patientInfo: {
      name: 'Mr. Suresh Patwardhan',
      ageGender: '48Y / M',
      date: '14-Oct-2025',
      vitals: 'BP: 132/84 | SpO2: 97% | Temp: 101.4°F',
      weight: '68 kg',
    },
    rxSymbolPath:
      'M 24 135 C 28 105, 46 95, 62 102 C 78 108, 76 130, 58 138 C 42 144, 30 155, 26 178 M 46 142 L 72 178 M 40 156 L 68 152',
    paperType: 'standard_pad',
    clinicStampText: 'PULSE CARE OPD · VERIFIED & SIGNED',
    doctorSignaturePath:
      'M 420 375 C 435 355, 455 350, 475 365 C 495 380, 510 350, 530 360 C 550 370, 565 355, 585 365 M 460 380 L 560 376',
    strokes: [
      {
        id: 'stroke-1',
        label: 'Tab. Augmentin 625 Duo  1 - 0 - 1 x 5d  (P.C.)',
        medicineId: 'med-1',
        // Authentic cursive character contours: Tab (T..b), Augmentin (A-u-g-m-e-n-t-i-n), 625, 1-0-1, 5d, PC
        svgPath:
          'M 85 142 C 95 130, 115 130, 110 148 M 102 135 L 128 144 C 138 140, 145 132, 155 142 C 165 140, 172 148, 185 138 C 195 136, 205 144, 218 139 C 228 136, 238 146, 250 140 C 265 138, 275 146, 290 141 C 305 138, 318 144, 335 140 M 350 138 C 362 130, 375 148, 385 136 C 395 138, 405 146, 415 139 M 435 142 C 445 138, 455 146, 465 140 M 478 142 C 488 138, 498 146, 508 140 M 520 142 C 535 135, 550 146, 565 140 M 580 138 C 595 134, 610 144, 625 140',
        inkColor: '#1E3A8A',
        boundingBox: { x: 10, y: 31, width: 84, height: 13 },
        pixelCoords: 'x: 68, y: 128, w: 560, h: 42',
      },
      {
        id: 'stroke-2',
        label: 'Cap. Pan 40mg  1 - 0 - 0 x 5d  (A.C. 30m before breakfast)',
        medicineId: 'med-2',
        // Cursive: Cap Pan 40, 1-0-0, AC
        svgPath:
          'M 85 198 C 98 185, 118 188, 125 204 C 135 195, 148 198, 160 202 M 175 194 C 190 188, 205 205, 220 196 C 235 192, 250 204, 268 198 M 285 196 C 298 190, 315 202, 330 196 M 350 198 C 365 192, 380 202, 395 196 M 415 198 C 430 194, 445 202, 460 197 M 480 196 C 500 190, 520 204, 545 198 C 565 195, 590 204, 615 198',
        inkColor: '#1E3A8A',
        boundingBox: { x: 10, y: 47, width: 84, height: 13 },
        pixelCoords: 'x: 68, y: 184, w: 560, h: 42',
      },
      {
        id: 'stroke-3',
        label: 'Tab. Dolo 650mg  1 - 0 - 1  S.O.S. (if fever > 100°F)',
        medicineId: 'med-3',
        // Cursive: Tab Dolo 650, 1-0-1 SOS
        svgPath:
          'M 85 258 C 98 245, 118 248, 128 264 M 140 252 C 158 245, 175 264, 195 254 C 210 248, 228 262, 245 256 M 260 254 C 275 248, 295 262, 315 255 M 335 256 C 352 250, 370 262, 390 256 M 410 254 C 428 248, 445 264, 465 254 M 485 252 C 510 246, 535 262, 560 256 C 580 252, 605 260, 625 256',
        inkColor: '#1E3A8A',
        boundingBox: { x: 10, y: 62, width: 84, height: 13 },
        pixelCoords: 'x: 68, y: 242, w: 560, h: 42',
      },
    ],
  },
  'rx-sample-2': {
    id: 'rx-sample-2',
    accessionId: 'DOC-CHE-2025-1194-B',
    doctorHeader: {
      name: 'Dr. Meenakshi Sundaram, M.D., D.M. (Endocrinology)',
      qualifications: 'Senior Consultant Diabetologist & Lipid Specialist',
      regNo: 'Reg: TN / MC / 2011 / 4491',
      clinicName: 'METABOLIC & CARDIOVASCULAR SUITE',
      clinicAddress: '18, Cathedral Road, Gopalapuram, Chennai - 600086',
      phone: '+91 44 2811 0922',
    },
    patientInfo: {
      name: 'Mrs. Rukmini K. Sharma',
      ageGender: '56Y / F',
      date: '19-Nov-2025',
      vitals: 'HbA1c: 8.6% | FBS: 168 mg/dL | Serum Cr: 0.9',
      weight: '62 kg',
    },
    rxSymbolPath:
      'M 24 135 C 28 105, 46 95, 62 102 C 78 108, 76 130, 58 138 C 42 144, 30 155, 26 178 M 46 142 L 72 178 M 40 156 L 68 152',
    paperType: 'hospital_stationery',
    clinicStampText: 'DIABETIC CLINIC CHENNAI · VERIFIED',
    doctorSignaturePath:
      'M 430 365 C 450 345, 480 345, 500 360 C 520 375, 545 350, 570 362 M 450 375 L 560 370',
    strokes: [
      {
        id: 'stroke-lasa-1',
        label: 'Tab. Metformin 500mg  1 - 0 - 1  (with meals)',
        medicineId: 'med-lasa-1',
        svgPath:
          'M 85 146 C 100 132, 120 135, 135 152 C 150 142, 170 145, 190 142 C 215 138, 235 148, 260 142 C 285 138, 310 148, 335 142 M 355 140 C 375 134, 400 148, 420 142 M 440 142 C 460 138, 480 146, 505 141 C 530 138, 560 148, 595 142',
        inkColor: '#0F172A',
        boundingBox: { x: 10, y: 32, width: 84, height: 14 },
        pixelCoords: 'x: 68, y: 132, w: 560, h: 44',
      },
      {
        id: 'stroke-lasa-2',
        label: 'Tab. Telmisartan 40mg  1 - 0 - 0  (O.D. Morning P.C.)',
        medicineId: 'med-lasa-2',
        svgPath:
          'M 85 208 C 102 195, 122 198, 138 214 M 150 205 C 172 196, 195 212, 220 206 C 245 200, 270 214, 295 208 M 315 206 C 335 200, 360 212, 385 206 M 405 208 C 428 202, 452 214, 480 207 C 505 202, 535 212, 570 208',
        inkColor: '#0F172A',
        boundingBox: { x: 10, y: 50, width: 84, height: 13 },
        pixelCoords: 'x: 68, y: 195, w: 560, h: 42',
      },
    ],
  },
  'rx-sample-3': {
    id: 'rx-sample-3',
    accessionId: 'DOC-NAG-2025-0319-C',
    doctorHeader: {
      name: 'Dr. Rajeshwari Kulkarni, M.D. (Paediatrics)',
      qualifications: 'Diploma in Child Health (DCH), Paediatric Pulmonologist',
      regNo: 'Reg: MMC / 2008 / 1932',
      clinicName: 'SHISHU SEVA CHILDREN HOSPITAL',
      clinicAddress: 'Central Avenue, Ramdaspeth, Nagpur - 440010',
      phone: '+91 712 242 8190',
    },
    patientInfo: {
      name: 'Master Aarav Joshi',
      ageGender: '7Y / M',
      date: '02-Dec-2025',
      vitals: 'Bilateral wheezing | SpO2: 94% on room air',
      weight: '21 kg',
    },
    rxSymbolPath:
      'M 24 135 C 28 105, 46 95, 62 102 C 78 108, 76 130, 58 138 C 42 144, 30 155, 26 178 M 46 142 L 72 178 M 40 156 L 68 152',
    paperType: 'hospital_stationery',
    clinicStampText: 'PAEDIATRIC OPD · URGENT CLINICAL SCRIPT',
    doctorSignaturePath:
      'M 420 370 C 445 350, 475 350, 505 365 C 530 380, 555 350, 580 365 M 445 380 L 565 375',
    strokes: [
      {
        id: 'stroke-abs-1',
        label: 'Syr. Levolin (1mg / 5ml)  5ml T.D.S. x 5d',
        medicineId: 'med-abs-1',
        svgPath:
          'M 85 144 C 102 130, 122 134, 138 152 M 150 142 C 172 136, 195 152, 220 146 C 245 140, 270 154, 298 146 M 320 144 C 345 138, 375 152, 405 145 C 430 140, 460 152, 495 146 M 520 144 C 548 138, 575 152, 610 146',
        inkColor: '#1E3A8A',
        boundingBox: { x: 10, y: 31, width: 84, height: 13 },
        pixelCoords: 'x: 68, y: 130, w: 560, h: 42',
      },
      {
        id: 'stroke-abs-2',
        label: 'Tab. Prednisolone  [1.0mg vs 10mg]  1 - 0 - 0 x 3d  (AMBIGUOUS)',
        medicineId: 'med-abs-2',
        // Degraded decimal ligature showing why model abstains
        svgPath:
          'M 85 204 C 105 190, 128 194, 145 212 M 160 202 C 185 195, 215 212, 245 206 C 275 200, 305 215, 335 208 M 345 208 C 352 195, 362 225, 372 208 C 382 198, 395 212, 410 206 M 435 206 C 465 200, 495 214, 530 208 C 555 204, 585 214, 615 208',
        inkColor: '#1E3A8A',
        boundingBox: { x: 10, y: 48, width: 84, height: 15 },
        pixelCoords: 'x: 68, y: 190, w: 560, h: 48',
      },
      {
        id: 'stroke-abs-3',
        label: 'Syr. Montair LC Kid  5ml at bedtime (H.S.) x 14d',
        medicineId: 'med-abs-3',
        svgPath:
          'M 85 264 C 102 250, 124 254, 140 272 M 152 262 C 175 255, 200 272, 228 266 C 255 260, 285 274, 315 268 M 338 266 C 365 260, 395 274, 428 268 M 450 268 C 480 262, 510 274, 545 268 C 570 264, 600 272, 625 268',
        inkColor: '#1E3A8A',
        boundingBox: { x: 10, y: 64, width: 84, height: 13 },
        pixelCoords: 'x: 68, y: 250, w: 560, h: 42',
      },
    ],
  },
};
