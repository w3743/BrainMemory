from __future__ import annotations

import tempfile
from pathlib import Path

from test_engine import (
    test_add_search_and_reinforce,
    test_duplicate_add_reinforces_existing_memory,
    test_duplicate_add_keeps_higher_sensitivity,
    test_embedding_backend_rejects_remote_model_id,
    test_embedding_config_defaults_to_local_bge,
    test_identity_question_recalls_name_memory,
    test_irrelevant_query_returns_no_answer_injection_results,
    test_nearby_but_conflicting_add_does_not_merge,
    test_reinforce_used_records_experience_activation,
    test_reindex_embeddings_rebuilds_vectors_and_bumps_version,
    test_search_does_not_reinforce_memory_until_used,
    test_sleep_archives_low_value_cold_memory,
    test_store_index_version_changes_on_memory_updates,
    test_supersede_hides_old_memory,
)
from test_strength import test_strength_decays_and_reinforces, test_unified_decay, test_adaptive_decay_weaker_faster, test_reinforce_gradual_approach, test_archive_threshold, test_constants
from test_adapters import (
    test_adapter_observe_extracts_memory_without_explicit_list,
    test_adapter_duplicate_add_reinforces_instead_of_growing_store,
    test_adapter_passes_retrieved_memories_to_extractor_for_arbitration,
    test_conflicting_llm_writes_keep_delete_over_update,
    test_conflicting_llm_writes_keep_supersede_over_update,
    test_correction_only_supersedes_relevant_used_memory,
    test_delete_request_does_not_update_memory_before_delete,
    test_english_project_preference_is_shared_but_user_preference_is_private,
    test_hermes_provider_facade,
    test_negative_memory_injection_uses_positive_actionable_text,
    test_no_workspace_environment_fact_is_global,
    test_no_workspace_personal_memory_is_user_scoped,
    test_no_workspace_project_like_memory_is_not_global,
    test_piagent_hook_accepts_legacy_csm_memory_ids,
    test_piagent_hook_accepts_workspace_id_scope,
    test_openclaw_irrelevant_message_does_not_inject_memory,
    test_openclaw_same_workspace_different_users_do_not_share_personal_memory,
    test_openclaw_same_workspace_different_users_share_project_memory,
    test_openclaw_sidecar_payload_flow,
    test_openclaw_post_run_reinforces_used_memory,
    test_project_preference_is_shared_but_personal_preference_is_private,
    test_scoped_retrieval_ignores_legacy_global_personal_memory,
    test_piagent_hook_injects_and_commits_memory,
    test_project_correction_still_supersedes_matching_memory,
)
from test_extractor import (
    test_deepseek_dry_run_and_fake_transport_cache,
    test_deepseek_prompt_is_simplified,
    test_deepseek_probe_requires_explicit_call_path,
    test_deepseek_requires_api_key,
    test_deepseek_skips_oversized_input_without_transport_call,
    test_default_extractor_without_key_is_noop,
    test_json_extractor_parses_valid_llm_output,
    test_json_extractor_rejects_invalid_schema,
    test_security_marks_email_without_redacting,
    test_security_marks_secret_without_rejecting,
)
from test_evaluation import (
    test_end_to_end_fixture_eval,
    test_embedding_quality_eval,
    test_load_end_to_end_cases,
    test_load_extraction_cases,
    test_load_retrieval_cases,
    test_load_strength_cases,
    test_mock_llm_extractor_fixture_eval,
    test_retrieval_fixture_eval,
    test_run_full_evaluation,
    test_strength_model_eval,
)
from test_evolution import (
    test_apply_feedback_used,
    test_apply_feedback_ignored,
    test_apply_feedback_corrected,
    test_bounds,
    test_detect_feedback_used,
    test_detect_feedback_correction,
    test_detect_feedback_ignored,
    test_inherit_from,
    test_evolution_engine_flow,
    test_supersede_inherits_trust,
)
from test_server import (
    test_admin_user_scoped_lookup_without_project_does_not_scan_all_private_memory,
    test_admin_console_and_core_admin_apis,
    test_sidecar_api_key_auth,
    test_sidecar_health_and_openclaw_flow,
    test_sidecar_hermes_provider_endpoints,
)
from test_packaging import (
    test_built_wheel_metadata_requires_sentence_transformers,
    test_docs_do_not_advertise_embedding_fallback,
    test_sentence_transformers_is_runtime_dependency,
)


