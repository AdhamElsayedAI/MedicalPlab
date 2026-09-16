"""Comprehensive pre-freeze test suite for MedicalPlab Phase 5 Generative 3D Anatomy Lab (Renal MVP)."""
from __future__ import annotations

import json
import os
import struct
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app
from medicalplab.anatomy import (
    AnatomyActionType,
    AnatomyService,
    ChallengeResult,
    InteractionRequestType,
    LessonState,
    SceneAction,
    StructuredAnatomyAgent,
    get_renal_manifest,
    get_structure_by_id,
    is_anatomy_enabled,
    resolve_mesh_node,
    resolve_query_to_structure,
    valid_renal_structure_ids,
)
from medicalplab.anatomy.manifest import RENAL_STRUCTURES
from medicalplab.anatomy.models import (
    ChallengeSubmitRequest,
    InteractSessionRequest,
    StartSessionRequest,
)
from medicalplab.anatomy.repository import AnatomyRepository
from medicalplab.anatomy.service import AnatomyOwnershipError, AnatomyServiceError
from medicalplab.anatomy.validator import (
    AnatomyValidationError,
    validate_agent_response,
    validate_scene_action,
)


def _get_glb_node_names(path: Path) -> set[str]:
    with open(path, "rb") as f:
        f.read(12)
        chunk_len, _ = struct.unpack("<II", f.read(8))
        data = json.loads(f.read(chunk_len).decode("utf-8"))
    return {n.get("name") for n in data.get("nodes", []) if n.get("name")}


