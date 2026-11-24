export interface SolarObservation {
  id?: string;
  timestamp: string;
  satelliteId: string;
  shortFlux: number;
  longFlux: number;
  ratio?: number;
  source: string;
  qualityStatus: 'GOOD' | 'QUESTIONABLE' | 'BAD' | 'MISSING';
}

export interface SolarFlareEvent {
  eventId: string;
  beginTime: string;
  peakTime: string;
  endTime?: string;
  flareClass: string;
  classCategory?: string;
  peakFlux?: number;
  sourceLocation?: string;
  source: string;
  verificationStatus?: 'CONFIRMED' | 'UNVERIFIED';
}

export interface ForecastResult {
  _id?: string;
  generatedAt: string;
  observationTimestamp: string;
  forecastHorizonHours: number;
  probabilityMPlus: number;
  probabilityXPlus: number | null;
  riskLevel: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  modelVersion: string;
  modelName: string;
  baselineProbability: number;
  dataFreshness: 'FRESH' | 'STALE' | 'UNAVAILABLE';
  actualOutcome?: boolean | null;
  verificationStatus?: 'PENDING' | 'VERIFIED_POSITIVE' | 'VERIFIED_NEGATIVE';
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  database: {
    connected: boolean;
    readyState: number;
    host: string;
    name: string;
  };
  mlService: {
    status: string;
    service?: string;
    python_version?: string;
    model_loaded?: boolean;
    available_model_version?: string;
  };
}

export interface ModelMetricsSummary {
  modelName: string;
  modelVersion: string;
  evaluationPeriod: {
    testStart: string;
    testEnd: string;
    testSamples: number;
    positiveCount: number;
    negativeCount: number;
  };
  metrics: {
    brierScore: number;
    baselineBrierScore: number;
    brierSkillScore: number;
    tss: number;
    rocAuc: number;
    prAuc: number;
    precision: number;
    recall: number;
    f1Score: number;
    classificationThreshold: number;
  };
  featureImportance: { feature: string; importance: number }[];
}
