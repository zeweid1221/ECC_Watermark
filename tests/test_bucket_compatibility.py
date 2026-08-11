import math
import unittest

from scripts.analyze_bucket_compatibility import safe_spearman
from watermark_project.config import GenerationProtocolConfig
from watermark_project.bucket_compatibility import (
    reconstruct_admissible_steps,
    resolve_adaptive_allowed_bits,
    soft_intervention_kl_nats,
)


class BucketCompatibilityTests(unittest.TestCase):
    def test_safe_spearman_uses_average_ranks_and_ignores_nonfinite_pairs(self):
        value = safe_spearman(
            [1.0, 2.0, 2.0, 4.0, math.nan],
            [4.0, 1.0, 1.0, 0.0, 99.0],
        )
        self.assertAlmostEqual(value, -1.0)

    def test_reconstructs_adaptive_payload_and_boundary_states(self):
        codewords = [[0, 0], [0, 1], [1, 1]]
        steps = reconstruct_admissible_steps(
            [0, 1, 2, 1, 1, 2],
            feasible_codewords=codewords,
            block_len=2,
        )
        self.assertEqual(steps[0]["allowed_buckets"], [0, 1])
        self.assertEqual(steps[1]["allowed_buckets"], [0, 1])
        self.assertEqual(steps[2]["step_type"], "boundary")
        self.assertEqual(steps[3]["allowed_buckets"], [0, 1])
        self.assertEqual(steps[4]["allowed_buckets"], [1])
        self.assertTrue(all(step["adheres_to_allowed_set"] for step in steps))

    def test_soft_kl_reduces_to_hard_projection_when_only_allowed_mass_remains(self):
        allowed_mass = 0.25
        value = soft_intervention_kl_nats(
            log_allowed_mass=math.log(allowed_mass),
            log_disallowed_payload_mass=-math.inf,
            logit_bias=5.0,
        )
        self.assertAlmostEqual(value, -math.log(allowed_mass))

    def test_invalid_prefix_recovers_to_nearest_feasible_continuation(self):
        codewords = [[0, 0, 0], [0, 1, 1]]
        allowed, status, distance = resolve_adaptive_allowed_bits(
            [1, 0],
            feasible_codewords=codewords,
            invalid_prefix_policy="nearest_feasible",
        )
        self.assertEqual(allowed, {0})
        self.assertEqual(status, "nearest_feasible")
        self.assertEqual(distance, 1)

        steps = reconstruct_admissible_steps(
            [1, 0, 0, 2],
            feasible_codewords=codewords,
            block_len=3,
            invalid_prefix_policy="nearest_feasible",
        )
        self.assertEqual(steps[2]["step_type"], "payload_recovery_forced")
        self.assertEqual(steps[2]["allowed_buckets"], [0])
        self.assertTrue(steps[2]["used_recovery"])
        self.assertFalse(steps[2]["used_fallback"])

    def test_legacy_invalid_prefix_is_not_counted_as_adherence(self):
        steps = reconstruct_admissible_steps(
            [1, 0, 0, 2],
            feasible_codewords=[[0, 0, 0], [0, 1, 1]],
            block_len=3,
        )
        self.assertEqual(
            GenerationProtocolConfig().adaptive_invalid_prefix_policy,
            "legacy_unconstrained",
        )
        self.assertEqual(steps[2]["step_type"], "payload_invalid_prefix")
        self.assertIsNone(steps[2]["adheres_to_allowed_set"])
        self.assertTrue(steps[2]["used_fallback"])

    def test_soft_kl_is_zero_without_bias_over_full_payload_mass(self):
        value = soft_intervention_kl_nats(
            log_allowed_mass=math.log(0.4),
            log_disallowed_payload_mass=math.log(0.6),
            logit_bias=0.0,
        )
        self.assertAlmostEqual(value, 0.0)


if __name__ == "__main__":
    unittest.main()
