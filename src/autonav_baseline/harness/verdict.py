"""
Experiment verdicts, generated from summary.json by explicit rules. Nothing here is hand-written per run.

Each verdict has: id, question, status (pass | warn | fail | info), statement, rule (the exact rule that
produced it) and evidence (the metric values it used). Negative results are stated plainly. A software
benchmark on one machine is never a hard real-time guarantee and never a statement about other hardware.
"""

from typing import Any, Dict, List

RULES_VERSION = 1


def _v(vid, question, status, statement, rule, evidence):
    return {"id": vid, "question": question, "status": status, "statement": statement,
            "rule": rule, "evidence": evidence}


def deadline_verdict(summary: Dict[str, Any]) -> Dict[str, Any]:
    dl = summary["deadline"]
    ms = dl["deadline_ms"]
    tot = summary["latency_ms"]["total_ms"]
    viol = dl["pipeline_total_ms"]["violation_percent"]
    n = dl["pipeline_total_ms"]["of"]
    ev = {"deadline_ms": ms, "p50_ms": tot["p50"], "p95_ms": tot["p95"], "p99_ms": tot["p99"], "max_ms": tot["max"],
          "violation_percent": viol, "frames_measured": n}
    rule = ("pass: 0 violations; warn: 0 < violations <= 5 %; fail: violations > 5 %. "
            "Violation = per-frame pipeline latency (preprocess + register) strictly greater than the deadline.")
    if viol == 0:
        return _v("deadline", f"Did the pipeline meet the {ms:.0f} ms deadline?", "pass",
                  f"All {n} measured frames finished within {ms:.0f} ms (P99 {tot['p99']:.1f} ms, max {tot['max']:.1f} ms). "
                  "This is a measurement on this machine under this profile, not a hard real-time guarantee.", rule, ev)
    if viol <= 5:
        return _v("deadline", f"Did the pipeline meet the {ms:.0f} ms deadline?", "warn",
                  f"{viol:.1f} % of frames missed {ms:.0f} ms (P95 {tot['p95']:.1f} ms, P99 {tot['p99']:.1f} ms). "
                  "A P95 under the deadline does not mean the deadline is met.", rule, ev)
    return _v("deadline", f"Did the pipeline meet the {ms:.0f} ms deadline?", "fail",
              f"No. {viol:.1f} % of {n} frames missed {ms:.0f} ms. Median latency {tot['p50']:.0f} ms is "
              f"{tot['p50'] / ms:.1f}x the deadline; P99 is {tot['p99']:.0f} ms.", rule, ev)


def registration_verdict(summary: Dict[str, Any]) -> Dict[str, Any]:
    reg = summary["registration"]
    pct = reg["accepted_percent"]
    ev = {"attempts": reg["attempts"], "accepted": reg["accepted"], "rejected": reg["rejected"],
          "rejected_by_reason": reg["rejected_by_reason"], "icp_iterations_median": reg["icp_iterations"].get("p50"),
          "inlier_ratio_median": reg["inlier_ratio"].get("p50"), "residual_median_m": reg["residual_m"].get("p50")}
    rule = "pass: >= 99 % accepted; warn: >= 90 %; fail: < 90 %. Accepted = passes the registration validity gate."
    status = "pass" if pct >= 99 else "warn" if pct >= 90 else "fail"
    txt = (f"{reg['accepted']} of {reg['attempts']} registrations passed the validity gate ({pct:.1f} %)"
           + (f"; rejections: {reg['rejected_by_reason']}." if reg["rejected"] else "."))
    return _v("registration", "Did registration produce valid matches?", status, txt, rule, ev)


