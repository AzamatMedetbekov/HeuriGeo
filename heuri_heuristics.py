# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Heuristic Extension Implementation for auxiliary point generation."""

import itertools
import numericals as ng
import heuri_math as hm
from parse import AGPoint, AGPredicate


# Thresholds
# IS_NEW_THRESHOLD: Points closer than this are considered identical (rejected)
IS_NEW_THRESHOLD = 5e-4
# INCIDENCE_THRESHOLD_GEN: Points closer than this to a line/circle are considered on it (generation)
INCIDENCE_THRESHOLD_GEN = 5e-4
# INCIDENCE_THRESHOLD_VAL: Stricter threshold for validation
INCIDENCE_THRESHOLD_VAL = 1e-4


def inject_predicates(problem, candidate, heuristic_type, ddar_instance=None):
    """
    Inject the correct predicates for a candidate based on its heuristic type.

    Args:
        problem: AGProblem instance
        candidate: Tuple of (AGPoint, [AGPredicate]) or just AGPoint
        heuristic_type: String "H1", "H2", "H3", "H4", or "H5"
        ddar_instance: Optional DDAR instance for extracting geometric context

    Returns:
        List of AGPredicate objects to add for this candidate
    """
    if isinstance(candidate, tuple):
        point, existing_preds = candidate
    else:
        point = candidate
        existing_preds = []

    # Parse point name to extract construction info
    name = point.name
    preds = list(existing_preds)  # Start with existing predicates

    if heuristic_type == "H1":
        # H1: Line-line intersection
        # Format: H_inter_LL_{idx}
        # Existing preds should already have coll(P, A, B) and coll(P, C, D)
        # No additional predicates needed beyond what's already in existing_preds
        pass

    elif heuristic_type == "H2":
        # H2: Line-circle intersection
        # Format: H_inter_LC_{idx}
        # Existing preds should have coll(P, A, B) for the line
        # and cong(center, P, center, p_on_circle) for the circle
        pass

    elif heuristic_type == "H3":
        # H3: Midpoint
        # Format: H_mid_{p1.name}_{p2.name}
        # DDAR doesn't support 'midp', use coll + cong instead
        # This is already handled in the candidate generation, no extra predicates needed
        pass

    elif heuristic_type == "H4":
        # H4: Reflection
        # Format: H_ref_{p1.name}_{p2.name}
        # DDAR doesn't support 'midp', use coll + cong instead
        # This is already handled in the candidate generation, no extra predicates needed
        pass

    elif heuristic_type == "H4":
        # H4: Reflection
        # Format: H_ref_{p1.name}_{p2.name}
        # p2 is the center, p1 is the original point
        # p2 is midpoint of p1 and reflected point
        try:
            parts = name.split("_")
            if len(parts) >= 3:
                p1_name = parts[1]
                p2_name = parts[2]

                p1 = None
                p2 = None
                for p in problem.points:
                    if p.name == p1_name:
                        p1 = p
                    elif p.name == p2_name:
                        p2 = p

                if p1 and p2:
                    # p2 is midpoint of p1 and the reflected point
                    preds.append(AGPredicate("midp", [p2, p1, point], []))
                    # cong(P, center, center, original) - distance from center to P equals distance from center to original
                    preds.append(AGPredicate("cong", [p2, point, p2, p1], []))
        except Exception:
            pass

    elif heuristic_type == "H5":
        # H5: Foot of perpendicular
        # Format: H_foot_{p.name}_on_{line_pts}
        # Already has coll and perp predicates in existing_preds
        pass

    return preds


def get_weighted_candidate(
    candidates, tried_candidates, weight_untried=3, weight_tried=1
):
    """
    Select a candidate using weighted random selection.
    Prefers candidates that haven't been tried before.

    Args:
        candidates: List of (AGPoint, [AGPredicate]) tuples
        tried_candidates: Set of candidate names that have been tried
        weight_untried: Weight for untried candidates (default 3)
        weight_tried: Weight for tried candidates (default 1)

    Returns:
        Selected candidate tuple or None if candidates is empty
    """
    if not candidates:
        return None

    import random

    # Calculate weights for each candidate
    weights = []
    for cand, _ in candidates:
        if cand.name in tried_candidates:
            weights.append(weight_tried)
        else:
            weights.append(weight_untried)

    # Weighted random selection
    total_weight = sum(weights)
    if total_weight == 0:
        return random.choice(candidates)

    r = random.uniform(0, total_weight)
    cumulative = 0
    for i, (cand, preds) in enumerate(candidates):
        cumulative += weights[i]
        if r <= cumulative:
            return (cand, preds)

    # Fallback to last candidate
    return candidates[-1]


