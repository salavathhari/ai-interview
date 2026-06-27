"""
Skill Dependency Mapper — prerequisite chains and learning order.

Defines which skills depend on which other skills, and generates
topologically sorted learning sequences.
"""

from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple


# Comprehensive dependency map: skill → list of prerequisites
SKILL_DEPENDENCIES: Dict[str, List[str]] = {
    # ── Programming Languages ──
    "python": [],
    "java": ["python"],
    "c++": [],
    "javascript": [],
    "typescript": ["javascript"],
    "go": ["python"],
    "rust": ["c++"],
    "kotlin": ["java"],
    "swift": ["java"],

    # ── Web Frontend ──
    "html": [],
    "css": ["html"],
    "javascript_frameworks": ["javascript"],
    "react": ["javascript", "html", "css"],
    "vue": ["javascript", "html", "css"],
    "angular": ["typescript", "html", "css"],
    "nextjs": ["react", "javascript"],
    "tailwindcss": ["css"],
    "sass": ["css"],

    # ── Web Backend ──
    "rest_api": ["python"],
    "fastapi": ["python", "rest_api"],
    "django": ["python", "rest_api"],
    "flask": ["python", "rest_api"],
    "spring": ["java", "rest_api"],
    "express": ["javascript", "rest_api"],
    "graphql": ["rest_api"],

    # ── Databases ──
    "sql": [],
    "mysql": ["sql"],
    "postgresql": ["sql"],
    "sqlite": ["sql"],
    "mongodb": [],
    "redis": [],
    "elasticsearch": [],
    "cassandra": ["sql"],

    # ── ORMs ──
    "sqlalchemy": ["python", "sql"],
    "prisma": ["typescript", "sql"],
    "django_orm": ["django", "sql"],
    "sequelize": ["javascript", "sql"],

    # ── DevOps / Cloud ──
    "git": [],
    "linux": [],
    "bash": ["linux"],
    "docker": ["linux"],
    "docker_compose": ["docker"],
    "kubernetes": ["docker", "docker_compose"],
    "terraform": ["cloud_basics"],
    "ci_cd": ["git", "docker"],
    "aws": ["linux", "docker"],
    "gcp": ["linux", "docker"],
    "azure": ["linux", "docker"],
    "aws_ec2": ["aws"],
    "aws_s3": ["aws"],
    "aws_lambda": ["aws"],
    "aws_rds": ["aws", "sql"],
    "aws_cloudfront": ["aws"],
    "nginx": ["linux"],

    # ── Data / ML ──
    "statistics": [],
    "linear_algebra": [],
    "python_data": ["python", "statistics"],
    "pandas": ["python_data"],
    "numpy": ["python_data"],
    "matplotlib": ["python_data"],
    "scikit_learn": ["python_data", "statistics"],
    "tensorflow": ["python_data", "linear_algebra"],
    "pytorch": ["python_data", "linear_algebra"],
    "machine_learning": ["statistics", "linear_algebra", "python_data"],
    "deep_learning": ["machine_learning", "tensorflow"],
    "nlp": ["deep_learning"],
    "computer_vision": ["deep_learning"],
    "data_pipeline": ["python", "sql"],
    "apache_spark": ["python_data", "sql"],
    "kafka": ["python"],

    # ── CS Fundamentals ──
    "data_structures": [],
    "algorithms": ["data_structures"],
    "dsa": ["data_structures", "algorithms"],
    "object_oriented_programming": [],
    "operating_systems": [],
    "computer_networks": [],
    "database_management": ["sql"],
    "compiler_design": ["data_structures"],
    "design_patterns": ["object_oriented_programming"],

    # ── System Design ──
    "system_design_basics": ["computer_networks", "sql", "linux"],
    "distributed_systems": ["system_design_basics"],
    "microservices": ["system_design_basics", "docker"],
    "message_queues": ["distributed_systems"],
    "caching": ["redis", "system_design_basics"],
    "load_balancing": ["system_design_basics"],
    "api_design": ["rest_api", "system_design_basics"],

    # ── Testing ──
    "unit_testing": [],
    "integration_testing": ["unit_testing"],
    "pytest": ["python", "unit_testing"],
    "jest": ["javascript", "unit_testing"],
    "selenium": ["python", "web_basics"],
    "cypress": ["javascript", "web_basics"],

    # ── Security ──
    "web_security": [],
    "authentication": ["web_security", "rest_api"],
    "oauth": ["authentication"],
    "jwt": ["authentication"],
    "owasp": ["web_security"],

    # ── Soft Skills ──
    "communication": [],
    "teamwork": [],
    "leadership": ["teamwork"],
    "problem_solving": [],
    "time_management": [],
    "presentation": ["communication"],

    # ── Version Control ──
    "git_branching": ["git"],
    "pull_requests": ["git"],
    "code_review": ["git"],
}