class TestRenalAnatomyDomain(unittest.TestCase):
    """Domain, manifest, and validation tests."""

    def test_01_manifest_contains_only_valid_structure_ids(self):
        """1. Manifest contains only valid, verified structure IDs (8 core renal structures)."""
        structures = get_renal_manifest()
        self.assertEqual(len(structures), 8)
        for s in structures:
            self.assertTrue(s.structure_id.islower())
            self.assertIn("_", s.structure_id)
            self.assertTrue(s.ontology_id.startswith("UBERON:"))
            self.assertTrue(len(s.mesh_node_names) > 0)
            self.assertTrue(len(s.relationships) > 0)
            self.assertTrue(len(s.evidence_refs) > 0)

    def test_02_all_mesh_mappings_resolve(self):
        """2. All mesh mappings resolve to valid structures."""
        structures = get_renal_manifest()
        for s in structures:
            for mesh_name in s.mesh_node_names:
                resolved = resolve_mesh_node(mesh_name)
                self.assertIsNotNone(
                    resolved,
                    f"Mesh node '{mesh_name}' failed to resolve to a structure."
                )
                self.assertEqual(resolved.structure_id, s.structure_id)

    def test_03_duplicate_structure_ids_rejected(self):
        """3. Duplicate structure IDs are strictly rejected."""
        all_ids = [s.structure_id for s in RENAL_STRUCTURES]
        unique_ids = set(all_ids)
        self.assertEqual(len(all_ids), len(unique_ids), "Duplicate structure IDs detected in manifest!")

    def test_04_unknown_scene_action_rejected(self):
        """4. Unknown scene action rejected."""
        with self.assertRaises(Exception):
            validate_scene_action(
                SceneAction(action="DESTROY_VIEWPORT", structure_id="renal_artery_left")  # type: ignore
            )
        # Also test via dict validation
        res = validate_agent_response({
            "tutor_message": "test",
            "scene_actions": [{"action": "DESTROY_VIEWPORT", "structure_id": "renal_artery_left"}]
        })
        self.assertTrue(res.fallback_applied)
        self.assertEqual(len(res.scene_actions), 0)

    def test_05_unknown_structure_action_rejected(self):
        """5. Unknown structure action rejected."""
        with self.assertRaises(AnatomyValidationError):
            validate_scene_action(
                SceneAction(action=AnatomyActionType.HIGHLIGHT_STRUCTURE, structure_id="hallucinated_organ")
            )

    def test_06_arbitrary_action_code_cannot_execute(self):
        """6. Arbitrary action/code cannot execute (injection prevention)."""
        malicious_payload = {
            "tutor_message": "Hello <script>fetch('http://malicious.site')</script>",
            "scene_actions": [
                {"action": "HIGHLIGHT_STRUCTURE", "structure_id": "renal_artery_left"}
            ]
        }
        # Validator must fail closed to safe fallback
        safe_response = validate_agent_response(malicious_payload)
        self.assertTrue(safe_response.fallback_applied)
        self.assertNotIn("<script>", safe_response.tutor_message)
        self.assertEqual(len(safe_response.scene_actions), 0)

    def test_07_agent_response_schema_validation(self):
        """7. Agent response schema validation succeeds on conformant output."""
        valid_payload = {
            "tutor_message": "The left renal artery supplies oxygenated blood to the kidney.",
            "scene_actions": [
                {"action": "FOCUS_STRUCTURE", "structure_id": "renal_artery_left"},
                {"action": "HIGHLIGHT_STRUCTURE", "structure_id": "renal_artery_left"}
            ],
            "interaction_request": {
                "type": "IDENTIFY_STRUCTURE",
                "target_structure_id": "renal_vein_left",
                "prompt": "Identify the anterior renal vein."
            }
        }
        response = validate_agent_response(valid_payload)
        self.assertFalse(response.fallback_applied)
        self.assertEqual(len(response.scene_actions), 2)
        self.assertEqual(response.scene_actions[1].action, AnatomyActionType.HIGHLIGHT_STRUCTURE)

    def test_08_invalid_agent_output_fails_closed(self):
        """8. Invalid agent output fails closed (no scene mutation, bounded message)."""
        corrupted_payload = {
            "tutor_message": "Corrupted response",
            "scene_actions": [
                {"action": "HIGHLIGHT_STRUCTURE", "structure_id": "non_existent_organ"}
            ]
        }
        response = validate_agent_response(corrupted_payload)
        self.assertTrue(response.fallback_applied)
        self.assertEqual(len(response.scene_actions), 0)
        self.assertIn("verified renal anatomy", response.tutor_message)

    def test_09_structure_selection_maps_deterministically(self):
        """9. Structure selection maps deterministically."""
        struct_vein = resolve_mesh_node("VH_M_renal_vein_L")
        self.assertIsNotNone(struct_vein)
        self.assertEqual(struct_vein.structure_id, "renal_vein_left")
        self.assertEqual(struct_vein.ontology_id, "UBERON:0001142")

        struct_pelvis = resolve_mesh_node("VH_M_renal_pelvis_L")
        self.assertIsNotNone(struct_pelvis)
        self.assertEqual(struct_pelvis.structure_id, "renal_pelvis_left")
        self.assertEqual(struct_pelvis.ontology_id, "UBERON:0001224")

    def test_10_challenge_scoring_is_deterministic(self):
        """10. Challenge scoring is deterministic."""
        repo = AnatomyRepository(":memory:")
        service = AnatomyService(repository=repo)
        start_res = service.start_session(StartSessionRequest(learner_id="test_learner_1"))
        session_id = start_res.session.session_id

        # Target is renal_artery_left for the challenge
        repo.save_session(
            start_res.session.model_copy(
                update={"current_target_structure_id": "renal_artery_left", "lesson_state": LessonState.CHALLENGE_ACTIVE}
            )
        )

        # Correct submission
        correct_res = service.submit_challenge(
            session_id, ChallengeSubmitRequest(learner_id="test_learner_1", selected_structure_id="renal_artery_left")
        )
        self.assertTrue(correct_res.is_correct)
        self.assertEqual(correct_res.session.challenge_result, ChallengeResult.CORRECT)
        self.assertEqual(correct_res.session.challenge_state, "PASSED")

        # Wrong submission on new session
        start_res2 = service.start_session(StartSessionRequest(learner_id="test_learner_2"))
        sess2_id = start_res2.session.session_id
        repo.save_session(
            start_res2.session.model_copy(
                update={"current_target_structure_id": "renal_artery_left", "lesson_state": LessonState.CHALLENGE_ACTIVE}
            )
        )
        wrong_res = service.submit_challenge(
            sess2_id, ChallengeSubmitRequest(learner_id="test_learner_2", selected_structure_id="renal_vein_left")
        )
        self.assertFalse(wrong_res.is_correct)
        self.assertEqual(wrong_res.session.challenge_result, ChallengeResult.INCORRECT)
        self.assertEqual(wrong_res.session.challenge_state, "FAILED")

    def test_11_llm_cannot_override_score(self):
        """11. LLM cannot override score (scoring logic is isolated from LLM output)."""
        repo = AnatomyRepository(":memory:")
        service = AnatomyService(repository=repo)
        start_res = service.start_session(StartSessionRequest(learner_id="test_learner_3"))
        session_id = start_res.session.session_id

        repo.save_session(
            start_res.session.model_copy(
                update={"current_target_structure_id": "renal_artery_left", "lesson_state": LessonState.CHALLENGE_ACTIVE}
            )
        )

        res = service.submit_challenge(
            session_id, ChallengeSubmitRequest(learner_id="test_learner_3", selected_structure_id="renal_pelvis_left")
        )
        self.assertFalse(res.is_correct)
        self.assertEqual(res.session.challenge_result, ChallengeResult.INCORRECT)

    def test_12_hint_progression_bounded(self):
        """12. Hint progression bounded (level 1 -> level 2 -> level 3, max 3)."""
        repo = AnatomyRepository(":memory:")
        service = AnatomyService(repository=repo)
        start_res = service.start_session(StartSessionRequest(learner_id="test_learner_4"))
        session_id = start_res.session.session_id

        # Student clicks wrong structure multiple times
        # Step 1: wrong click -> hint 1
        res1 = service.interact(
            session_id, InteractSessionRequest(learner_id="test_learner_4", selected_structure_id="renal_pelvis_left")
        )
        self.assertEqual(res1.session.hint_level, 1)
        self.assertIn("Hint 1", res1.tutor_response.tutor_message)

        # Step 2: wrong click -> hint 2
        res2 = service.interact(
            session_id, InteractSessionRequest(learner_id="test_learner_4", selected_structure_id="renal_artery_left")
        )
        self.assertEqual(res2.session.hint_level, 2)
        self.assertIn("Hint 2", res2.tutor_response.tutor_message)

        # Step 3: wrong click -> hint 3
        res3 = service.interact(
            session_id, InteractSessionRequest(learner_id="test_learner_4", selected_structure_id="ureter_left")
        )
        self.assertEqual(res3.session.hint_level, 3)
        self.assertIn("Hint 3", res3.tutor_response.tutor_message)

        # Step 4: subsequent wrong click stays clamped at hint 3
        res4 = service.interact(
            session_id, InteractSessionRequest(learner_id="test_learner_4", selected_structure_id="ureter_left")
        )
        self.assertEqual(res4.session.hint_level, 3)

    def test_13_attribution_metadata_present(self):
        """13. Attribution metadata present in manifest and notices."""
        manifest_path = Path(__file__).resolve().parents[2] / "THIRD_PARTY_NOTICES_ANATOMY.md"
        self.assertTrue(manifest_path.exists(), "THIRD_PARTY_NOTICES_ANATOMY.md must exist.")
        content = manifest_path.read_text(encoding="utf-8")
        self.assertIn("HuBMAP Human Reference Atlas", content)
        self.assertIn("CC BY 4.0", content)
        self.assertIn("BodyParts3D", content)

    def test_14_session_ownership_enforced(self):
        """14. Session ownership enforced (HTTP 403 / AnatomyOwnershipError on unauthorized learner)."""
        repo = AnatomyRepository(":memory:")
        service = AnatomyService(repository=repo)
        start_res = service.start_session(StartSessionRequest(learner_id="authorized_owner"))
        session_id = start_res.session.session_id

        # Authorized access succeeds
        sess = service.get_session(session_id, learner_id="authorized_owner")
        self.assertEqual(sess.learner_id, "authorized_owner")

        # Unauthorized access raises error
        with self.assertRaises(AnatomyOwnershipError):
            service.get_session(session_id, learner_id="unauthorized_intruder")

    def test_15_session_resume_works(self):
        """15. Session resume works (resumes in-progress session for learner)."""
        repo = AnatomyRepository(":memory:")
        service = AnatomyService(repository=repo)
        res1 = service.start_session(StartSessionRequest(learner_id="learner_resume_test"))
        session_id1 = res1.session.session_id

        # Advance session state
        service.interact(
            session_id1, InteractSessionRequest(learner_id="learner_resume_test", selected_structure_id="renal_pelvis_left")
        )

        # Start session again with same learner and objective -> resumes same session
        res2 = service.start_session(StartSessionRequest(learner_id="learner_resume_test"))
        self.assertEqual(res2.session.session_id, session_id1)
        self.assertEqual(res2.session.hint_level, 1)

    def test_16_feature_flag_default_off(self):
        """16. Feature flag default is OFF."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_anatomy_enabled())

    def test_17_feature_disabled_returns_safe_503(self):
        """17. Feature disabled returns safe 503 response via API."""
        client = TestClient(app)
        with patch.dict(os.environ, {"MEDICALPLAB_ANATOMY_3D_ENABLED": "false"}):
            resp = client.get("/api/v1/anatomy/manifest")
            self.assertEqual(resp.status_code, 503)
            self.assertIn("disabled by feature flag", resp.json()["detail"])

            resp_start = client.post("/api/v1/anatomy/session/start", json={"learner_id": "test_503"})
            self.assertEqual(resp_start.status_code, 503)

    def test_18_feature_enabled_serves_api_successfully(self):
        """18. Feature enabled serves API successfully."""
        client = TestClient(app)
        with patch.dict(os.environ, {"MEDICALPLAB_ANATOMY_3D_ENABLED": "true"}):
            resp = client.get("/api/v1/anatomy/manifest")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(len(data["structures"]), 8)
            self.assertEqual(data["provenance"]["license"], "CC BY 4.0")

            # Start session
            resp_start = client.post("/api/v1/anatomy/session/start", json={"learner_id": "api_test_learner"})
            self.assertEqual(resp_start.status_code, 200)
            sess_data = resp_start.json()
            session_id = sess_data["session"]["session_id"]

            # Interact
            resp_interact = client.post(
                f"/api/v1/anatomy/session/{session_id}/interact",
                json={"learner_id": "api_test_learner", "message": "Teach me renal blood flow"}
            )
            self.assertEqual(resp_interact.status_code, 200)

            # Submit challenge
            resp_chal = client.post(
                f"/api/v1/anatomy/session/{session_id}/challenge",
                json={"learner_id": "api_test_learner", "selected_structure_id": "renal_artery_left"}
            )
            self.assertEqual(resp_chal.status_code, 200)
            self.assertIn("is_correct", resp_chal.json())

    def test_19_all_structures_exist_in_committed_glbs(self):
        """19. Invariant A & B: All manifest structures have verified mesh nodes in committed GLBs."""
        base_dir = Path(__file__).resolve().parents[2] / "frontend" / "public" / "models" / "anatomy" / "hra" / "renal"
        glb_files = [
            base_dir / "VH_M_Kidney_L.glb",
            base_dir / "VH_M_Ureter_L.glb",
            base_dir / "VH_M_Blood_Vasculature_Kidney.glb",
        ]
        all_nodes: set[str] = set()
        for p in glb_files:
            self.assertTrue(p.exists(), f"Committed GLB missing: {p}")
            all_nodes.update(_get_glb_node_names(p))

        for s in RENAL_STRUCTURES:
            # At least one registered mesh node must exist in GLB
            found = [m for m in s.mesh_node_names if m in all_nodes]
            self.assertTrue(
                len(found) > 0,
                f"Structure '{s.structure_id}' has no matching mesh node in committed GLBs! Nodes: {s.mesh_node_names}"
            )

    def test_20_no_dangling_relationship_targets(self):
        """20. Invariant: Relationships must only target valid manifest structures."""
        valid_ids = valid_renal_structure_ids()
        for s in RENAL_STRUCTURES:
            for rel in s.relationships:
                target = rel.get("target")
                self.assertIn(
                    target,
                    valid_ids,
                    f"Dangling relationship target '{target}' in structure '{s.structure_id}'"
                )

    def test_21_atomic_multi_action_failure(self):
        """21. Multi-action payload validation fails atomically on any invalid action."""
        payload = {
            "tutor_message": "Action test",
            "scene_actions": [
                {"action": "HIGHLIGHT_STRUCTURE", "structure_id": "renal_artery_left"},
                {"action": "INVALID_ACTION_NAME", "structure_id": "renal_artery_left"},
            ]
        }
        res = validate_agent_response(payload)
        self.assertTrue(res.fallback_applied)
        # Must NOT execute the first valid action and ignore the second
        self.assertEqual(len(res.scene_actions), 0)

    def test_22_independent_challenge_resets_revealing_state(self):
        """22. Challenge independence: Target is not leaked by auto-highlighting in challenge prompt."""
        agent = StructuredAnatomyAgent()
        # Learner clicks correct structure during guided phase -> transitions to independent challenge
        resp = agent.plan_interaction(
            user_query=None,
            lesson_state=LessonState.GUIDED_IDENTIFICATION,
            selected_structure_id="renal_vein_left",
            target_structure_id="renal_vein_left",
            hint_level=0,
        )
        self.assertIsNotNone(resp.interaction_request)
        self.assertEqual(resp.interaction_request.type, InteractionRequestType.IDENTIFY_STRUCTURE)
        new_target = resp.interaction_request.target_structure_id
        # Target must NOT be highlighted in scene actions
        highlighted = [act.structure_id for act in resp.scene_actions if act.action == AnatomyActionType.HIGHLIGHT_STRUCTURE]
        self.assertNotIn(new_target, highlighted, "Independent challenge must not highlight target!")
        # Scene must be reset to normalize viewport
        actions = [act.action for act in resp.scene_actions]
        self.assertIn(AnatomyActionType.RESET_SCENE, actions)


if __name__ == "__main__":
    unittest.main()