def accuracy_verdict(summary: Dict[str, Any]) -> Dict[str, Any]:
    acc = summary.get("accuracy", {})
    if acc.get("status") != "MEASURED":
        return _v("accuracy", "How accurate was the estimated trajectory?", "info",
                  "Not assessed: " + str(acc.get("reason", "no ground truth")), "needs ground truth", {})
    ate = acc["ate_m"]
    path = acc["gt_path_length_m"]
    ev = {"ate_rmse_m": ate["rmse"], "ate_max_m": ate["max"], "gt_path_length_m": path,
          "ate_rmse_percent_of_path": ate["rmse"] / path * 100 if path else None,
          "final_error_m": acc["final_position_error_after_alignment_m"], "rpe_mode": acc.get("rpe_mode"),
          "rpe": {k: v.get("translation_percent_of_length") for k, v in acc["rpe"].items() if isinstance(v, dict)}}
    return _v("accuracy", "How accurate was the estimated trajectory?", "info",
              f"ATE RMSE {ate['rmse']:.2f} m (max {ate['max']:.2f} m) over {path:.1f} m of ground-truth path "
              f"after rigid alignment; position RPE is reported per window in the summary. "
              "Scan-to-scan odometry has no loop closure, so error accumulates with distance.",
              "descriptive; no pass/fail threshold is applied to accuracy", ev)


def single_frame_verdict(summary: Dict[str, Any]) -> Dict[str, Any]:
    ms = summary["deadline"]["deadline_ms"]
    tot = summary["latency_ms"]["total_ms"]
    vox = summary["latency_ms"].get("voxel_ms", {})
    ev = {"deadline_ms": ms, "preprocess_p50_ms": tot["p50"], "preprocess_p95_ms": tot["p95"],
          "voxel_p50_ms": vox.get("p50"), "frames": tot["n"]}
    over = tot["p50"] > ms
    return _v("preprocessing", "What does preprocessing alone cost per frame?", "fail" if over else "info",
              f"Preprocessing (invalid-point removal, range filter, voxel downsample) takes a median {tot['p50']:.0f} ms "
              f"(P95 {tot['p95']:.0f} ms); the voxel stage alone is {vox.get('p50', float('nan')):.0f} ms. "
              + ("That already exceeds the deadline before any registration." if over else "")
              + " Non-consecutive frames: no odometry or accuracy claim.",
              "fail if the median preprocessing latency exceeds the deadline", ev)


def generate_verdicts(summary: Dict[str, Any], run: Dict[str, Any]) -> Dict[str, Any]:
    out: List[Dict[str, Any]] = []
    if summary.get("status") == "completed":
        if summary["mode"] == "single-frame":
            out.append(single_frame_verdict(summary))
        else:
            out += [deadline_verdict(summary), registration_verdict(summary), accuracy_verdict(summary)]
            if not run["dataset"]["same_sensor_as_target"]:
                out.append(_v("sensor", "Does this result describe the OS1-64?", "warn",
                              "No. This dataset uses a different sensor (" + run["dataset"]["sensor"] + "); do not read it as an OS1-64 result.",
                              "dataset.same_sensor_as_target is false", {}))
    return {"rules_version": RULES_VERSION, "run_id": run["run_id"], "hardware_label": run["hardware_label"],
            "profile_claim": run["profile"]["claim"], "evidence": summary.get("evidence"), "verdicts": out}


def compare_profiles(runs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """runs: profile_id -> summary. Deadline scaling verdict with the one-way inference rule."""
    p50 = {k: s["latency_ms"]["total_ms"]["p50"] for k, s in runs.items()}
    viol = {k: s["deadline"]["pipeline_total_ms"]["violation_percent"] for k, s in runs.items()}
    full, one = p50.get("laptop-full"), p50.get("laptop-1c")
    note = []
    if full and one:
        note.append(f"Median latency changes by {one / full:.2f}x from laptop-full to laptop-1c "
                    + ("(the pipeline is effectively single-threaded)." if 0.9 <= one / full <= 1.1 else "."))
    four = viol.get("laptop-4c")
    if four is not None and four > 0:
        note.append("It misses the deadline on 4 laptop cores, so a Raspberry Pi 5 very likely misses it too (one-way inference).")
    elif four == 0:
        note.append("It meets the deadline on 4 laptop cores; this says nothing about a Raspberry Pi 5.")
    return {"p50_ms": p50, "violation_percent": viol, "statements": note}