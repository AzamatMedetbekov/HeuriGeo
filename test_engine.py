import graph as gh
from problem import EmptyDependency

g = gh.Graph()

# Add points
a, b, c, m = g.add_points(["a", "b", "c", "m"])

# Declare M as midpoint of AB (adds collinearity + AM = MB)
deps = EmptyDependency(level=0, rule_name="manual")
g.add_midp([m, a, b], deps)

print("Graph created successfully. Nodes:", [p.name for p in g.all_points()])
print("Midpoint check:", g.check_midp([m, a, b]))