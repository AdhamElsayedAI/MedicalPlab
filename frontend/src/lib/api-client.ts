import {
  PLABEvaluationResult,
  PLABProgress,
  PLABQuestionPublic,
  StudentMasteryProfile,
} from './types';
import type {
  CourseLearningRequest,
  CourseLearningResponse,
  AnatomyCommandRequest,
  AnatomyCommandResponse,
  TutorChatRequest,
  TutorChatResponse,
} from './types';
import { INITIAL_STUDENT_PROFILE } from "./demo-data";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");
const RUNTIME_MODE = (process.env.NEXT_PUBLIC_RUNTIME_MODE || "demo").trim().toLowerCase();
const DEMO_FALLBACKS_ALLOWED = RUNTIME_MODE === "demo" || RUNTIME_MODE === "test";

export class ApiUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiUnavailableError";
  }
}

class PlatformApiClient {
  private userId: string = "user_alice";
  private tenantId: string = "tenant_nhs_demo";

  setUser(userId: string, tenantId: string) {
    this.userId = userId;
    this.tenantId = tenantId;
  }

  getBaseUrl(): string {
    return API_BASE_URL;
  }

  getRuntimeMode(): string {
    return RUNTIME_MODE;
  }

  private getHeaders(): HeadersInit {
    return {
      "Content-Type": "application/json",
      "X-User-Id": this.userId,
      "X-Tenant-Id": this.tenantId,
    };
  }

