# AlphaGeometry2 with Heuristic Extension

This repository extends the [AlphaGeometry2](https://www.jmlr.org/papers/v26/25-1654.html) symbolic theorem prover with a **rule-based heuristic extension** for auxiliary point generation inspired by human geometric intuition.

## Overview

**Base System**: AlphaGeometry2 (AG2) — Gold-medalist level geometry prover by [Chervonyi et al. (2025)](https://www.jmlr.org/papers/v26/25-1654.html)  
**Extension**: Rule-Based Heuristics — Automated auxiliary point generation without LLMs

The original AG2 uses a language model to suggest auxiliary points for difficult problems. This extension adds a deterministic, rule-based alternative that generates candidate points using classic geometric constructions (midpoints, reflections, perpendicular feet).

## Key Enhancements

### Heuristic Extension Module
- **`heuri_heuristics.py`**: Implements H2, H3, H4, H5 heuristics
  - **H2**: Intersections of lines and circles
  - **H3**: Midpoints of point pairs
  - **H4**: Reflections of points w.r.t. other points
  - **H5**: Feet of perpendiculars from points to lines
- **`heuri_math.py`**: Core geometric operations (reflections, projections, intersections)

### Try-Fail-Retry Loop
The test suite now implements an automated loop:
1. **Try**: Attempt proof with base DDAR
2. **Fail**: If stuck, generate auxiliary point candidates
3. **Retry**: Try each candidate (up to 10) until proof succeeds

## Installation

```bash
$ python3 -m venv ag2
$ source ag2/bin/activate
$ pip install numpy
```

## Usage

Run the prover on IMO problems:

```bash
$ python -m test
```

The output shows:
- Problems solved by DDAR alone
- Problems solved with heuristic auxiliary points (if found)
- Number of candidate points generated per problem

## Architecture

```
DDAR (Deductive Database Algebraic Reasoning)
├── ddar.py              — Main logical engine
├── elimination.py       — Gaussian elimination systems
├── numericals.py        — Euclidean geometry primitives
├── parse.py             — Problem format parser
├── heuri_heuristics.py  — Auxiliary point generator (NEW)
├── heuri_math.py        — Geometric operations (NEW)
└── test.py              — IMO problem test suite
```

## How It Works

When DDAR cannot prove a theorem:

1. **Generate Candidates**: `get_heuristic_candidates()` scans the current geometry and proposes:
   - Line-Circle Intersections (H2): Intersection points of existing lines and circles
   - Midpoints (H3): For any two points A, B → candidate point at (A+B)/2
   - Reflections (H4): For point P w.r.t. center C → candidate at 2C - P
   - Perpendicular Feet (H5): From point P to line L → orthogonal projection

2. **Non-Trivial Filtering**: Candidates must land on existing lines or circles (not coincident with construction parents)

3. **K-Attempts**: Try up to 10 shuffled candidates, running full DDAR closure each time

4. **Success**: If any candidate enables the proof, report the auxiliary point used

## Original Paper

This work extends the AlphaGeometry2 system described in:

```
@article{chervonyi2025gold,
  title={Gold-medalist performance in solving olympiad geometry with alphageometry2},
  author={Chervonyi, Yuri and Trinh, Trieu H and Ol{\v{s}}{\'a}k, Miroslav and Yang, Xiaomeng and Nguyen, Hoang H and Menegali, Marcelo and Jung, Junehyuk and Kim, Junsu and Verma, Vikas and Le, Quoc V and others},
  journal={Journal of Machine Learning Research},
  volume={26},
  number={241},
  pages={1--39},
  year={2025}
}
```

## License

Copyright 2025-2026 Google LLC

Licensed under the Apache License, Version 2.0.

This is not an official Google product.