class SkillDependencyMapper:
    """Maps prerequisite relationships and generates learning order."""

    def __init__(self, custom_deps: Dict[str, List[str]] = None):
        self.dependencies = dict(SKILL_DEPENDENCIES)
        if custom_deps:
            self.dependencies.update(custom_deps)

    def get_prerequisites(self, skill: str) -> List[str]:
        """Get direct prerequisites for a skill."""
        return self.dependencies.get(skill.lower(), [])

    def get_all_prerequisites(self, skill: str) -> List[str]:
        """Get ALL transitive prerequisites for a skill (BFS)."""
        visited = set()
        queue = deque([skill.lower()])
        prereqs = []

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for prereq in self.dependencies.get(current, []):
                if prereq not in visited:
                    prereqs.append(prereq)
                    queue.append(prereq)

        return prereqs

    def get_dependents(self, skill: str) -> List[str]:
        """Get skills that depend on this skill."""
        dependents = []
        skill_lower = skill.lower()
        for s, deps in self.dependencies.items():
            if skill_lower in deps:
                dependents.append(s)
        return dependents

    def topological_sort(self, skills: List[str]) -> List[str]:
        """
        Return skills in valid learning order using topological sort.
        Skills with no prerequisites come first.
        """
        skill_set = {s.lower() for s in skills}
        # Include all transitive prerequisites
        all_needed = set(skill_set)
        for skill in list(skill_set):
            for prereq in self.get_all_prerequisites(skill):
                all_needed.add(prereq)

        # Build subgraph
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        for skill in all_needed:
            if skill not in in_degree:
                in_degree[skill] = 0
            for prereq in self.dependencies.get(skill, []):
                if prereq in all_needed:
                    graph[prereq].append(skill)
                    in_degree[skill] += 1

        # Kahn's algorithm
        queue = deque([s for s in all_needed if in_degree[s] == 0])
        result = []
        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Only return skills that were requested (or are prerequisites)
        return [s for s in result if s in skill_set]

    def get_learning_path(self, missing_skills: List[str]) -> List[Dict]:
        """
        Generate a structured learning path with dependencies mapped.
        Returns ordered list of {skill, prerequisites, dependents, difficulty}.
        """
        ordered = self.topological_sort(missing_skills)
        path = []

        for i, skill in enumerate(ordered):
            prereqs = [p for p in self.get_prerequisites(skill) if p in ordered[:i]]
            dependents = [d for d in self.get_dependents(skill) if d in ordered[i+1:]]

            # Estimate difficulty based on dependency depth
            depth = len(self.get_all_prerequisites(skill))
            if depth == 0:
                difficulty = "Easy"
            elif depth <= 2:
                difficulty = "Medium"
            else:
                difficulty = "Hard"

            path.append({
                "skill": skill,
                "order": i + 1,
                "prerequisites": prereqs,
                "dependents": dependents,
                "difficulty": difficulty,
                "estimated_hours": self._estimate_hours(skill, difficulty),
            })

        return path

    def detect_cycles(self) -> List[str]:
        """Detect any circular dependencies."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = defaultdict(int)
        cycles = []

        def dfs(node, path):
            color[node] = GRAY
            for neighbor in self.dependencies.get(node, []):
                if color[neighbor] == GRAY:
                    cycle_start = path.index(neighbor)
                    cycles.append(" -> ".join(path[cycle_start:] + [neighbor]))
                elif color[neighbor] == WHITE:
                    dfs(neighbor, path + [neighbor])
            color[node] = BLACK

        for skill in self.dependencies:
            if color[skill] == WHITE:
                dfs(skill, [skill])

        return cycles

    def _estimate_hours(self, skill: str, difficulty: str) -> float:
        """Estimate learning hours based on skill and difficulty."""
        base_hours = {"Easy": 4, "Medium": 8, "Hard": 14}
        hours = base_hours.get(difficulty, 8)

        # Adjust for known complex topics
        complex_skills = {"kubernetes", "distributed_systems", "system_design_basics",
                         "deep_learning", "machine_learning", "terraform", "apache_spark"}
        if skill.lower() in complex_skills:
            hours *= 1.5

        return round(hours, 1)

    def export_dependencies_db(self) -> List[Dict]:
        """Export all dependencies for database seeding."""
        records = []
        for skill, prereqs in self.dependencies.items():
            for prereq in prereqs:
                records.append({
                    "skill_name": skill,
                    "prerequisite": prereq,
                    "dependency_type": "required",
                })
        return records
