# MedicalPlab — Mobile Client Integration Examples
**Target Ecosystems:** Flutter (Dart 3.x) & React Native (TypeScript 5.x / Expo)  
**Protocol:** REST / JSON over HTTPS / HTTP  
**Identity Contract:** `X-User-Id` header (Pilot Learner Partitioning)

---

## 1. Flutter / Dart Example

A lightweight, production-ready client using `http` with timeouts, error mapping, and idempotency keys.

```dart
// lib/medicalplab_api_client.dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class MedicalPlabClient {
  final String baseUrl;
  final String learnerId;
  final http.Client _httpClient;
  final Duration timeout;

  MedicalPlabClient({
    required this.baseUrl,
    required this.learnerId,
    http.Client? httpClient,
    this.timeout = const Duration(seconds: 15),
  }) : _httpClient = httpClient ?? http.Client();

  Map<String, String> _headers([Map<String, String>? extra]) {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-User-Id': learnerId,
      ...?extra,
    };
  }

  /// 1. Health check
  Future<bool> checkHealth() async {
    final url = Uri.parse('$baseUrl/health');
    final response = await _httpClient.get(url).timeout(timeout);
    return response.statusCode == 200;
  }

  /// 2. Fetch Preclinical Question
  Future<Map<String, dynamic>> fetchQuestion({
    required String subject,
    required String topic,
  }) async {
    final uri = Uri.parse('$baseUrl/api/v1/university/question')
        .replace(queryParameters: {'subject': subject, 'topic': topic});
    
    final response = await _httpClient.get(uri, headers: _headers()).timeout(timeout);
    return _handleResponse(response);
  }

  /// 3. Submit Preclinical Answer (with Idempotency Key)
  Future<Map<String, dynamic>> submitAnswer({
    required String questionId,
    required String selectedOption,
    required String idempotencyKey,
  }) async {
    final url = Uri.parse('$baseUrl/api/v1/university/answer');
    final body = jsonEncode({
      'question_id': questionId,
      'selected_option': selectedOption,
      'idempotency_key': idempotencyKey,
    });

    final response = await _httpClient.post(url, headers: _headers(), body: body).timeout(timeout);
    return _handleResponse(response);
  }

  /// 4. Socratic Remediation Start
  Future<Map<String, dynamic>> startRemediation({
    required String questionId,
    required String triggerDistractor,
  }) async {
    final url = Uri.parse('$baseUrl/api/v1/remediation/start');
    final body = jsonEncode({
      'learner_id': learnerId,
      'question_id': questionId,
      'trigger_distractor': triggerDistractor,
    });

    final response = await _httpClient.post(url, headers: _headers(), body: body).timeout(timeout);
    return _handleResponse(response);
  }

  /// 5. Submit Held-Out Transfer Item Answer
  Future<Map<String, dynamic>> submitTransferAnswer({
    required String sessionId,
    required String selectedOption,
  }) async {
    final url = Uri.parse('$baseUrl/api/v1/remediation/session/$sessionId/transfer');
    final body = jsonEncode({
      'session_id': sessionId,
      'learner_id': learnerId,
      'selected_option': selectedOption,
    });

    final response = await _httpClient.post(url, headers: _headers(), body: body).timeout(timeout);
    return _handleResponse(response);
  }

  /// 6. Evidence-Grounded AI Tutor Chat
  Future<Map<String, dynamic>> sendTutorQuery({
    required String query,
    String? topic,
    String? sessionId,
    String? learnerId,
  }) async {
    final url = Uri.parse('$baseUrl/api/v1/tutor/chat');
    final body = jsonEncode({
      'query': query,
      if (topic != null) 'topic': topic,
      if (sessionId != null) 'session_id': sessionId,
      if (learnerId != null) 'learner_id': learnerId,
    });

    final response = await _httpClient.post(url, headers: _headers(), body: body).timeout(timeout);
    return _handleResponse(response);
  }

  /// 7. 3D Anatomy Challenge Submit
  Future<Map<String, dynamic>> submitAnatomyChallenge({
    required String sessionId,
    required String selectedStructureId,
  }) async {
    final url = Uri.parse('$baseUrl/api/v1/anatomy/session/$sessionId/challenge');
    final body = jsonEncode({
      'learner_id': learnerId,
      'selected_structure_id': selectedStructureId,
    });

    final response = await _httpClient.post(url, headers: _headers(), body: body).timeout(timeout);
    return _handleResponse(response);
  }

  /// 8. Unified Learner Progress
  Future<Map<String, dynamic>> getProgress() async {
    final url = Uri.parse('$baseUrl/api/v1/learner/progress');
    final response = await _httpClient.get(url, headers: _headers()).timeout(timeout);
    return _handleResponse(response);
  }

  /// Error Mapper
  Map<String, dynamic> _handleResponse(http.Response res) {
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    
    final errorDetail = _tryDecodeDetail(res.body);
    switch (res.statusCode) {
      case 400:
        throw ApiException(400, 'Bad Request: $errorDetail');
      case 403:
        throw ApiException(403, 'Session Ownership Error: $errorDetail');
      case 404:
        throw ApiException(404, 'Entity Not Found: $errorDetail');
      case 422:
        throw ApiException(422, 'Validation Error: $errorDetail');
      case 503:
        throw ApiException(503, 'Service Feature Disabled: $errorDetail');
      default:
        throw ApiException(res.statusCode, 'Server Error: ${res.statusCode}');
    }
  }

  String _tryDecodeDetail(String body) {
    try {
      final data = jsonDecode(body);
      return data['detail']?.toString() ?? body;
    } catch (_) {
      return body;
    }
  }
}

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);
  @override
  String toString() => 'ApiException($statusCode): $message';
}
```

