/**
 * Pure mobile API client implementing the frozen MedicalPlab API Contract.
 * Sourced directly from docs/mobile-handoff/API_CONTRACT.md.
 * 
 * Invariant: Backend remains authoritative for correctness, scoring, and lifecycle.
 * The client never computes or overrides learning state.
 */

import type {
  LearnerState,
  AdaptiveRecommendation,
  RemediationTurnResponse,
  RemediationSessionResponse,
  TransferItemDTO,
  TransferSubmissionResponse,
} from "../../lib/types";

export interface UniversitySubjectItem {
  name: string;
  count: number;
}

export interface UniversityTopicItem {
  name: string;
  count: number;
}

export interface UniversityQuestionPayload {
  id: string;
  track: string;
  stem: string;
  subject: string;
  topic: string;
  options: Record<string, string>;
  difficulty: string;
}

export interface UniversityQuestionResponse {
  question: UniversityQuestionPayload | null;
  position?: number;
  total?: number;
  next_action?: string;
}

export interface UniversityAnswerResponse {
  question_id: string;
  is_correct: boolean;
  correct_answer: string;
  explanation: string;
  subject: string;
  topic: string;
  source: {
    title?: string;
    url?: string;
    license?: string;
  };
  next_action: string;
  progress: any;
}

export const MOBILE_LEARNER_KEY = "medicalplab.mobile.learner.v1";
export const ACTIVE_SESSION_KEY = "medicalplab.mobile.active_session.v1";

const DEFAULT_API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

