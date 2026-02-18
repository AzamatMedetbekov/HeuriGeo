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

"""Geometric operations for heuristic extension (Reflections, Projections, Intersections)."""

import numpy as np
import numericals as ng


def reflect_point_wrt_point(p: ng.NumPoint, center: ng.NumPoint) -> ng.NumPoint:
    """Heuristic 4: Reflection of point P with respect to center."""
    return 2 * center - p


def foot_of_perpendicular(p: ng.NumPoint, line: ng.NumLine) -> ng.NumPoint:
    """Heuristic 5: Foot of perpendicular from P to line."""
    signed_dist = np.dot(p, line.n) - line.c
    return p - signed_dist * line.n


def intersect_line_circle(line: ng.NumLine, circle: ng.NumCircle) -> list[ng.NumPoint]:
    """Finds intersection of a line and a circle for Heuristic 2.

    Returns:
        A list of intersection points (0, 1, or 2 points).
    """
    proj_O = foot_of_perpendicular(circle.center, line)
    dist_O_to_line = ng.distance(circle.center, proj_O)

    if dist_O_to_line > circle.r + ng.ATOM:
        return []

    discriminant = circle.r**2 - dist_O_to_line**2
    if discriminant < 0:
        discriminant = 0

    dist_along_line = np.sqrt(discriminant)
    line_dir = ng.perp_rot(line.n)

    if dist_along_line < ng.ATOM:
        return [proj_O]

    return [proj_O + dist_along_line * line_dir, proj_O - dist_along_line * line_dir]


def is_point_on_line(p: ng.NumPoint, line: ng.NumLine) -> bool:
    return line.distance(p) < 1e-4


def is_point_on_circle(p: ng.NumPoint, circle: ng.NumCircle) -> bool:
    return circle.distance(p) < 1e-4
