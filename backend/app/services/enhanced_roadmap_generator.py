"""
Enhanced Roadmap Generator — Production-grade AI Career Learning Planner.

Generates structured learning phases with milestones, resources,
practice questions, coding problems, and AI mentor recommendations.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.career import JobDescription, ResumeAnalysis, SkillGapAnalysis, LearningRoadmap, CareerReadiness
from app.models.interview_session import InterviewSession
from app.models.coding_challenge import CodingSession
from app.models.intelligence import PerformanceMetrics, SkillAnalytics, LearningProgress
from app.services.skill_dependency_mapper import SkillDependencyMapper
from app.services.career_service import CareerService


# ── Skill Knowledge Base ──

SKILL_RESOURCES = {
    "docker": {
        "docs": ["https://docs.docker.com/get-started/", "https://docs.docker.com/compose/"],
        "youtube": ["Docker Tutorial for Beginners (TechWorld with Nana)", "Docker Full Course (freeCodeCamp)"],
        "practice": ["Dockerize a FastAPI app", "Set up docker-compose for a multi-service app"],
        "interview_questions": [
            "What is the difference between a Docker image and a container?",
            "How does Docker differ from virtual machines?",
            "Explain Dockerfile instructions: COPY vs ADD, RUN vs CMD",
            "What is docker-compose and when would you use it?",
            "How do you manage persistent data in Docker?",
        ],
        "coding_problems": [],
    },
    "kubernetes": {
        "docs": ["https://kubernetes.io/docs/home/", "https://kubernetes.io/docs/tutorials/"],
        "youtube": ["Kubernetes Tutorial for Beginners (TechWorld with Nana)", "K8s Full Course (freeCodeCamp)"],
        "practice": ["Deploy a Dockerized app to K8s", "Set up horizontal pod autoscaling"],
        "interview_questions": [
            "What is a Pod in Kubernetes?",
            "Explain the difference between Deployment and StatefulSet",
            "How does Kubernetes handle service discovery?",
            "What is a ConfigMap and how is it different from a Secret?",
            "Explain the Kubernetes networking model",
        ],
        "coding_problems": [],
    },
    "aws": {
        "docs": ["https://docs.aws.amazon.com/", "https://aws.amazon.com/getting-started/"],
        "youtube": ["AWS Full Course (freeCodeCamp)", "AWS Certified Solutions Architect (Stephane Maarek)"],
        "practice": ["Deploy a static site to S3 + CloudFront", "Set up EC2 with auto-scaling group"],
        "interview_questions": [
            "What is the difference between S3 and EBS?",
            "Explain AWS IAM and best practices for permissions",
            "How does AWS Lambda work and when should you use it?",
            "What is the shared responsibility model?",
            "Compare EC2, ECS, and EKS for container deployment",
        ],
        "coding_problems": [],
    },
    "redis": {
        "docs": ["https://redis.io/docs/", "https://redis.io/docs/get-started/"],
        "youtube": ["Redis Crash Course (Traversy Media)", "Redis Full Course (freeCodeCamp)"],
        "practice": ["Implement API response caching with Redis", "Build a rate limiter using Redis"],
        "interview_questions": [
            "What data structures does Redis support?",
            "Explain Redis persistence: RDB vs AOF",
            "How would you implement a distributed lock with Redis?",
            "What is Redis Pub/Sub and when to use it?",
            "How does Redis handle memory eviction?",
        ],
        "coding_problems": [],
    },
    "kafka": {
        "docs": ["https://kafka.apache.org/documentation/", "https://developer.confluent.io/quickstart/kafka/"],
        "youtube": ["Apache Kafka in 5 Minutes", "Kafka Full Course (freeCodeCamp)"],
        "practice": ["Build a message producer/consumer in Python", "Implement event-driven architecture with Kafka"],
        "interview_questions": [
            "What is the difference between a topic and a partition?",
            "Explain consumer groups in Kafka",
            "How does Kafka achieve message ordering?",
            "What is the difference between Kafka and RabbitMQ?",
            "How do you handle message replay in Kafka?",
        ],
        "coding_problems": [],
    },
    "terraform": {
        "docs": ["https://developer.hashicorp.com/terraform/docs", "https://developer.hashicorp.com/terraform/tutorials"],
        "youtube": ["Terraform Course (freeCodeCamp)", "Terraform for Beginners (TechWorld with Nana)"],
        "practice": ["Provision AWS infrastructure with Terraform", "Build reusable Terraform modules"],
        "interview_questions": [
            "What is Terraform state and why is it important?",
            "Explain the difference between terraform plan and terraform apply",
            "How do you manage secrets in Terraform?",
            "What are Terraform modules and when should you use them?",
            "How does Terraform handle drift detection?",
        ],
        "coding_problems": [],
    },
    "system_design_basics": {
        "docs": ["https://github.com/donnemartin/system-design-primer", "https://bytebytego.com/"],
        "youtube": ["System Design Interview (Alex Xu)", "Gaurav Sen System Design"],
        "practice": ["Design a URL shortener", "Design a chat application"],
        "interview_questions": [
            "Design a URL shortener like bit.ly",
            "Design a rate limiter",
            "Design a notification system",
            "How would you design a news feed like Twitter?",
            "Design a distributed cache",
        ],
        "coding_problems": [],
    },
    "data_structures": {
        "docs": ["https://wiki.c2.com/?DataStructures", "https://www.geeksforgeeks.org/data-structures/"],
        "youtube": ["Data Structures Easy to Advanced (William Fiset)", "DSA Full Course (take U forward)"],
        "practice": ["Implement a hash map from scratch", "Build a binary search tree"],
        "interview_questions": [
            "When would you use a hash map vs a tree map?",
            "Explain the time complexity of operations on different data structures",
            "How does a heap differ from a binary search tree?",
            "What is a trie and when would you use it?",
            "Explain the difference between stack and queue",
        ],
        "coding_problems": ["Two Sum", "Valid Parentheses", "Merge Two Sorted Lists", "LRU Cache"],
    },
    "algorithms": {
        "docs": ["https://www.geeksforgeeks.org/fundamentals-of-algorithms/", "https://algorithm-visualizer.org/"],
        "youtube": ["Algorithms Course (MIT OpenCourseWare)", "Algorithm Design & Analysis (Abdul Bari)"],
        "practice": ["Implement binary search variations", "Solve 20 LeetCode easy problems"],
        "interview_questions": [
            "Explain Big-O notation for common operations",
            "When would you use dynamic programming vs greedy?",
            "How does merge sort achieve O(n log n)?",
            "Explain the difference between BFS and DFS",
            "What is tail recursion and why does it matter?",
        ],
        "coding_problems": ["Binary Search", "Merge Sort", "Quick Select", "Top K Frequent Elements"],
    },
    "python": {
        "docs": ["https://docs.python.org/3/tutorial/", "https://realpython.com/"],
        "youtube": ["Python Full Course (freeCodeCamp)", "Corey Schafer Python Tutorials"],
        "practice": ["Build a REST API with FastAPI", "Automate a data pipeline with Python"],
        "interview_questions": [
            "Explain Python's GIL and its implications",
            "What are decorators and how do they work?",
            "Difference between list comprehension and generator expression?",
            "How does Python memory management work?",
            "Explain *args and **kwargs",
        ],
        "coding_problems": ["FizzBuzz", "Palindrome Check", "Anagram Detection", "Matrix Rotation"],
    },
    "sql": {
        "docs": ["https://www.sqlitetutorial.net/", "https://www.postgresql.org/docs/"],
        "youtube": ["SQL Tutorial (freeCodeCamp)", "SQL for Data Science (UC Davis - Coursera)"],
        "practice": ["Write complex JOINs and subqueries", "Optimize slow queries with EXPLAIN"],
        "interview_questions": [
            "What is the difference between WHERE and HAVING?",
            "Explain different types of JOINs",
            "What are database indexes and when to use them?",
            "Explain ACID properties",
            "What is the difference between DELETE, TRUNCATE, and DROP?",
        ],
        "coding_problems": ["Second Highest Salary", "Department Top Salaries", "Consecutive Numbers"],
    },
    "fastapi": {
        "docs": ["https://fastapi.tiangolo.com/tutorial/", "https://fastapi.tiangolo.com/advanced/"],
        "youtube": ["FastAPI Course (freeCodeCamp)", "FastAPI Full Tutorial (TechWorld with Nana)"],
        "practice": ["Build a CRUD API with authentication", "Add WebSocket support to FastAPI"],
        "interview_questions": [
            "How does FastAPI achieve high performance?",
            "Explain dependency injection in FastAPI",
            "How do you handle background tasks in FastAPI?",
            "What is the difference between FastAPI and Flask?",
            "How do you implement authentication in FastAPI?",
        ],
        "coding_problems": [],
    },
    "react": {
        "docs": ["https://react.dev/learn", "https://react.dev/reference/"],
        "youtube": ["React Course (freeCodeCamp)", "React Full Stack (Traversy Media)"],
        "practice": ["Build a todo app with hooks", "Create a dashboard with React Router"],
        "interview_questions": [
            "Explain the virtual DOM and reconciliation",
            "What are React hooks and why were they introduced?",
            "Explain useEffect cleanup and dependency arrays",
            "What is the difference between state and props?",
            "How do you optimize React performance?",
        ],
        "coding_problems": [],
    },
    "git": {
        "docs": ["https://git-scm.com/doc", "https://github.com/learn"],
        "youtube": ["Git and GitHub Crash Course (Traversy Media)", "Git Full Course (freeCodeCamp)"],
        "practice": ["Practice branching and merging strategies", "Set up a CI/CD pipeline with GitHub Actions"],
        "interview_questions": [
            "What is the difference between git merge and git rebase?",
            "How do you resolve merge conflicts?",
            "Explain git stash and when to use it",
            "What is a detached HEAD state?",
            "How does git cherry-pick work?",
        ],
        "coding_problems": [],
    },
    "linux": {
        "docs": ["https://linuxcommand.org/", "https://www.redhat.com/en/topics/linux"],
        "youtube": ["Linux Full Course (freeCodeCamp)", "Linux Administration (LearnLinuxTV)"],
        "practice": ["Set up a Linux server with SSH", "Write bash scripts for automation"],
        "interview_questions": [
            "What is the difference between soft and hard links?",
            "How do you check open ports on a Linux system?",
            "Explain file permissions in Linux",
            "What is cgroups and how is it used in containers?",
            "How do you troubleshoot a slow Linux server?",
        ],
        "coding_problems": [],
    },
}

# ── Coding Problem Database ──

CODING_PROBLEMS_BY_SKILL = {
    "data_structures": [
        {"title": "Two Sum", "difficulty": "Easy", "topic": "HashMap", "leetcode": "1"},
        {"title": "Valid Parentheses", "difficulty": "Easy", "topic": "Stack", "leetcode": "20"},
        {"title": "Merge Two Sorted Lists", "difficulty": "Easy", "topic": "Linked List", "leetcode": "21"},
        {"title": "LRU Cache", "difficulty": "Medium", "topic": "Design", "leetcode": "146"},
    ],
    "algorithms": [
        {"title": "Binary Search", "difficulty": "Easy", "topic": "Search", "leetcode": "704"},
        {"title": "Merge Intervals", "difficulty": "Medium", "topic": "Sorting", "leetcode": "56"},
        {"title": "Top K Frequent Elements", "difficulty": "Medium", "topic": "Heap", "leetcode": "347"},
        {"title": "Word Search", "difficulty": "Medium", "topic": "Backtracking", "leetcode": "79"},
    ],
    "sql": [
        {"title": "Second Highest Salary", "difficulty": "Medium", "topic": "SQL", "leetcode": "176"},
        {"title": "Department Top Salaries", "difficulty": "Hard", "topic": "SQL", "leetcode": "185"},
        {"title": "Consecutive Numbers", "difficulty": "Medium", "topic": "SQL", "leetcode": "180"},
    ],
    "python": [
        {"title": "Two Sum", "difficulty": "Easy", "topic": "Array", "leetcode": "1"},
        {"title": "Longest Substring Without Repeating Characters", "difficulty": "Medium", "topic": "Sliding Window", "leetcode": "3"},
        {"title": "Container With Most Water", "difficulty": "Medium", "topic": "Two Pointers", "leetcode": "11"},
    ],
    "docker": [],
    "kubernetes": [],
    "aws": [],
    "redis": [
        {"title": "Implement LRU Cache", "difficulty": "Medium", "topic": "Design", "leetcode": "146"},
    ],
}


class _RoadmapCache:
    """Simple LRU cache for roadmap generation results."""

    def __init__(self, max_size: int = 64, ttl_seconds: int = 300):
        self._cache: Dict[tuple, tuple] = {}  # key -> (result, timestamp)
        self._max_size = max_size
        self._ttl = ttl_seconds
        import threading
        self._lock = threading.Lock()

    def get(self, key: tuple):
        import time
        with self._lock:
            if key in self._cache:
                result, ts = self._cache[key]
                if time.time() - ts < self._ttl:
                    return result
                del self._cache[key]
            return None

    def set(self, key: tuple, result):
        import time
        with self._lock:
            if len(self._cache) >= self._max_size:
                oldest = min(self._cache, key=lambda k: self._cache[k][1])
                del self._cache[oldest]
            self._cache[key] = (result, time.time())

    def invalidate(self, user_id: int):
        """Invalidate all entries for a user."""
        with self._lock:
            to_delete = [k for k in self._cache if k[0] == user_id]
            for k in to_delete:
                del self._cache[k]


_roadmap_cache = _RoadmapCache()


class EnhancedRoadmapGenerator:
    """Generates production-grade learning roadmaps with phases, milestones, and resources."""

    def __init__(self, db: Session):
        self.db = db
        self.dep_mapper = SkillDependencyMapper()

    def generate(
        self,
        user_id: int,
        skill_gap_id: int,
        resume_analysis_id: Optional[int] = None,
        job_description_id: Optional[int] = None,
    ) -> Dict:
        """
        Generate a complete learning journey with phases, resources, and practice.
        """
        # Check cache
        cache_key = (user_id, skill_gap_id, resume_analysis_id, job_description_id)
        cached = _roadmap_cache.get(cache_key)
        if cached:
            return cached

        # Gather all data
        gap = self.db.query(SkillGapAnalysis).filter(SkillGapAnalysis.id == skill_gap_id).first()
        resume_data = self._get_resume_data(user_id, resume_analysis_id)
        jd_data = self._get_jd_data(user_id, job_description_id)
        interview_data = self._get_interview_data(user_id)
        coding_data = self._get_coding_data(user_id)
        career_readiness = self._get_career_readiness(user_id)

        # Parse missing skills from gap
        missing_skills = self._parse_json(gap.missing_skills) if gap else []
        priority_skills = self._parse_json(gap.priority_skills) if gap else []
        matched_skills = self._parse_json(gap.matched_skills) if gap else []

        # Get dependency-ordered learning path
        learning_path = self.dep_mapper.get_learning_path(missing_skills)

        # Organize into phases
        phases = self._organize_phases(
            learning_path, priority_skills, interview_data, coding_data, jd_data
        )

        # Calculate totals
        total_hours = sum(p["estimated_hours"] for p in phases for t in p["topics"])
        total_weeks = max(1, round(total_hours / 10))  # ~10 hours/week

        # Get career goal
        career_goal = jd_data.get("title", "Software Engineer") if jd_data else "Software Engineer"
        company = jd_data.get("company", "") if jd_data else ""

        # Generate daily plan
        daily_plan = self._generate_daily_plan(phases)

        # Generate AI mentor tips
        mentor_tips = self._generate_mentor_tips(
            matched_skills, missing_skills, interview_data, coding_data, career_readiness
        )

        # Build roadmap
        roadmap_data = {
            "career_goal": f"{career_goal}{' at ' + company if company else ''}",
            "total_hours": total_hours,
            "estimated_weeks": total_weeks,
            "current_readiness": career_readiness.get("overall_score", 0) if career_readiness else 0,
            "target_readiness": 85,
            "phases": phases,
            "daily_plan": daily_plan,
            "mentor_tips": mentor_tips,
            "skill_gap_summary": {
                "matched_count": len(matched_skills),
                "missing_count": len(missing_skills),
                "priority_count": len(priority_skills),
                "match_percentage": gap.match_percentage if gap else 0,
            },
            "interview_readiness": interview_data.get("overall_score", 0) if interview_data else 0,
            "coding_readiness": coding_data.get("overall_score", 0) if coding_data else 0,
        }

        # Cache result
        _roadmap_cache.set(cache_key, roadmap_data)

        return roadmap_data

    def _organize_phases(
        self, learning_path, priority_skills, interview_data, coding_data, jd_data
    ) -> List[Dict]:
        """Organize learning path into structured phases."""
        if not learning_path:
            return []

        phases = []
        phase_num = 0

        # Group by difficulty level
        easy = [p for p in learning_path if p["difficulty"] == "Easy"]
        medium = [p for p in learning_path if p["difficulty"] == "Medium"]
        hard = [p for p in learning_path if p["difficulty"] == "Hard"]

        # Phase 1: Fundamentals (Easy skills)
        if easy:
            phase_num += 1
            phases.append(self._build_phase(
                phase_num, "Foundation Building",
                "Master the core fundamentals required for your target role",
                "High" if any(p["skill"] in priority_skills for p in easy) else "Medium",
                easy, "foundation",
            ))

        # Phase 2: Core Skills (Medium skills)
        if medium:
            phase_num += 1
            phases.append(self._build_phase(
                phase_num, "Core Skill Development",
                "Build proficiency in essential technologies and frameworks",
                "High",
                medium, "core",
            ))

        # Phase 3: Advanced Topics (Hard skills)
        if hard:
            phase_num += 1
            phases.append(self._build_phase(
                phase_num, "Advanced Mastery",
                "Tackle complex topics that differentiate senior candidates",
                "High",
                hard, "advanced",
            ))

        # Phase 4: Interview Preparation
        phase_num += 1
        weak_interview = []
        if interview_data:
            for topic in interview_data.get("weak_topics", []):
                weak_interview.append(topic)
        if weak_interview or True:  # Always include interview prep
            phases.append(self._build_interview_phase(
                phase_num, weak_interview, interview_data
            ))

        # Phase 5: Coding Practice
        phase_num += 1
        weak_coding = []
        if coding_data:
            weak_coding = coding_data.get("weak_topics", [])
        phases.append(self._build_coding_phase(
            phase_num, weak_coding, coding_data
        ))

        return phases

    def _build_phase(self, num, title, objective, priority, topics, phase_type) -> Dict:
        """Build a single learning phase."""
        total_hours = sum(t["estimated_hours"] for t in topics)
        weeks = max(1, round(total_hours / 10))

        enriched_topics = []
        for t in topics:
            skill_key = t["skill"].lower()
            resources = SKILL_RESOURCES.get(skill_key, {})
            coding_probs = CODING_PROBLEMS_BY_SKILL.get(skill_key, [])

            enriched_topics.append({
                "name": t["skill"],
                "order": t["order"],
                "prerequisites": t["prerequisites"],
                "difficulty": t["difficulty"],
                "estimated_hours": t["estimated_hours"],
                "description": f"Learn {t['skill']} from fundamentals to practical application",
                "resources": {
                    "documentation": resources.get("docs", []),
                    "videos": resources.get("youtube", []),
                    "practice_projects": resources.get("practice", []),
                },
                "interview_questions": resources.get("interview_questions", []),
                "coding_problems": coding_probs,
            })

        return {
            "phase_number": num,
            "title": title,
            "objective": objective,
            "priority": priority,
            "estimated_hours": total_hours,
            "estimated_weeks": weeks,
            "phase_type": phase_type,
            "status": "not_started",
            "progress_percentage": 0,
            "topics": enriched_topics,
            "milestone": f"Complete all {len(topics)} topics and build a capstone project",
        }

    def _build_interview_phase(self, num, weak_topics, interview_data) -> Dict:
        """Build interview preparation phase."""
        all_interview_qs = []
        for skill in ["docker", "kubernetes", "aws", "redis", "python", "sql", "fastapi",
                       "react", "git", "linux", "data_structures", "algorithms"]:
            resource = SKILL_RESOURCES.get(skill, {})
            for q in resource.get("interview_questions", []):
                all_interview_qs.append({"skill": skill, "question": q})

        return {
            "phase_number": num,
            "title": "Interview Preparation",
            "objective": "Sharpen interview skills with targeted practice on weak areas",
            "priority": "High",
            "estimated_hours": 20,
            "estimated_weeks": 2,
            "phase_type": "interview",
            "status": "not_started",
            "progress_percentage": 0,
            "topics": [{
                "name": "Technical Interview Skills",
                "order": 1,
                "prerequisites": [],
                "difficulty": "Intermediate",
                "estimated_hours": 15,
                "description": "Practice answering technical questions confidently",
                "resources": {"documentation": [], "videos": [], "practice_projects": []},
                "interview_questions": [q["question"] for q in all_interview_qs[:30]],
                "coding_problems": [],
            }],
            "milestone": "Score 70%+ in mock interview sessions",
            "weak_areas": weak_topics,
        }

    def _build_coding_phase(self, num, weak_topics, coding_data) -> Dict:
        """Build coding practice phase."""
        all_coding = []
        for skill, problems in CODING_PROBLEMS_BY_SKILL.items():
            for p in problems:
                all_coding.append({**p, "skill": skill})

        return {
            "phase_number": num,
            "title": "Coding Challenge Mastery",
            "objective": "Strengthen problem-solving with targeted coding challenges",
            "priority": "High",
            "estimated_hours": 25,
            "estimated_weeks": 3,
            "phase_type": "coding",
            "status": "not_started",
            "progress_percentage": 0,
            "topics": [{
                "name": "Problem Solving Practice",
                "order": 1,
                "prerequisites": [],
                "difficulty": "Intermediate",
                "estimated_hours": 25,
                "description": "Solve coding challenges across key topics",
                "resources": {"documentation": [], "videos": [], "practice_projects": []},
                "interview_questions": [],
                "coding_problems": [f"{p['title']} ({p['difficulty']})" for p in all_coding[:20]],
            }],
            "milestone": "Solve 50+ problems with 80%+ acceptance rate",
            "weak_areas": weak_topics,
        }

    def _generate_daily_plan(self, phases) -> Dict:
        """Generate a suggested daily learning plan."""
        active_phase = None
        for p in phases:
            if p["status"] != "completed":
                active_phase = p
                break

        if not active_phase:
            active_phase = phases[0] if phases else None

        if not active_phase:
            return {
                "today_focus": "",
                "hours_today": 0,
                "activities": [],
                "streak_days": 0,
                "needs_analysis": True,
            }

        first_topic = active_phase["topics"][0] if active_phase["topics"] else None

        return {
            "today_focus": first_topic["name"] if first_topic else "Review previous topics",
            "hours_today": 2,
            "activities": [
                f"Read documentation for {first_topic['name']}" if first_topic else "Review notes",
                f"Watch tutorial video (30 min)" if first_topic else "Practice problems",
                f"Hands-on practice (1 hour)" if first_topic else "Review weak areas",
                "Solve 2-3 practice problems",
            ],
            "streak_days": 0,
            "needs_analysis": False,
        }

    def _generate_mentor_tips(self, matched, missing, interview, coding, readiness) -> List[Dict]:
        """Generate AI mentor recommendations."""
        tips = []

        if not matched:
            tips.append({
                "type": "warning",
                "title": "Build Your Foundation",
                "message": "Start with resume upload and skill gap analysis to get personalized recommendations.",
                "action": "Upload Resume",
                "action_url": "/resume",
            })
        elif missing:
            tips.append({
                "type": "priority",
                "title": "Focus on Missing Skills",
                "message": f"You're missing {len(missing)} skills. Prioritize: {', '.join(missing[:3])}",
                "action": "View Roadmap",
                "action_url": "/career/learning-roadmap",
            })

        if interview and interview.get("overall_score", 100) < 60:
            tips.append({
                "type": "urgent",
                "title": "Boost Interview Skills",
                "message": f"Your interview score is {interview['overall_score']}%. Practice weak areas: {', '.join(interview.get('weak_topics', [])[:3])}",
                "action": "Start Interview Prep",
                "action_url": "/career/learning-roadmap",
            })

        if coding and coding.get("overall_score", 100) < 60:
            tips.append({
                "type": "urgent",
                "title": "Strengthen Coding",
                "message": f"Coding score: {coding['overall_score']}%. Focus on: {', '.join(coding.get('weak_topics', [])[:3])}",
                "action": "Practice Coding",
                "action_url": "/coding",
            })

        if readiness and readiness.get("overall_score", 0) >= 70:
            tips.append({
                "type": "success",
                "title": "Great Progress!",
                "message": f"Your career readiness is {readiness['overall_score']}%. Keep pushing toward your goal.",
                "action": "View Dashboard",
                "action_url": "/career/dashboard",
            })

        tips.append({
            "type": "tip",
            "title": "Daily Learning Habit",
            "message": "Consistency beats intensity. 2 focused hours daily beats 10 hours on weekends.",
            "action": None,
        })

        return tips

    # ── Data Helpers ──

    def _get_resume_data(self, user_id, resume_analysis_id):
        if resume_analysis_id:
            a = self.db.query(ResumeAnalysis).filter(ResumeAnalysis.id == resume_analysis_id).first()
        else:
            a = self.db.query(ResumeAnalysis).filter(
                ResumeAnalysis.user_id == user_id
            ).order_by(ResumeAnalysis.created_at.desc()).first()
        if not a:
            return None
        return {"detected_skills": self._parse_json(a.detected_skills), "technologies": self._parse_json(a.technologies)}

    def _get_jd_data(self, user_id, job_description_id):
        if job_description_id:
            jd = self.db.query(JobDescription).filter(JobDescription.id == job_description_id).first()
        else:
            jd = self.db.query(JobDescription).filter(
                JobDescription.user_id == user_id
            ).order_by(JobDescription.created_at.desc()).first()
        if not jd:
            return None
        return {
            "title": jd.title, "company": jd.company,
            "required_skills": self._parse_json(jd.required_skills),
            "preferred_skills": self._parse_json(jd.preferred_skills),
        }

    def _get_interview_data(self, user_id):
        s = self.db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id, InterviewSession.status == "completed"
        ).order_by(InterviewSession.ended_at.desc()).first()
        if not s:
            return None
        topic_scores = {}
        for field, name in [("score_dsa", "dsa"), ("score_dbms", "dbms"), ("score_os", "os"),
                            ("score_cn", "cn"), ("score_oop", "oop"), ("score_system_design", "system_design")]:
            val = getattr(s, field, None)
            if val is not None:
                topic_scores[name] = val
        return {"overall_score": s.score, "topic_scores": topic_scores,
                "weak_topics": [t for t, v in topic_scores.items() if v < 60],
                "strong_topics": [t for t, v in topic_scores.items() if v >= 75]}

    def _get_coding_data(self, user_id):
        sessions = self.db.query(CodingSession).filter(
            CodingSession.user_id == user_id, CodingSession.status == "submitted"
        ).order_by(CodingSession.ended_at.desc()).limit(20).all()
        if not sessions:
            return None
        topic_scores = {}
        for cs in sessions:
            if cs.challenge and cs.challenge.topics:
                for t in cs.challenge.topics:
                    topic_scores.setdefault(t, []).append(cs.coding_score or 0)
        avg = {t: round(sum(v)/len(v), 1) for t, v in topic_scores.items()}
        return {"overall_score": round(sum(cs.coding_score or 0 for cs in sessions) / len(sessions), 1),
                "weak_topics": [t for t, s in avg.items() if s < 60],
                "strong_topics": [t for t, s in avg.items() if s >= 75]}

    def _get_career_readiness(self, user_id):
        r = self.db.query(CareerReadiness).filter(
            CareerReadiness.user_id == user_id
        ).order_by(CareerReadiness.created_at.desc()).first()
        if not r:
            return None
        return {"overall_score": r.overall_score, "resume_match": r.resume_match_score,
                "ats": r.ats_score, "interview": r.interview_score, "coding": r.coding_score}

    def _parse_json(self, val):
        if not val:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                p = json.loads(val)
                return p if isinstance(p, list) else []
            except (json.JSONDecodeError, KeyError, TypeError):
                return []
        return []