def get_heuristic_candidates(
    points, defined_lines, defined_circles, verbose=False, diagnose_mode=False
):
    """
    Generates auxiliary points based on rule-based heuristics (H2, H3, H4, H5).

    Args:
        points: List of AGPoint objects (existing points).
        defined_lines: List of FormalLine objects from DDAR (existing lines).
        defined_circles: List of FormalCircle objects from DDAR (existing circles).
        verbose: If True, prints candidate generation statistics.

    Returns:
        A list of tuples (AGPoint, list[AGPredicate]) for new candidates.
    """
    candidates = []  # List of (AGPoint, [AGPredicate])
    existing_pos = [p.value for p in points]

    stats = {
        "H1": {"total": 0, "new": 0, "nontrivial": 0},
        "H2": {"total": 0, "new": 0, "nontrivial": 0},
        "H3": {"total": 0, "new": 0, "nontrivial": 0},
        "H4": {"total": 0, "new": 0, "nontrivial": 0},
        "H5": {"total": 0, "new": 0, "nontrivial": 0},
    }

    # H2 audit info for diagnose mode
    h2_audit = {
        "pairs_checked": 0,
        "pairs_with_intersections": 0,
        "points_generated": 0,
        "passed_is_new": 0,
        "passed_nontrivial": 0,
        "lines_count": len(defined_lines),
        "circles_count": len(defined_circles),
    }

    def is_new(p_val):
        for ep in existing_pos:
            if ng.distance(p_val, ep) < IS_NEW_THRESHOLD:
                return False
        for c, _ in candidates:
            if ng.distance(p_val, c.value) < IS_NEW_THRESHOLD:
                return False
        return True

    def check_nontrivial_incidence(p_val, construction_parents):
        for line in defined_lines:
            line_pt_names = {pt.name for pt in line.points}
            if not construction_parents.intersection(line_pt_names):
                if line.value.distance(p_val) < INCIDENCE_THRESHOLD_GEN:
                    return True

        for circle in defined_circles:
            circle_pt_names = {pt.name for pt in circle.points}
            if not construction_parents.intersection(circle_pt_names):
                if circle.value.distance(p_val) < INCIDENCE_THRESHOLD_GEN:
                    return True
        return False

    # H1: Intersection of multiple lines
    for line1, line2 in itertools.combinations(defined_lines, 2):
        inter = ng.intersect_ll(line1.value, line2.value)
        if inter is None:
            continue

        stats["H1"]["total"] += 1

        if not is_new(inter):
            continue
        stats["H1"]["new"] += 1

        parents = {pt.name for pt in line1.points} | {pt.name for pt in line2.points}

        supporting_lines = [
            l
            for l in defined_lines
            if l != line1
            and l != line2
            and l.value.distance(inter) < INCIDENCE_THRESHOLD_GEN
        ]

        # H1 logic requires at least 3 concurrent lines to be interesting?
        # The prompt implies standard H1 logic. The original code checked supporting_lines.
        # If len(supporting_lines) == 0, it means it's just an intersection of 2 lines.
        # Usually that defines a point, but maybe it's not "heuristic" enough unless confirmed by a 3rd line?
        # Actually, let's keep the logic as is, just using new threshold.
        if len(supporting_lines) == 0:
            continue

        if check_nontrivial_incidence(inter, parents):
            stats["H1"]["nontrivial"] += 1
            name = f"H_inter_LL_{len(candidates)}"
            pt = AGPoint(name, inter)

            preds = []
            l1_pts = line1.points[:2]
            preds.append(AGPredicate("coll", [pt, l1_pts[0], l1_pts[1]], []))

            l2_pts = line2.points[:2]
            preds.append(AGPredicate("coll", [pt, l2_pts[0], l2_pts[1]], []))

            candidates.append((pt, preds))

    # H3: Midpoints
    for p1, p2 in itertools.combinations(points, 2):
        mid = ng.midpoint(p1.value, p2.value)
        stats["H3"]["total"] += 1

        if not is_new(mid):
            continue
        stats["H3"]["new"] += 1

        parents = {p1.name, p2.name}

        if check_nontrivial_incidence(mid, parents):
            stats["H3"]["nontrivial"] += 1
            name = f"H_mid_{p1.name}_{p2.name}"
            pt = AGPoint(name, mid)
            preds = [
                AGPredicate("coll", [pt, p1, p2], []),
                AGPredicate("cong", [pt, p1, pt, p2], []),
            ]
            candidates.append((pt, preds))

    # H4: Reflections
    for p1 in points:
        for p2 in points:
            if p1.name == p2.name:
                continue
            ref = hm.reflect_point_wrt_point(p1.value, p2.value)
            stats["H4"]["total"] += 1

            if not is_new(ref):
                continue
            stats["H4"]["new"] += 1

            parents = {p1.name, p2.name}

            if check_nontrivial_incidence(ref, parents):
                stats["H4"]["nontrivial"] += 1
            name = f"H_ref_{p1.name}_{p2.name}"
            pt = AGPoint(name, ref)
            preds = [
                AGPredicate("coll", [p1, p2, pt], []),
                AGPredicate("cong", [p2, p1, p2, pt], []),
            ]
            candidates.append((pt, preds))

    # H5: Feet of Perpendiculars
    for p in points:
        for line in defined_lines:
            foot = hm.foot_of_perpendicular(p.value, line.value)
            stats["H5"]["total"] += 1

            if not is_new(foot):
                continue
            stats["H5"]["new"] += 1

            line_parent_names = {x.name for x in line.points}
            parents = line_parent_names.union({p.name})

            if check_nontrivial_incidence(foot, parents):
                stats["H5"]["nontrivial"] += 1
            sorted_line_parents = sorted(list(line_parent_names))
            line_str = "_".join(sorted_line_parents[:2])
            name = f"H_foot_{p.name}_on_{line_str}"
            pt = AGPoint(name, foot)

            l_pts = line.points[:2]
            preds = [
                AGPredicate("coll", [pt, l_pts[0], l_pts[1]], []),
                AGPredicate("perp", [p, pt, l_pts[0], l_pts[1]], []),
            ]
            candidates.append((pt, preds))

    # H2: Intersections of Lines and Circles
    for line in defined_lines:
        for circle in defined_circles:
            if diagnose_mode:
                h2_audit["pairs_checked"] += 1

            intersections = hm.intersect_line_circle(line.value, circle.value)

            if diagnose_mode and len(intersections) > 0:
                h2_audit["pairs_with_intersections"] += 1

            line_parents = {pt.name for pt in line.points}
            circle_parents = {pt.name for pt in circle.points}
            parents = line_parents.union(circle_parents)

            for inter in intersections:
                if diagnose_mode:
                    h2_audit["points_generated"] += 1

                stats["H2"]["total"] += 1

                if not is_new(inter):
                    continue

                if diagnose_mode:
                    h2_audit["passed_is_new"] += 1

                stats["H2"]["new"] += 1

                if check_nontrivial_incidence(inter, parents):
                    if diagnose_mode:
                        h2_audit["passed_nontrivial"] += 1

                    stats["H2"]["nontrivial"] += 1
                    name = f"H_inter_LC_{len(candidates)}"
                    pt = AGPoint(name, inter)

                    l_pts = line.points[:2]
                    preds = [AGPredicate("coll", [pt, l_pts[0], l_pts[1]], [])]

                    if circle.centers and circle.defining_points:
                        center = circle.centers[0]
                        p_on_circ = circle.defining_points[0]
                        preds.append(
                            AGPredicate("cong", [center, pt, center, p_on_circ], [])
                        )

                    candidates.append((pt, preds))

    if verbose:
        print("\nCandidate Generation Diagnosis:")
        print(f"  {'Type':<5} | {'Total':<8} | {'New':<8} | {'Valid':<8}")
        print("-" * 35)
        for h, s in stats.items():
            print(f"  {h:<5} | {s['total']:<8} | {s['new']:<8} | {s['nontrivial']:<8}")
        print(f"  Total Candidates: {len(candidates)}")

        if diagnose_mode:
            print("\n  H2 Detailed Audit:")
            print(f"    Line-circle pairs checked: {h2_audit['pairs_checked']}")
            print(
                f"    Pairs with intersections: {h2_audit['pairs_with_intersections']}"
            )
            print(f"    Points generated: {h2_audit['points_generated']}")
            print(f"    Passed is_new filter: {h2_audit['passed_is_new']}")
            print(f"    Passed nontrivial filter: {h2_audit['passed_nontrivial']}")
            print(f"    Available lines: {h2_audit['lines_count']}")
            print(f"    Available circles: {h2_audit['circles_count']}")

    if diagnose_mode:
        return candidates, h2_audit
    return candidates