export class MobileApiClient {
  private baseUrl: string;
  private learnerId: string | null = null;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || DEFAULT_API_BASE_URL;
  }

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/+$/, "");
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  getLearnerId(): string {
    if (this.learnerId && this.learnerId.trim()) {
      return this.learnerId.trim();
    }
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem(MOBILE_LEARNER_KEY);
        if (stored && stored.trim()) {
          this.learnerId = stored.trim();
          return this.learnerId;
        }
        const newId = `uni-${crypto.randomUUID()}`;
        localStorage.setItem(MOBILE_LEARNER_KEY, newId);
        this.learnerId = newId;
        return newId;
      } catch {
        // Fallback below
      }
    }
    return "demo-student-001";
  }

  setLearnerId(id: string) {
    this.learnerId = id.trim();
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(MOBILE_LEARNER_KEY, this.learnerId);
      } catch {
        // storage fallback
      }
    }
  }

  resetIdentity(): string {
    if (typeof window !== "undefined") {
      try {
        const newId = `uni-${crypto.randomUUID()}`;
        localStorage.setItem(MOBILE_LEARNER_KEY, newId);
        localStorage.removeItem(ACTIVE_SESSION_KEY);
        this.learnerId = newId;
        return newId;
      } catch {
        // storage fallback
      }
    }
    return "demo-student-001";
  }

  getActiveSessionId(): string | null {
    if (typeof window !== "undefined") {
      try {
        return localStorage.getItem(ACTIVE_SESSION_KEY);
      } catch {
        return null;
      }
    }
    return null;
  }

  setActiveSessionId(sessionId: string | null) {
    if (typeof window !== "undefined") {
      try {
        if (sessionId) {
          localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
        } else {
          localStorage.removeItem(ACTIVE_SESSION_KEY);
        }
      } catch {
        // storage fallback
      }
    }
  }

  private getHeaders(): HeadersInit {
    return {
      "Content-Type": "application/json",
      "X-User-Id": this.getLearnerId(),
    };
  }

  private async handleResponse<T>(res: Response, endpoint: string): Promise<T> {
    if (!res.ok) {
      let detail = `Endpoint ${endpoint} returned HTTP ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson && typeof errJson.detail === "string") {
          detail = errJson.detail;
        }
      } catch {
        // retain fallback
      }
      const error = new Error(detail) as Error & { status: number; endpoint: string };
      error.status = res.status;
      error.endpoint = endpoint;
      throw error;
    }
    return res.json() as Promise<T>;
  }

  // 1. Subjects & Topics
  async getSubjects(): Promise<UniversitySubjectItem[]> {
    const res = await fetch(`${this.baseUrl}/api/v1/university/subjects`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    const data = await this.handleResponse<{ items: UniversitySubjectItem[] }>(res, "/api/v1/university/subjects");
    return data.items || [];
  }

  async getTopics(subject: string): Promise<UniversityTopicItem[]> {
    const res = await fetch(`${this.baseUrl}/api/v1/university/topics?subject=${encodeURIComponent(subject)}`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    const data = await this.handleResponse<{ items: UniversityTopicItem[] }>(res, "/api/v1/university/topics");
    return data.items || [];
  }

  // 2. Question Retrieval
  async getQuestion(subject: string, topic: string, after?: string): Promise<UniversityQuestionResponse> {
    let url = `${this.baseUrl}/api/v1/university/question?subject=${encodeURIComponent(subject)}&topic=${encodeURIComponent(topic)}`;
    if (after) {
      url += `&after=${encodeURIComponent(after)}`;
    }
    const res = await fetch(url, {
      method: "GET",
      headers: this.getHeaders(),
    });
    return this.handleResponse<UniversityQuestionResponse>(res, "/api/v1/university/question");
  }

  // 3. Answer Submission
  async submitAnswer(
    questionId: string,
    selectedOption: string,
    idempotencyKey?: string
  ): Promise<UniversityAnswerResponse> {
    const key = idempotencyKey || `att-${crypto.randomUUID()}`;
    const res = await fetch(`${this.baseUrl}/api/v1/university/answer`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({
        question_id: questionId,
        selected_option: selectedOption,
        idempotency_key: key,
      }),
    });
    return this.handleResponse<UniversityAnswerResponse>(res, "/api/v1/university/answer");
  }

  // 4. Adaptive State & Recommendation
  async getAdaptiveRecommendation(): Promise<AdaptiveRecommendation | null> {
    const res = await fetch(`${this.baseUrl}/api/v1/adaptive/recommendation`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    return this.handleResponse<AdaptiveRecommendation | null>(res, "/api/v1/adaptive/recommendation");
  }

  async getAdaptiveState(): Promise<LearnerState> {
    const res = await fetch(`${this.baseUrl}/api/v1/adaptive/state`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    return this.handleResponse<LearnerState>(res, "/api/v1/adaptive/state");
  }

  // 5. Socratic Remediation Loop
  async startRemediation(
    questionId: string,
    selectedOption: string,
    attemptId?: string,
    idempotencyKey?: string
  ): Promise<RemediationTurnResponse> {
    const key = idempotencyKey || `rem-start-${crypto.randomUUID()}`;
    const res = await fetch(`${this.baseUrl}/api/v1/remediation/start`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({
        question_id: questionId,
        selected_option: selectedOption,
        attempt_id: attemptId || null,
        idempotency_key: key,
      }),
    });
    const result = await this.handleResponse<RemediationTurnResponse>(res, "/api/v1/remediation/start");
    if (result.session_id) {
      this.setActiveSessionId(result.session_id);
    }
    return result;
  }

  async submitRemediationTurn(
    sessionId: string,
    studentMessage: string,
    idempotencyKey?: string
  ): Promise<RemediationTurnResponse> {
    const key = idempotencyKey || `turn-${crypto.randomUUID()}`;
    const res = await fetch(`${this.baseUrl}/api/v1/remediation/turn`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({
        session_id: sessionId,
        student_message: studentMessage,
        idempotency_key: key,
      }),
    });
    return this.handleResponse<RemediationTurnResponse>(res, "/api/v1/remediation/turn");
  }

  // 6. Independent Held-Out Transfer
  async getTransferItem(sessionId: string): Promise<TransferItemDTO> {
    const res = await fetch(`${this.baseUrl}/api/v1/remediation/session/${encodeURIComponent(sessionId)}/transfer`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    return this.handleResponse<TransferItemDTO>(res, `/api/v1/remediation/session/${sessionId}/transfer`);
  }

  async submitTransfer(
    sessionId: string,
    questionId: string,
    selectedOption: string,
    wasAssisted: boolean = false,
    idempotencyKey?: string
  ): Promise<TransferSubmissionResponse> {
    const key = idempotencyKey || `trans-${crypto.randomUUID()}`;
    const res = await fetch(`${this.baseUrl}/api/v1/remediation/session/${encodeURIComponent(sessionId)}/transfer`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        selected_option: selectedOption,
        was_assisted: wasAssisted,
        idempotency_key: key,
      }),
    });
    const result = await this.handleResponse<TransferSubmissionResponse>(
      res,
      `/api/v1/remediation/session/${sessionId}/transfer`
    );
    // On completed transfer, clear active session
    this.setActiveSessionId(null);
    return result;
  }

  // 7. Session Resume & Abandon
  async getRemediationSession(sessionId: string): Promise<RemediationSessionResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/remediation/session/${encodeURIComponent(sessionId)}`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    return this.handleResponse<RemediationSessionResponse>(res, `/api/v1/remediation/session/${sessionId}`);
  }

  async abandonRemediation(sessionId: string): Promise<RemediationTurnResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/remediation/session/${encodeURIComponent(sessionId)}/abandon`, {
      method: "POST",
      headers: this.getHeaders(),
    });
    const result = await this.handleResponse<RemediationTurnResponse>(
      res,
      `/api/v1/remediation/session/${sessionId}/abandon`
    );
    this.setActiveSessionId(null);
    return result;
  }
}

export const mobileApi = new MobileApiClient();
