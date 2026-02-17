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

"""HAGeo Heuristics Implementation."""

import itertools
import numericals as ng
import hageo_math as hm
from parse import AGPoint


def get_hageo_candidates(points, defined_lines, defined_circles):
    """
    Generates auxiliary points based on HAGeo heuristics (H3, H4, H5).

    Args:
        points: List of AGPoint objects (existing points).
        defined_lines: List of FormalLine objects from DDAR (existing lines).
        defined_circles: List of FormalCircle objects from DDAR (existing circles).

    Returns:
        A list of new AGPoint candidates that satisfy the non-trivial incidence condition.
    """
    candidates = []
    existing_pos = [p.value for p in points]

    def is_new(p_val):
        for ep in existing_pos:
            if ng.distance(p_val, ep) < 1e-4:
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

    # H3: Midpoints
    for p1, p2 in itertools.combinations(points, 2):
        mid = ng.midpoint(p1.value, p2.value)
        parents = {p1.name, p2.name}

        if is_new(mid) and check_nontrivial_incidence(mid, parents):
            name = f"H_mid_{p1.name}_{p2.name}"
            candidates.append(AGPoint(name, mid))

    # H4: Reflections
    for p1 in points:
        for p2 in points:
            if p1.name == p2.name:
                continue
            ref = hm.reflect_point_wrt_point(p1.value, p2.value)
            parents = {p1.name, p2.name}

            if is_new(ref) and check_nontrivial_incidence(ref, parents):
                name = f"H_ref_{p1.name}_{p2.name}"
                candidates.append(AGPoint(name, ref))

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
                candidates.append(AGPoint(name, foot))

    return candidates