---

## 2. React Native / TypeScript Example

A typed client using `fetch` with `AbortController` timeouts and strongly typed response envelopes.

```typescript
// src/api/medicalplabClient.ts

export interface ClientConfig {
  baseUrl: string;
  learnerId: string;
  timeoutMs?: number;
}

export interface QuestionDTO {
  question_id: string;
  subject: string;
  topic: string;
  stem: string;
  options: Record<string, string>;
  has_transfer_question?: boolean;
}

export interface AnswerResponseDTO {
  is_correct: boolean;
  explanation: string;
  distractor_signal?: string;
  recommended_action?: 'PROCEED' | 'REMEDIATE' | 'REVIEW';
}

export interface TutorResponseDTO {
  response_id: string;
  session_id: string;
  mode: string;
  message: string;
  socratic_question?: string;
  hints?: string[];
  citations: Array<{
    ref: string;
    document_id: string;
    pmcid?: string;
    title: string;
    quote: string;
    license: string;
    chunk_id: string;
  }>;
  support_status: 'SUPPORTED' | 'SAFE_FALLBACK' | 'PARTIALLY_SUPPORTED' | 'UNSUPPORTED' | 'ABSTAIN';
  fallback_applied: boolean;
  abstain: boolean;
  pedagogical_state: string;
}

export class MedicalPlabError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(`MedicalPlab API [${status}]: ${detail}`);
    this.name = 'MedicalPlabError';
  }
}

export class MedicalPlabClient {
  private baseUrl: string;
  private learnerId: string;
  private timeoutMs: number;

  constructor(config: ClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, '');
    this.learnerId = config.learnerId;
    this.timeoutMs = config.timeoutMs ?? 15000;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-User-Id': this.learnerId,
      ...(options.headers as Record<string, string> || {}),
    };

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...options,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        let detail = response.statusText;
        try {
          const errData = await response.json();
          detail = errData.detail || JSON.stringify(errData);
        } catch (_) {}
        throw new MedicalPlabError(response.status, detail);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (err.name === 'AbortError') {
        throw new MedicalPlabError(408, `Request timed out after ${this.timeoutMs}ms`);
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }

  // 1. Health Check
  async health(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }

  // 2. Fetch Preclinical Question
  async getQuestion(subject: string, topic: string): Promise<QuestionDTO> {
    const query = new URLSearchParams({ subject, topic }).toString();
    return this.request<QuestionDTO>(`/api/v1/university/question?${query}`);
  }

  // 3. Submit Answer
  async submitAnswer(questionId: string, option: string, idempotencyKey: string): Promise<AnswerResponseDTO> {
    return this.request<AnswerResponseDTO>('/api/v1/university/answer', {
      method: 'POST',
      body: JSON.stringify({
        question_id: questionId,
        selected_option: option,
        idempotency_key: idempotencyKey,
      }),
    });
  }

  // 4. Start Socratic Remediation
  async startRemediation(questionId: string, triggerDistractor: string) {
    return this.request('/api/v1/remediation/start', {
      method: 'POST',
      body: JSON.stringify({
        learner_id: this.learnerId,
        question_id: questionId,
        trigger_distractor: triggerDistractor,
      }),
    });
  }

  // 5. Submit Held-Out Transfer Answer
  async submitTransferAnswer(sessionId: string, selectedOption: string) {
    return this.request(`/api/v1/remediation/session/${sessionId}/transfer`, {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        learner_id: this.learnerId,
        selected_option: selectedOption,
      }),
    });
  }

  // 6. Evidence-Grounded Tutor Query
  async askTutor(
    query: string,
    options?: { topic?: string; sessionId?: string; learnerId?: string }
  ): Promise<TutorResponseDTO> {
    return this.request<TutorResponseDTO>('/api/v1/tutor/chat', {
      method: 'POST',
      body: JSON.stringify({
        query,
        ...(options?.topic ? { topic: options.topic } : {}),
        ...(options?.sessionId ? { session_id: options.sessionId } : {}),
        ...(options?.learnerId ? { learner_id: options.learnerId } : {}),
      }),
    });
  }

  // 7. 3D Anatomy Challenge Submit
  async submitAnatomyChallenge(sessionId: string, structureId: string) {
    return this.request(`/api/v1/anatomy/session/${sessionId}/challenge`, {
      method: 'POST',
      body: JSON.stringify({
        learner_id: this.learnerId,
        selected_structure_id: structureId,
      }),
    });
  }

  // 8. Unified Learner Progress
  async getProgress() {
    return this.request('/api/v1/learner/progress');
  }
}
```

---

## 3. Key Best Practices for Mobile Clients

1. **Idempotency:** Always supply unique `idempotency_key` (UUID v4) on question answer submissions to prevent double-scoring on network retries.
2. **Never Cache Stale Sessions:** Remediation and 3D Anatomy sessions are stateful. When switching questions or logging out, clear active session IDs from device memory.
3. **Handle `SAFE_FALLBACK` Gracefully:** When the AI Tutor returns `fallback_applied: true`, indicate to the student that procedural Socratic guidance is active and unverified claims were safely blocked.
4. **Offline Mode:** MedicalPlab requires active connectivity for deterministic scoring, evidence retrieval, and claim verification (`OFFLINE_SYNC_SUPPORTED = NO`).
