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

"""Bridge module to connect DDAR engine with heuristic candidate generator."""

from ddar import DDAR
from heuri_heuristics import get_heuristic_candidates
from parse import AGProblem


def extract_lines_and_circles(ddar_instance):
    """
    Extract deduced lines and circles from a DDAR instance.

    Args:
        ddar_instance: A DDAR object after deduction_closure() has run

    Returns:
        tuple: (defined_lines, defined_circles) where:
            - defined_lines: list of FormalLine objects from DDAR
            - defined_circles: list of FormalCircle objects from DDAR

    Both FormalLine and FormalCircle objects have:
        - .value: NumLine or NumCircle (geometric representation)
        - .points: list of AGPoint (points that define this object)
    """
    # DDAR stores lines and circles as sets
    # FormalLine has: points, main_pair, direction, value
    # FormalCircle has: defining_points, points, centers, value
    #
    # heuri_heuristics expects:
    # - lines: objects with .value (NumLine) and .points (list of AGPoint)
    # - circles: objects with .value (NumCircle) and .points (list of AGPoint)

    defined_lines = list(ddar_instance.lines)
    defined_circles = list(ddar_instance.circles)

    return defined_lines, defined_circles


if __name__ == "__main__":
    # Test with a problem from test.py
    # Using 2000_p1 (a complete geometry problem)
    test_problem = (
        "a@-0.5224995081800106_0.10855387073174794 = ;"
        " b@-0.18661048092098675_0.19019216505952974 = ;"
        " g1@-0.4843181580129312_-0.04853780631339801 = ;"
        " g2@-0.12022634032706143_-0.08293583930559657 = ;"
        " m@-0.3631425485390431_0.05847659536258823 = ;"
        " n@-0.3853283338800269_-0.17635261459308932 = ;"
        " c@-0.6410940637479596_-0.009079906237506334 = ;"
        " d@0.030683990770088265_0.15419668241805734 = ;"
        " e@-0.4039049526120616_0.22618764770100208 = ;"
        " p@-0.48422076136091424_0.029048367665792673 = ;"
        " q@-0.242064335717172_0.08790482305938377 = perp a b a g1, perp a b b"
        " g2, cong a g1 g1 m, cong b g2 g2 m, cong a g1 g1 n, cong b g2 g2 n,"
        " cong a g1 g1 c, para a b m c, cong b g2 g2 d, para a b m d, coll a c"
        " e, coll b d e, coll a n p, coll c d p, coll b n q, coll c d q ? cong"
        " e p e q"
    )

    print("=" * 60)
    print("Bridge Test: Connecting DDAR to Heuristic Generator")
    print("=" * 60)

    # Parse the problem
    print("\n1. Parsing problem...")
    problem = AGProblem.parse(test_problem)
    print(f"   Found {len(problem.points)} points")
    print(f"   Found {len(problem.preds)} predicates")

    # Run DDAR
    print("\n2. Running DDAR deduction...")
    ddar = DDAR(problem.points)
    for pred in problem.preds:
        ddar.force_pred(pred)
    ddar.deduction_closure(progress_dot=False)
    print(f"   Deduction complete")

    # Extract lines and circles
    print("\n3. Extracting deduced geometry...")
    defined_lines, defined_circles = extract_lines_and_circles(ddar)
    print(f"   Found {len(defined_lines)} lines")
    print(f"   Found {len(defined_circles)} circles")

    # Show some details about what was found
    if defined_lines:
        print(f"\n   Sample lines:")
        for i, line in enumerate(defined_lines[:3]):
            print(f"     Line {i + 1}: defined by {[p.name for p in line.points]}")

    if defined_circles:
        print(f"\n   Sample circles:")
        for i, circle in enumerate(defined_circles[:3]):
            print(f"     Circle {i + 1}: defined by {[p.name for p in circle.points]}")

    # Generate heuristic candidates
    print("\n4. Generating heuristic candidates...")
    candidates = get_heuristic_candidates(
        problem.points, defined_lines, defined_circles
    )

    print(f"\n   SUCCESS: Generated {len(candidates)} heuristic candidates!")

    if candidates:
        print(f"\n   Candidate details:")
        for i, (cand, preds) in enumerate(candidates[:10]):  # Show first 10
            print(
                f"     {i + 1}. {cand.name}: ({cand.value[0]:.6f}, {cand.value[1]:.6f})"
            )
            print(f"        Predicates: {[str(p) for p in preds]}")

        if len(candidates) > 10:
            print(f"     ... and {len(candidates) - 10} more")
    else:
        print(
            "\n   WARNING: No candidates generated (this may be normal for simple geometries)"
        )

    print("\n" + "=" * 60)
    print("Bridge test complete!")
    print("=" * 60)
