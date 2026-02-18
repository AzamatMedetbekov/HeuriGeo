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


def get_heuristic_candidates(points, defined_lines, defined_circles):
    """
    Generates auxiliary points based on rule-based heuristics (H2, H3, H4, H5).

    Args:
        points: List of AGPoint objects (existing points).
        defined_lines: List of FormalLine objects from DDAR (existing lines).
        defined_circles: List of FormalCircle objects from DDAR (existing circles).

    Returns:
        A list of tuples (AGPoint, list[AGPredicate]) for new candidates.
    """
    candidates = []  # List of (AGPoint, [AGPredicate])
    existing_pos = [p.value for p in points]

    def is_new(p_val):
        for ep in existing_pos:
            if ng.distance(p_val, ep) < 1e-4:
                return False
        for c, _ in candidates:
            if ng.distance(p_val, c.value) < 1e-4:
                return False
        return True

    def check_nontrivial_incidence(p_val, construction_parents):
        for line in defined_lines:
            line_pt_names = {pt.name for pt in line.points}
            if not construction_parents.intersection(line_pt_names):
                if line.value.distance(p_val) < 1e-4:
                    return True

        for circle in defined_circles:
            circle_pt_names = {pt.name for pt in circle.points}
            if not construction_parents.intersection(circle_pt_names):
                if circle.value.distance(p_val) < 1e-4:
                    return True
        return False

    # H1: Intersection of multiple lines
    for line1, line2 in itertools.combinations(defined_lines, 2):
        inter = ng.intersect_ll(line1.value, line2.value)
        if inter is None:
            continue

        parents = {pt.name for pt in line1.points} | {pt.name for pt in line2.points}

        supporting_lines = [
            l
            for l in defined_lines
            if l != line1 and l != line2 and l.value.distance(inter) < 1e-4
        ]
        if len(supporting_lines) == 0:
            continue

        if is_new(inter) and check_nontrivial_incidence(inter, parents):
            name = f"H_inter_LL_{len(candidates)}"
            pt = AGPoint(name, inter)

            # Predicates: collinearity with defining lines
            preds = []
            # Take 2 points from line1 to define it
            l1_pts = line1.points[:2]
            preds.append(AGPredicate("coll", [pt, l1_pts[0], l1_pts[1]], []))

            l2_pts = line2.points[:2]
            preds.append(AGPredicate("coll", [pt, l2_pts[0], l2_pts[1]], []))

            candidates.append((pt, preds))

    # H3: Midpoints
    for p1, p2 in itertools.combinations(points, 2):
        mid = ng.midpoint(p1.value, p2.value)
        parents = {p1.name, p2.name}

        if is_new(mid) and check_nontrivial_incidence(mid, parents):
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
            parents = {p1.name, p2.name}

            if is_new(ref) and check_nontrivial_incidence(ref, parents):
                name = f"H_ref_{p1.name}_{p2.name}"
                pt = AGPoint(name, ref)
                # Ref of p1 wrt p2 => p2 is midpoint of p1, ref
                preds = [
                    AGPredicate("coll", [p1, p2, pt], []),
                    AGPredicate("cong", [p1, p2, p2, pt], []),
                ]
                candidates.append((pt, preds))

    # H5: Feet of Perpendiculars
    for p in points:
        for line in defined_lines:
            foot = hm.foot_of_perpendicular(p.value, line.value)
            line_parent_names = {x.name for x in line.points}
            parents = line_parent_names.union({p.name})

            if is_new(foot) and check_nontrivial_incidence(foot, parents):
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
            intersections = hm.intersect_line_circle(line.value, circle.value)
            line_parents = {pt.name for pt in line.points}
            circle_parents = {pt.name for pt in circle.points}
            parents = line_parents.union(circle_parents)

            for inter in intersections:
                if is_new(inter) and check_nontrivial_incidence(inter, parents):
                    name = f"H_inter_LC_{len(candidates)}"
                    pt = AGPoint(name, inter)

                    l_pts = line.points[:2]
                    # Circle definition is trickier, depends on how it was constructed.
                    # FormalCircle has .defining_points and .centers
                    # We need to express "pt is on circle".
                    # Simplest: distance to center equals radius.
                    # But radius might not be explicit.
                    # Use defining points: cong(center, pt, center, defining_point_0)
                    preds = [AGPredicate("coll", [pt, l_pts[0], l_pts[1]], [])]

                    if circle.centers and circle.defining_points:
                        center = circle.centers[0]
                        p_on_circ = circle.defining_points[0]
                        preds.append(
                            AGPredicate("cong", [center, pt, center, p_on_circ], [])
                        )

                    candidates.append((pt, preds))

    return candidates