def main() -> None:
    test_strength_decays_and_reinforces()
    test_adaptive_decay_weaker_faster()
    test_reinforce_gradual_approach()
    test_archive_threshold()
    test_constants()
    test_unified_decay()
    with tempfile.TemporaryDirectory() as tmp:
        test_add_search_and_reinforce(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_duplicate_add_reinforces_existing_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_duplicate_add_keeps_higher_sensitivity(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_nearby_but_conflicting_add_does_not_merge(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_supersede_hides_old_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_sleep_archives_low_value_cold_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_store_index_version_changes_on_memory_updates(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_reindex_embeddings_rebuilds_vectors_and_bumps_version(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_identity_question_recalls_name_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_irrelevant_query_returns_no_answer_injection_results(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_search_does_not_reinforce_memory_until_used(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_reinforce_used_records_experience_activation(Path(tmp))
    test_embedding_config_defaults_to_local_bge()
    test_embedding_backend_rejects_remote_model_id()
    with tempfile.TemporaryDirectory() as tmp:
        test_piagent_hook_injects_and_commits_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_piagent_hook_accepts_workspace_id_scope(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_piagent_hook_accepts_legacy_csm_memory_ids(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_openclaw_sidecar_payload_flow(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_openclaw_post_run_reinforces_used_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_openclaw_irrelevant_message_does_not_inject_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_openclaw_same_workspace_different_users_do_not_share_personal_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_openclaw_same_workspace_different_users_share_project_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_no_workspace_personal_memory_is_user_scoped(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_no_workspace_project_like_memory_is_not_global(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_no_workspace_environment_fact_is_global(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_project_preference_is_shared_but_personal_preference_is_private(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_english_project_preference_is_shared_but_user_preference_is_private(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_scoped_retrieval_ignores_legacy_global_personal_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_negative_memory_injection_uses_positive_actionable_text(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_hermes_provider_facade(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_adapter_observe_extracts_memory_without_explicit_list(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_adapter_duplicate_add_reinforces_instead_of_growing_store(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_adapter_passes_retrieved_memories_to_extractor_for_arbitration(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_conflicting_llm_writes_keep_delete_over_update(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_conflicting_llm_writes_keep_supersede_over_update(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_correction_only_supersedes_relevant_used_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_project_correction_still_supersedes_matching_memory(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_delete_request_does_not_update_memory_before_delete(Path(tmp))
    test_default_extractor_without_key_is_noop()
    test_deepseek_requires_api_key()
    test_json_extractor_parses_valid_llm_output()
    test_json_extractor_rejects_invalid_schema()
    test_security_marks_email_without_redacting()
    test_security_marks_secret_without_rejecting()
    test_deepseek_dry_run_and_fake_transport_cache()
    test_deepseek_prompt_is_simplified()
    test_deepseek_probe_requires_explicit_call_path()
    test_deepseek_skips_oversized_input_without_transport_call()
    test_load_extraction_cases()
    test_load_retrieval_cases()
    test_load_end_to_end_cases()
    test_load_strength_cases()
    with tempfile.TemporaryDirectory() as tmp:
        test_mock_llm_extractor_fixture_eval(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_retrieval_fixture_eval(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_end_to_end_fixture_eval(Path(tmp))
    test_strength_model_eval()
    with tempfile.TemporaryDirectory() as tmp:
        test_embedding_quality_eval(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_run_full_evaluation(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_sidecar_health_and_openclaw_flow(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_sidecar_hermes_provider_endpoints(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_sidecar_api_key_auth(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_admin_console_and_core_admin_apis(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_admin_user_scoped_lookup_without_project_does_not_scan_all_private_memory(Path(tmp))
    test_sentence_transformers_is_runtime_dependency()
    test_built_wheel_metadata_requires_sentence_transformers()
    test_docs_do_not_advertise_embedding_fallback()
    # ── 自适应进化 ──
    test_apply_feedback_used()
    test_apply_feedback_ignored()
    test_apply_feedback_corrected()
    test_bounds()
    test_detect_feedback_used()
    test_detect_feedback_correction()
    test_detect_feedback_ignored()
    test_inherit_from()
    with tempfile.TemporaryDirectory() as tmp:
        test_evolution_engine_flow(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_supersede_inherits_trust(Path(tmp))
    print("79 checks passed")


if __name__ == "__main__":
    main()