  async checkHealth(): Promise<{
    status: string;
    service: string;
    isOnline: boolean;
    uptime_seconds?: number;
    runtime_mode?: string;
    demo_fallbacks_enabled?: boolean;
  }> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: "GET",
        headers: this.getHeaders(),
        signal: controller.signal,
      });
      if (response.ok) {
        const data = await response.json();
        return { ...data, isOnline: true };
      }
    } catch {
      // Explicit offline state below.
    } finally {
      clearTimeout(timeoutId);
    }
    return { status: "offline", service: "MedicalPlab API", isOnline: false };
  }

  async sendAIQuery(prompt: string): Promise<{
    explanation: string;
    intent: string;
    next_actions: string[];
    citations?: unknown[];
    latency_ms: number;
    safety_validated: boolean;
    demo_fallback?: boolean;
    runtime_mode?: string;
    model_name?: string;
  }> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(`${API_BASE_URL}/ai/chat`, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify({ query: prompt }),
        signal: controller.signal,
      });

      if (response.ok) {
        const data = await response.json();
        return {
          explanation: data.explanation || "",
          intent: data.intent || "teaching",
          next_actions: data.next_actions || [],
          latency_ms: Number(data.latency_ms ?? 0),
          safety_validated: data.safety_validated === true,
          citations: data.citations || [],
          demo_fallback: data.demo_fallback === true,
          runtime_mode: data.runtime_mode,
          model_name: data.model_name,
        };
      }

      let detail = `MedicalPlab API returned HTTP ${response.status}.`;
      try {
        const errorData = await response.json();
        detail = errorData.message || errorData.error || detail;
      } catch {
        // Keep status-based detail.
      }
      throw new ApiUnavailableError(detail);
    } catch (error) {
      if (DEMO_FALLBACKS_ALLOWED) {
        return this.fallbackClinicalAI(prompt);
      }
      if (error instanceof ApiUnavailableError) {
        throw error;
      }
      throw new ApiUnavailableError(
        "MedicalPlab AI is unavailable. Pilot/production mode does not fabricate a clinical response."
      );
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async getStudentAnalytics(): Promise<StudentMasteryProfile> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(`${API_BASE_URL}/student/analytics`, {
        method: "GET",
        headers: this.getHeaders(),
        signal: controller.signal,
      });
      if (response.ok) {
        const data = await response.json();
        return {
          ...INITIAL_STUDENT_PROFILE,
          overallAccuracy: data.overall_accuracy ?? INITIAL_STUDENT_PROFILE.overallAccuracy,
          totalAttempts: data.total_attempts ?? INITIAL_STUDENT_PROFILE.totalAttempts,
          weakTopics: data.weak_topics?.length ? data.weak_topics : INITIAL_STUDENT_PROFILE.weakTopics,
        };
      }
      throw new ApiUnavailableError(`Student analytics returned HTTP ${response.status}.`);
    } catch (error) {
      if (DEMO_FALLBACKS_ALLOWED) {
        return INITIAL_STUDENT_PROFILE;
      }
      if (error instanceof ApiUnavailableError) {
        throw error;
      }
      throw new ApiUnavailableError("Student analytics are unavailable.");
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async recordAttempt(topic: string, isCorrect: boolean): Promise<boolean> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(`${API_BASE_URL}/student/attempts`, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify({ topic, is_correct: isCorrect, time_spent_seconds: 28.0 }),
        signal: controller.signal,
      });
      return response.ok;
    } catch {
      // Never report a successful write that the server did not acknowledge.
      return false;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async getPLABQuestions(): Promise<PLABQuestionPublic[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/plab/questions`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new ApiUnavailableError(`PLAB questions returned HTTP ${response.status}.`);
    }
    const body = await response.json();
    return Array.isArray(body.items) ? body.items : [];
  }

  async getPLABQuestion(questionId: string): Promise<PLABQuestionPublic> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/plab/questions/${encodeURIComponent(questionId)}`,
      { method: "GET", headers: this.getHeaders() }
    );
    if (!response.ok) {
      throw new ApiUnavailableError(`PLAB question returned HTTP ${response.status}.`);
    }
    return response.json();
  }

  async evaluatePLABAnswer(input: {
    questionId: string;
    selectedOption: "A" | "B" | "C" | "D" | "E";
    idempotencyKey: string;
    responseTimeMs?: number;
  }): Promise<PLABEvaluationResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/plab/evaluate`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({
        question_id: input.questionId,
        selected_option: input.selectedOption,
        idempotency_key: input.idempotencyKey,
        response_time_ms: input.responseTimeMs,
      }),
    });
    if (!response.ok) {
      throw new ApiUnavailableError(`PLAB evaluation returned HTTP ${response.status}.`);
    }
    return response.json();
  }

  async getPLABProgress(): Promise<PLABProgress> {
    const response = await fetch(`${API_BASE_URL}/api/v1/plab/progress`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new ApiUnavailableError(`PLAB progress returned HTTP ${response.status}.`);
    }
    return response.json();
  }

  async queryCourseLearning(input: CourseLearningRequest): Promise<CourseLearningResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/learn/query`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(input),
    });
    if (!response.ok) {
      throw new ApiUnavailableError(`Course learning returned HTTP ${response.status}.`);
    }
    return response.json();
  }

  async sendAnatomyCommand(input: AnatomyCommandRequest): Promise<AnatomyCommandResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/anatomy/command`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(input),
    });
    if (!response.ok) {
      throw new ApiUnavailableError(`Anatomy command returned HTTP ${response.status}.`);
    }
    return response.json();
  }

  async sendTutorChat(request: TutorChatRequest): Promise<TutorChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tutor/chat`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      // If 404 on canonical route, attempt fallback to legacy /ai/chat
      if (response.status === 404) {
        const legacyResp = await fetch(`${API_BASE_URL}/ai/chat`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify(request),
        });
        if (legacyResp.ok) {
          const lData = await legacyResp.json();
          if (lData.tutor_response) {
            return lData.tutor_response;
          }
        }
      }
      const errorText = await response.text();
      throw new Error(`Tutor chat failed (${response.status}): ${errorText}`);
    }

    return response.json();
  }


  private fallbackClinicalAI(prompt: string) {
    const pLower = prompt.toLowerCase();
    let explanation = "";
    let citations: Array<Record<string, unknown>> = [];

    if (pLower.includes("lad") || pLower.includes("stemi") || pLower.includes("coronary")) {
      explanation =
        "DEMO ONLY: The Left Anterior Descending (LAD) artery provides perfusion to the anterior ventricular septum and apex. This client-side fallback is presentation content and must not be counted as a model or clinical benchmark result.";
      citations = [
        {
          ref: "DEMO-NICE-NG185",
          guideline: "Demo reference only",
          section: "Not validated by live RAG",
          status: "demo",
        },
      ];
    } else if (pLower.includes("tamponade") || pLower.includes("beck")) {
      explanation =
        "DEMO ONLY: Cardiac tamponade teaching content is being shown because the live API is unavailable. This is not a model-generated or evidence-verified result.";
      citations = [
        {
          ref: "DEMO-TAMPONADE",
          guideline: "Demo reference only",
          section: "Not validated by live RAG",
          status: "demo",
        },
      ];
    } else {
      explanation =
        "DEMO ONLY: MedicalPlab is offline, so this screen is displaying a non-clinical placeholder rather than fabricating a grounded answer.";
    }

    return {
      explanation,
      intent: "demo_fallback",
      next_actions: ["Reconnect to MedicalPlab API"],
      citations,
      latency_ms: 0,
      safety_validated: false,
      demo_fallback: true,
      runtime_mode: RUNTIME_MODE,
      model_name: "demo-fallback",
    };
  }
}

export const api = new PlatformApiClient();

