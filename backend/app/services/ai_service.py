import random
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from app.services.ai_cache import ai_cache
from app.core.logging import logger
from app.models.api_usage import ApiUsage
from app.database import SessionLocal

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AIService:
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "between", "by", "can", "do", "does",
        "for", "from", "have", "how", "i", "in", "is", "it", "of", "on", "or", "the",
        "their", "this", "to", "what", "when", "with", "would", "you", "your"
    }

    TECHNICAL_SIGNALS = {
        "api", "architecture", "cache", "database", "deploy", "design", "docker", "error",
        "index", "latency", "load", "memory", "monitoring", "optimize", "performance",
        "query", "queue", "react", "scalability", "schema", "security", "service", "sql",
        "system", "test", "tradeoff", "transaction"
    }

    @staticmethod
    def _summarize_prompt(text: str, max_chars: int = 2000) -> str:
        """Prompt Compression: Truncate/Summarize large texts (like resumes) to save tokens."""
        if len(text) <= max_chars:
            return text
        # Simple compression: Keep first 1000 and last 1000 chars
        return f"{text[:1000]}\n[...truncated for token optimization...]\n{text[-1000:]}"

    @staticmethod
    def extract_skills(resume_text: str):
        """
        Mock AI Skill Extraction.
        In a real app, you'd use LLM to parse text into structured list.
        """
        keywords = ["Python", "JavaScript", "TypeScript", "React", "Node.js", "Express", 
                    "FastAPI", "Django", "Flask", "PostgreSQL", "SQL", "MongoDB", 
                    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "Java", "C++"]
        
        detected = [skill for skill in keywords if skill.lower() in resume_text.lower()]
        return detected

    @staticmethod
    def generate_questions(role: str, resume_text: str, count: int = 5):
        """
        Generate technical interview questions using OpenAI with Caching and Token Optimization.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_key_here":
            return AIService._generate_mock_question_batch(role, resume_text, count)

        # 1. Prompt Compression
        compressed_resume = AIService._summarize_prompt(resume_text)
        
        prompt = f"Role: {role}. Resume: {compressed_resume}. Generate {count} technical interview questions in JSON format."
        
        # 2. Caching Check
        model = "gpt-3.5-turbo"
        cached_result = ai_cache.get(prompt, model)
        if cached_result:
            print("AI Cache Hit!")
            return cached_result

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800, # 3. Token Limits
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            questions = data if isinstance(data, list) else data.get("questions", [])
            
            # 4. Store in Cache
            ai_cache.set(prompt, model, questions[:count])
            
            logger.info(f"AI Generation Success | Model: {model} | Count: {count}")
            return questions[:count]
        except Exception as e:
            logger.error(f"AI Generation Failed | Error: {str(e)}", exc_info=True)
            return AIService._generate_mock_question_batch(role, resume_text, count)

    @staticmethod
    def get_difficulty_adjustment(current_difficulty: str, score: int):
        """
        Calculates the next difficulty level based on current difficulty and score.
        """
        levels = ["Easy", "Medium", "Hard"]
        if score >= 8:
            # Level Up
            idx = levels.index(current_difficulty)
            return levels[min(idx + 1, 2)]
        elif score <= 4:
            # Level Down
            idx = levels.index(current_difficulty)
            return levels[max(idx - 1, 0)]
        return current_difficulty

    @staticmethod
    def get_next_topic_and_difficulty(
        role: str,
        interview_type: str,
        base_difficulty: str,
        previous_questions: list,
        weak_topics: list,
        strong_topics: list
    ) -> tuple[str, str, str]:
        """
        Determines the next topic, target difficulty, and context message.
        Returns (topic, difficulty, context_message)
        """
        import random
        role_str = role.strip()
        type_str = interview_type.strip()
        
        # Determine topic pools based on interview type
        if type_str == "HR":
            target_topics = ["HR"]
            weights = [1.0]
        elif type_str == "Coding":
            target_topics = ["DSA"]
            weights = [1.0]
        elif type_str == "System Design":
            target_topics = ["System Design"]
            weights = [1.0]
        else: # Technical
            if "frontend" in role_str.lower():
                target_topics = ["Role-Specific Skills", "Projects", "HR"]
                weights = [0.60, 0.20, 0.20]
            elif "ml" in role_str.lower() or "machine learning" in role_str.lower():
                target_topics = ["Role-Specific Skills", "Projects", "HR"]
                weights = [0.60, 0.30, 0.10]
            elif "backend" in role_str.lower():
                target_topics = ["Projects", "System Design", "OOP", "DBMS", "OS", "CN"]
                weights = [0.30, 0.15, 0.15, 0.20, 0.10, 0.10]
            else: # SDE default
                target_topics = ["DSA", "DBMS", "OS", "CN", "Projects", "HR"]
                weights = [0.40, 0.15, 0.15, 0.10, 0.15, 0.05]
        
        # If there are previous questions, check adaptive rules
        if previous_questions:
            last_q = previous_questions[-1]
            last_score = last_q.get("score")
            last_topic = last_q.get("topic")
            last_diff = last_q.get("difficulty") or "Medium"
            
            diff_levels = ["Easy", "Medium", "Hard"]
            
            if last_score is not None:
                if last_score >= 8:
                    # Strong answer: Increase difficulty and ask deeper follow-up
                    try:
                        idx = diff_levels.index(last_diff.capitalize())
                        next_diff = diff_levels[min(idx + 1, 2)]
                    except ValueError:
                        next_diff = "Hard"
                    return last_topic, next_diff, f"Follow-up: Candidate answered previous question on {last_topic} strongly (score: {last_score}). Ask a deeper, more advanced question probing on technical risks, trade-offs, or advanced scenarios."
                elif last_score <= 5:
                    # Weak answer: Ask conceptual clarification or simpler follow-up
                    try:
                        idx = diff_levels.index(last_diff.capitalize())
                        next_diff = diff_levels[max(idx - 1, 0)]
                    except ValueError:
                        next_diff = "Easy"
                    return last_topic, next_diff, f"Clarification: Candidate struggled with previous question on {last_topic} (score: {last_score}). Ask a simpler, more fundamental, or conceptual clarification question on the same topic."
        
        # Repeated mistakes logic
        mistake_topics = []
        if previous_questions:
            topic_scores = {}
            for q in previous_questions:
                t = q.get("topic")
                s = q.get("score")
                if t and s is not None:
                    topic_scores.setdefault(t, []).append(s)
            
            for t, scores in topic_scores.items():
                weak_count = sum(1 for s in scores if s <= 5)
                if weak_count >= 1:
                    mistake_topics.append(t)
        
        # If we have mistake topics (revisit them with 30% probability)
        if mistake_topics and random.random() < 0.30:
            chosen_topic = random.choice(mistake_topics)
            return chosen_topic, base_difficulty, f"Focus on weak area: Candidate has shown weaknesses in {chosen_topic} previously. Generate a question targeting this weak topic."
        
        # Otherwise, choose topic based on weights
        chosen_topic = random.choices(target_topics, weights=weights, k=1)[0]
        return chosen_topic, base_difficulty, "New topic: Generate a question on this topic based on the interview structure."

    @staticmethod
    def generate_next_question(
        role: str,
        interview_type: str,
        difficulty: str,
        resume_text: str,
        previous_questions: list,
        weak_topics: list,
        strong_topics: list,
        jd_text: str = ""
    ) -> dict:
        """
        Adaptive Question Generation.
        Moves difficulty up/down and selects topic based on role weights and candidate history.
        """
        api_key = os.getenv("OPENAI_API_KEY")

        # Calculate target topic, difficulty and context message
        target_topic, target_difficulty, context_message = AIService.get_next_topic_and_difficulty(
            role, interview_type, difficulty, previous_questions, weak_topics, strong_topics
        )

        if not api_key or api_key == "your_key_here":
            return AIService._generate_mock_questions(role, target_topic, target_difficulty, context_message, resume_text)

        history_text = "\n".join([f"Q: {q.get('question')} | A: {q.get('answer')} | Score: {q.get('score')}" for q in previous_questions])

        jd_section = ""
        if jd_text:
            jd_section = f"""
        Job Description context (use this to tailor questions to the role requirements):
        {jd_text[:3000]}...
        """

        prompt = f"""
        You are an expert technical interviewer for the position of {role}.
        The candidate is undergoing a {interview_type} interview.
        The candidate's resume highlights: {resume_text[:2000]}...
        {jd_section}
        Target Topic to test: {target_topic}
        Target Difficulty: {target_difficulty}
        Context / Adaptive Goal: {context_message}

        Previous Questions and Answers in this session:
        {history_text}

        Candidate's historical weak topics: {", ".join(weak_topics) if weak_topics else "None"}
        Candidate's historical strong topics: {", ".join(strong_topics) if strong_topics else "None"}

        Your task:
        Generate the NEXT interview question targeting {target_topic} at a {target_difficulty} difficulty.

        Guidelines:
        1. Contextualize the question using their resume projects/skills if applicable.
        2. If a Job Description is provided, prioritize topics and skills mentioned in it.
        3. Ensure the question behaves according to the Adaptive Goal:
           - If it is a 'Follow-up', make it a deeper, direct follow-up to their previous answer, probing technical depth or risks.
           - If it is a 'Clarification', ask a simpler conceptual clarification or definition about the previous topic.
           - If it is a 'New topic' or 'Focus on weak area', start a fresh question about that topic.
        4. Do NOT repeat any questions already asked in: {history_text}.
        5. Focus on deep engineering depth (trade-offs, concurrency, scaling, performance) for 'Hard' questions, and conceptual fundamentals for 'Easy' questions.

        Return ONLY a JSON object with these exact keys:
        {{
          "text": "The next question text...",
          "topic": "{target_topic}",
          "difficulty": "{target_difficulty}",
          "follow_up_reason": "An explanation of why this question was chosen in relation to the candidate's performance/history."
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={ "type": "json_object" }
            )
            # Log usage
            AIService._log_usage("gpt-3.5-turbo", "adaptive-questioning", response.usage)

            import json
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"Adaptive Generation Error: {e}")
            return AIService._generate_mock_questions(role, target_topic, target_difficulty, context_message, resume_text)

    @staticmethod
    def _generate_mock_questions(role: str, topic: str, difficulty: str, context: str, resume_text: str) -> dict:
        """
        Sophisticated Fallback Mock AI Question Generation based on exact pool.
        """
        import random
        
        pools = {
            "DSA": {
                "Easy": [
                    "Explain the difference between an Array and a Linked List in memory and access time.",
                    "What is a Hash Map, and how does it resolve key collisions?",
                    "What is recursion? Explain with a simple example like factorial."
                ],
                "Medium": [
                    "Explain BFS and DFS. In what scenarios would you choose one over the other?",
                    "Explain the difference between Merge Sort and Quick Sort in terms of average/worst time and space complexity.",
                    "What is binary search? What are the prerequisites and time complexity of binary search?"
                ],
                "Hard": [
                    "What is Dynamic Programming? Explain how you would solve the Knapsack or Fibonacci problem with memoization vs tabulation.",
                    "How do you detect a cycle in a directed graph? Explain the algorithm (DFS-based or Kahn's algorithm) and its complexity.",
                    "Explain the concept of an AVL tree or Red-Black tree. How do they maintain balance during insertions?"
                ]
            },
            "DBMS": {
                "Easy": [
                    "What is database normalization and what are the main differences between 1NF, 2NF, and 3NF?",
                    "What are the primary differences between DELETE, TRUNCATE, and DROP statements in SQL?",
                    "Explain primary keys, foreign keys, and unique constraints in database design."
                ],
                "Medium": [
                    "Explain indexing in databases. How does a B-Tree index speed up query execution, and what are its overheads?",
                    "What are the ACID properties in database transactions? Provide a concrete scenario where isolation is crucial.",
                    "Explain the differences between INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL JOIN with examples."
                ],
                "Hard": [
                    "Explain transaction isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable). What are dirty reads, non-repeatable reads, and phantom reads?",
                    "How would you optimize a slow-running SQL query that performs multiple joins on large tables? Explain query planning.",
                    "What are database locks? Explain the difference between shared locks, exclusive locks, and deadlocks in databases."
                ]
            },
            "OS": {
                "Easy": [
                    "What is the difference between a process and a thread?",
                    "What is virtual memory, and how does it benefit an operating system?"
                ],
                "Medium": [
                    "What is a deadlock? Explain the four Coffman conditions necessary for a deadlock to occur.",
                    "Explain paging and segmentation. What is thrashing, and how does an OS mitigate it?"
                ],
                "Hard": [
                    "How does the operating system handle context switching? What overheads are involved?",
                    "Describe different CPU scheduling algorithms (e.g. Round Robin, SRTF, Multi-level Queue) and their trade-offs."
                ]
            },
            "CN": {
                "Easy": [
                    "What are the key differences between TCP and UDP? Give scenarios where you would choose one over the other.",
                    "Explain the DNS lookup process when you enter a URL in a browser."
                ],
                "Medium": [
                    "What happens when you enter a URL in a browser? Step through the network protocol layers involved.",
                    "Explain HTTP vs HTTPS. How does the SSL/TLS handshake work at a high level to establish a secure connection?"
                ],
                "Hard": [
                    "Describe the TCP three-way handshake and four-way teardown. Why is there a TIME_WAIT state in teardown?",
                    "How does congestion control work in TCP? Explain slow start, congestion avoidance, fast retransmit, and recovery."
                ]
            },
            "OOP": {
                "Easy": [
                    "What are the four pillars of Object-Oriented Programming?",
                    "Explain the difference between abstraction and encapsulation with real-world examples."
                ],
                "Medium": [
                    "Explain polymorphism. What is the difference between compile-time (overloading) and runtime (overriding) polymorphism?",
                    "What is an abstract class vs an interface? When would you use which in design?"
                ],
                "Hard": [
                    "Explain the SOLID design principles. Give a concrete code example of the Liskov Substitution Principle.",
                    "How does multiple inheritance work, and what is the diamond problem? How is it resolved in Python (MRO) or Java?"
                ]
            },
            "System Design": {
                "Easy": [
                    "What is caching? How does it improve system performance?",
                    "What is load balancing and why do we need it in scale?"
                ],
                "Medium": [
                    "Design a URL shortener like Bit.ly. What are the key database and API requirements?",
                    "Explain caching strategies like Write-Through, Write-Back, and Cache-Aside. When do you use each?"
                ],
                "Hard": [
                    "How would you design a scalable notification service that can handle millions of push notifications per second?",
                    "Explain database sharding and partitioning. How does consistent hashing help in distributed databases?"
                ]
            },
            "Projects": {
                "Easy": [
                    "Describe the overall architecture of one of your recent projects listed on your resume.",
                    "What challenges did you face when integrating third-party APIs or libraries in your project?"
                ],
                "Medium": [
                    "Why did you choose your specific database (e.g. PostgreSQL, MongoDB, Redis) for your resume project?",
                    "How did you handle error tracking, validation, and logging in your application?"
                ],
                "Hard": [
                    "How would you scale your project to handle 100x the current user traffic? What bottlenecks would you expect in your database and api layers?",
                    "Explain how you would containerize your application and deploy it with high availability and load balancing."
                ]
            },
            "HR": {
                "Easy": [
                    "Tell me about yourself and your background.",
                    "What are your greatest technical strengths and weaknesses?"
                ],
                "Medium": [
                    "Describe a challenging technical problem you faced in a project and how you solved it.",
                    "Why are you interested in joining our company as a software developer?"
                ],
                "Hard": [
                    "Describe a situation where you had a conflict with a team member or a manager. How did you resolve it?",
                    "Tell me about a time you made a mistake in a production deployment. How did you handle it and what did you learn?"
                ]
            },
            "Role-Specific Skills": {
                "Easy": [
                    "What is JavaScript's event loop and how does it handle asynchronous callbacks?",
                    "What is a React Hook, and what rules must you follow when using hooks?",
                    "What is Python's Global Interpreter Lock (GIL), and how does it affect multi-threaded programs?"
                ],
                "Medium": [
                    "Explain the difference between let, const, and var in JavaScript.",
                    "What is React's Virtual DOM and how does reconciliation work?",
                    "Explain how machine learning supervised learning differs from unsupervised learning."
                ],
                "Hard": [
                    "What are React Server Components and how do they differ from client components?",
                    "Explain how transformer models work in machine learning.",
                    "Describe Python's memory management and garbage collection mechanism."
                ]
            }
        }

        # Normalize difficulty
        diff_key = difficulty.capitalize() if difficulty else "Medium"
        if diff_key not in ["Easy", "Medium", "Hard"]:
            diff_key = "Medium"
            
        topic_key = topic if topic in pools else "Projects"
        
        question_list = pools[topic_key][diff_key]
        question_text = random.choice(question_list)

        # Personalize if projects or skills and resume text is available
        if topic_key == "Projects" and resume_text:
            keywords = ["Python", "FastAPI", "React", "Docker", "AWS", "SQL", "PostgreSQL", "Java", "Kubernetes", "TypeScript"]
            detected = [k for k in keywords if k.lower() in resume_text.lower()]
            if detected:
                skill = random.choice(detected)
                if diff_key == "Easy":
                    question_text = f"Based on your resume mentioning {skill}, could you describe the overall architecture of the project where you used it?"
                elif diff_key == "Medium":
                    question_text = f"Why did you choose {skill} over other alternatives for your project?"
                else:
                    question_text = f"How did you handle scaling, caching, or latency bottlenecks in your project utilizing {skill}?"

        return {
            "text": question_text,
            "topic": topic_key,
            "difficulty": diff_key,
            "follow_up_reason": f"Fallback: selected {topic_key} ({diff_key}) due to '{context}'"
        }

    @staticmethod
    def _generate_mock_question_batch(role: str, resume_text: str, count: int = 5) -> list:
        """
        Generate a batch of mock questions across varied topics for the generate_questions endpoint.
        Returns a list of {text, topic, difficulty} dicts.
        """
        import random
        topics_cycle = ["DSA", "DBMS", "OS", "CN", "OOP", "System Design", "Projects", "HR"]
        difficulties = ["Easy", "Medium", "Hard"]
        results = []
        used_topics = set()
        for i in range(count):
            topic = topics_cycle[i % len(topics_cycle)]
            difficulty = difficulties[i % 3]
            q = AIService._generate_mock_questions(role, topic, difficulty, "Batch generation", resume_text)
            if q["text"] not in [r["text"] for r in results]:
                results.append({"text": q["text"], "topic": q["topic"], "difficulty": q["difficulty"]})
        return results[:count]

    @staticmethod
    def _log_usage(model: str, feature: str, usage_obj):
        """
        Log API usage to the database for admin monitoring.
        """
        if not usage_obj:
            return
        
        db = SessionLocal()
        try:
            # Simple cost calculation for gpt-3.5-turbo (approx)
            prompt_cost = 0.0015 / 1000
            completion_cost = 0.002 / 1000
            total_cost = (usage_obj.prompt_tokens * prompt_cost) + (usage_obj.completion_tokens * completion_cost)
            
            log = ApiUsage(
                model=model,
                feature=feature,
                prompt_tokens=usage_obj.prompt_tokens,
                completion_tokens=usage_obj.completion_tokens,
                total_tokens=usage_obj.total_tokens,
                cost=total_cost
            )
            db.add(log)
            db.commit()
        except Exception as e:
            print(f"Error logging API usage: {e}")
        finally:
            db.close()

    @staticmethod
    def evaluate_answer(question: str, answer: str):
        """
        Evaluate user's answer using OpenAI based on specific metrics:
        Technical Accuracy, Communication, Confidence, and Completeness.
        """
        obvious_low_quality = AIService._low_quality_answer_result(question, answer)
        if obvious_low_quality:
            return obvious_low_quality

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_key_here":
            return AIService._evaluate_mock_answer(question, answer)

        prompt = f"""
        You are an expert technical interviewer. Evaluate the candidate's answer based on the following metrics:
        1. Technical Accuracy (Is the technical explanation accurate?)
        2. Communication (How well does the candidate convey their thoughts?)
        3. Confidence (Does the candidate sound certain and authoritative?)
        4. Completeness (Did they answer all parts of the question?)

        Question: {question}
        Candidate Answer: {answer}
        
        Provide:
        1. A total score from 0 to 10.
        2. Individual scores (0-10) for: Accuracy, Communication, Confidence, Completeness.
        3. Detailed feedback explaining the score based on the metrics above.
        4. 2-3 specific improvement tips.
        
        Return the result as a raw JSON object with keys: 
        "score", "accuracy_score", "communication_score", "confidence_score", "completeness_score", "feedback", "improvement_tips".
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            # Log usage
            AIService._log_usage("gpt-3.5-turbo", "interview-evaluation", response.usage)

            import json
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(content)
            return {
                "score": int(data.get("score", 0)),
                "accuracy": int(data.get("accuracy_score", 0)),
                "communication": int(data.get("communication_score", 0)),
                "confidence": int(data.get("confidence_score", 0)),
                "completeness": int(data.get("completeness_score", 0)),
                "feedback": data.get("feedback", "No feedback provided."),
                "improvement_tips": data.get("improvement_tips", "No improvement tips provided.")
            }
        except Exception as e:
            print(f"OpenAI Evaluation Error: {e}")
            return AIService._evaluate_mock_answer(question, answer)

    @staticmethod
    def _evaluate_mock_answer(question: str, answer: str):
        """
        Content-aware fallback evaluation for local/dev mode.
        """
        normalized_answer = AIService._normalize_text(answer)
        answer_words = AIService._keywords(normalized_answer)
        question_keywords = AIService._keywords(question)
        word_count = len(re.findall(r"[a-zA-Z0-9+#.]+", normalized_answer))

        overlap = set(answer_words) & set(question_keywords)
        relevance = len(overlap) / max(len(set(question_keywords)), 1)
        technical_hits = len(set(answer_words) & AIService.TECHNICAL_SIGNALS)

        length_score = min(word_count / 45, 1.0) * 3.0
        relevance_score = min(relevance * 10, 1.0) * 3.0
        technical_score = min(technical_hits / 3, 1.0) * 2.0
        structure_score = AIService._structure_score(normalized_answer) * 2.0

        raw_score = length_score + relevance_score + technical_score + structure_score
        score = max(1, min(9, round(raw_score)))

        if word_count < 15:
            score = min(score, 4)
        if relevance < 0.08 and technical_hits == 0:
            score = min(score, 4)

        accuracy = max(1, min(10, round(score + (2 if relevance >= 0.2 else -1))))
        communication = max(1, min(10, round(score + (1 if AIService._structure_score(normalized_answer) >= 0.5 else 0))))
        confidence = max(1, min(10, round(score if "maybe" not in normalized_answer else score - 1)))
        completeness = max(1, min(10, round(score + (1 if word_count >= 45 else -1))))

        if score <= 4:
            feedback = (
                f"The answer is too brief or not specific enough for the question. It scored {score}/10 because it "
                "does not clearly explain the technical approach, trade-offs, or concrete examples."
            )
            tips = "1. Directly answer the question asked. 2. Add a concrete example, trade-off, and expected outcome. 3. Use relevant technical terms accurately."
        elif score <= 7:
            feedback = (
                f"The answer is partially correct and shows some relevant understanding with a score of {score}/10, "
                "but it needs more depth, examples, and clearer technical reasoning."
            )
            tips = "1. Structure the answer as problem, approach, trade-offs, and result. 2. Include one real project example. 3. Mention edge cases or failure modes."
        else:
            feedback = (
                f"The answer is strong and relevant with a score of {score}/10. It addresses the question with "
                "reasonable technical detail and clear communication."
            )
            tips = "1. Add measurable impact where possible. 2. Briefly compare alternatives. 3. Close with how you would validate the solution."

        return {
            "score": score,
            "accuracy": accuracy,
            "communication": communication,
            "confidence": confidence,
            "completeness": completeness,
            "feedback": feedback,
            "improvement_tips": tips
        }

    @staticmethod
    def _normalize_text(text: str | None) -> str:
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    @staticmethod
    def _keywords(text: str | None) -> list[str]:
        normalized = AIService._normalize_text(text)
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]{2,}", normalized)
        return [word for word in words if word not in AIService.STOP_WORDS]

    @staticmethod
    def _structure_score(answer: str) -> float:
        markers = [
            "because", "for example", "first", "second", "then", "however", "trade",
            "measure", "validate", "test", "monitor", "edge case", "in my project"
        ]
        hits = sum(1 for marker in markers if marker in answer)
        return min(hits / 3, 1.0)

    @staticmethod
    def _low_quality_answer_result(question: str, answer: str):
        normalized = AIService._normalize_text(answer)
        words = re.findall(r"[a-zA-Z0-9+#.]+", normalized)
        unique_words = set(words)

        low_quality_phrases = {
            "", "anything", "nothing", "no idea", "i don't know", "dont know", "idk",
            "good", "yes", "no", "asdf", "test", "skip"
        }

        repeated_chars = bool(re.fullmatch(r"(.)\1{4,}", normalized.replace(" ", "")))
        repeated_word_noise = len(words) >= 4 and len(unique_words) <= 2

        if normalized in low_quality_phrases or len(words) <= 2 or repeated_chars or repeated_word_noise:
            return {
                "score": 1,
                "accuracy": 1,
                "communication": 1,
                "confidence": 1,
                "completeness": 1,
                "feedback": "The answer does not meaningfully address the question. It is either empty, too short, or unrelated to the technical prompt.",
                "improvement_tips": "1. Give a direct technical answer. 2. Explain your reasoning in 4-6 sentences. 3. Include one concrete example or trade-off."
            }

        answer_keywords = set(AIService._keywords(answer))
        question_keywords = set(AIService._keywords(question))
        if len(words) < 8 and not (answer_keywords & question_keywords):
            return {
                "score": 2,
                "accuracy": 2,
                "communication": 2,
                "confidence": 2,
                "completeness": 1,
                "feedback": "The answer is too short and does not show enough relevance to the question.",
                "improvement_tips": "1. Reference the main topic in the question. 2. Add implementation details. 3. Describe trade-offs or validation."
            }

        return None

    @staticmethod
    def speech_to_text(audio_path: str):
        """
        Transcribe audio using OpenAI Whisper.
        """
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            print(f"Whisper Error: {e}")
            return None

    @staticmethod
    def text_to_speech(text: str):
        """
        Convert text to speech using OpenAI TTS.
        Returns audio bytes.
        """
        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            return response.content # bytes
        except Exception as e:
            print(f"TTS Error: {e}")
            return None

    @staticmethod
    def review_code(
        code: str,
        language: str,
        problem_description: str,
        test_results: list,
    ) -> dict:
        """
        AI Code Review: Evaluates code quality, complexity, readability.
        Uses OpenAI if key is set; falls back to deterministic heuristic scorer.
        Returns: {score, feedback, time_complexity, space_complexity, strengths, suggestions}
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_key_here":
            return AIService._review_code_heuristic(code, language, test_results)

        passed = sum(1 for r in test_results if r.get("passed", False))
        total = len(test_results)
        correctness_summary = f"{passed}/{total} test cases passed."

        prompt = f"""You are a senior software engineer conducting a code review for a technical interview.

Problem: {problem_description[:500]}
Language: {language}
Test Results: {correctness_summary}

Code to review:
```{language}
{code[:3000]}
```

Evaluate the code on:
1. Correctness & Edge Cases
2. Time Complexity
3. Space Complexity
4. Code Readability & Naming
5. Code Structure & Best Practices

Return ONLY a JSON object with these exact keys:
{{
  "score": <float 0-10>,
  "feedback": "<2-3 sentence overall assessment>",
  "time_complexity": "<e.g., O(n), O(n log n)>",
  "space_complexity": "<e.g., O(1), O(n)>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "suggestions": ["<suggestion 1>", "<suggestion 2>"]
}}"""

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=600,
            )
            AIService._log_usage("gpt-3.5-turbo", "code-review", response.usage)
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            return {
                "score": float(data.get("score", 5.0)),
                "feedback": data.get("feedback", ""),
                "time_complexity": data.get("time_complexity", "Unknown"),
                "space_complexity": data.get("space_complexity", "Unknown"),
                "strengths": data.get("strengths", []),
                "suggestions": data.get("suggestions", []),
            }
        except Exception as e:
            print(f"AI Code Review Error: {e}")
            return AIService._review_code_heuristic(code, language, test_results)

    @staticmethod
    def _review_code_heuristic(code: str, language: str, test_results: list) -> dict:
        """
        Deterministic heuristic code review — used as fallback when OpenAI is unavailable.
        Evaluates: line count, structure, naming, nested loops, comments, edge cases.
        """
        lines = [l for l in code.split("\n") if l.strip()]
        line_count = len(lines)
        code_lower = code.lower()

        # Correctness contribution
        passed = sum(1 for r in test_results if r.get("passed", False))
        total = max(len(test_results), 1)
        correctness_ratio = passed / total

        # Structure signals
        has_function = any(kw in code_lower for kw in ["def ", "function ", "void ", "int main", "public static"])
        has_comments = any(kw in code for kw in ["#", "//", "/*", '"""', "'''"])
        has_edge_case = any(kw in code_lower for kw in ["none", "null", "empty", "len(", ".length", "if not", "== 0", "== null"])
        has_early_return = any(kw in code_lower for kw in ["return none", "return null", "return -1", "return []", "return {}"])

        # Complexity estimation
        nested_loops = code_lower.count("for ") + code_lower.count("while ") >= 2
        has_recursion = any(
            word in code_lower for word in ["def solve", "def dfs", "def bfs", "self.", "function solve"]
        )
        uses_hashmap = any(kw in code_lower for kw in ["dict(", "{}", "hashmap", "map<", "unordered_map", "new hashmap"])
        uses_sort = "sort(" in code_lower or ".sort(" in code_lower

        # Naming quality
        has_meaningful_names = not any(
            bad in code_lower for bad in [" a = ", " b = ", " x = ", " y = ", " temp = "]
        )

        # Compute score components
        correctness_score = correctness_ratio * 4.0        # 0-4 pts
        structure_score = (has_function + has_comments + has_early_return) / 3.0 * 2.0  # 0-2 pts
        readability_score = (has_meaningful_names + (line_count > 5) + (line_count < 100)) / 3.0 * 2.0  # 0-2 pts
        edge_score = float(has_edge_case) * 1.0            # 0-1 pt
        elegance_score = (1 - int(nested_loops) * 0.5) * 1.0  # penalize O(n²)

        raw_score = correctness_score + structure_score + readability_score + edge_score + elegance_score
        score = round(max(1.0, min(10.0, raw_score)), 1)

        # Determine complexity estimates
        if nested_loops and not uses_hashmap:
            time_complexity = "O(n²)"
            space_complexity = "O(1)"
        elif uses_sort:
            time_complexity = "O(n log n)"
            space_complexity = "O(1) or O(n)"
        elif uses_hashmap:
            time_complexity = "O(n)"
            space_complexity = "O(n)"
        elif has_recursion:
            time_complexity = "O(n) or O(2ⁿ) depending on memoization"
            space_complexity = "O(n) call stack"
        else:
            time_complexity = "O(n)"
            space_complexity = "O(1)"

        # Build feedback
        strengths = []
        suggestions = []

        if correctness_ratio >= 1.0:
            strengths.append("All test cases pass — solution is correct.")
        elif correctness_ratio >= 0.5:
            strengths.append(f"Partial correctness ({passed}/{total} tests passing).")

        if has_function:
            strengths.append("Code is well-structured with proper function definitions.")
        if has_comments:
            strengths.append("Good use of comments to explain logic.")
        if has_edge_case:
            strengths.append("Edge case handling is present.")

        if not has_comments:
            suggestions.append("Add comments to explain the algorithm and key steps.")
        if nested_loops:
            suggestions.append("Consider optimizing nested loops — try using a HashMap to reduce to O(n).")
        if not has_edge_case:
            suggestions.append("Handle edge cases: empty input, single element, negative numbers.")
        if not has_meaningful_names:
            suggestions.append("Use descriptive variable names instead of single-letter names.")
        if line_count > 80:
            suggestions.append("Consider breaking the solution into smaller helper functions.")

        if score >= 8:
            feedback = f"Excellent solution with a quality score of {score}/10. The code is correct, readable, and efficiently handles edge cases."
        elif score >= 6:
            feedback = f"Good solution with a score of {score}/10. The approach is sound but could be improved in readability or efficiency."
        elif score >= 4:
            feedback = f"Partial solution scoring {score}/10. The logic has the right direction but misses some cases or could be optimized."
        else:
            feedback = f"The solution scores {score}/10 and needs significant improvement in correctness and code quality."

        return {
            "score": score,
            "feedback": feedback,
            "time_complexity": time_complexity,
            "space_complexity": space_complexity,
            "strengths": strengths[:3],
            "suggestions": suggestions[:3],
        }

    @staticmethod
    def _adapt_coding_difficulty(user_id: int, current_difficulty: str, db) -> str:
        """
        Adapt coding difficulty based on user's recent coding submissions.
        If recent avg correctness > 80% and AI score > 7 → increase difficulty.
        If recent avg correctness < 40% → decrease difficulty.
        """
        from app.models.coding_challenge import CodingSubmission
        import random

        recent = db.query(CodingSubmission).filter(
            CodingSubmission.user_id == user_id,
            CodingSubmission.is_final == True,
        ).order_by(CodingSubmission.created_at.desc()).limit(5).all()

        if len(recent) < 2:
            return current_difficulty

        avg_correctness = sum(s.correctness_score or 0 for s in recent) / len(recent)
        avg_ai_score = sum(s.ai_score or 5.0 for s in recent) / len(recent)

        levels = ["Easy", "Medium", "Hard"]
        current_idx = levels.index(current_difficulty) if current_difficulty in levels else 1

        if avg_correctness >= 80 and avg_ai_score >= 7:
            # Performing well → increase difficulty
            new_idx = min(current_idx + 1, 2)
            return levels[new_idx]
        elif avg_correctness < 40:
            # Struggling → decrease difficulty
            new_idx = max(current_idx - 1, 0)
            return levels[new_idx]

        return current_difficulty

    @staticmethod
    def select_coding_challenge(role: str, difficulty: str, db, user_id: int = None) -> object:
        """
        Select an appropriate coding challenge from DB based on role and difficulty.
        Adapts based on user's recent performance if user_id provided.
        Falls back to any challenge if no exact match found.
        """
        from app.models.coding_challenge import CodingChallenge

        # Adapt difficulty based on recent performance
        if user_id:
            difficulty = AIService._adapt_coding_difficulty(user_id, difficulty, db)

        # Try exact match on difficulty and role tag
        challenges = db.query(CodingChallenge).filter(
            CodingChallenge.difficulty == difficulty
        ).all()

        # Filter by role tag if possible
        role_lower = role.lower()
        matched = [
            c for c in challenges
            if c.role_tags and any(r.lower() in role_lower or role_lower in r.lower() for r in (c.role_tags or []))
        ]

        if matched:
            import random
            return random.choice(matched)

        # Fall back to difficulty match only
        if challenges:
            import random
            return random.choice(challenges)

        # Fall back to any challenge
        any_challenge = db.query(CodingChallenge).first()
        return any_challenge
