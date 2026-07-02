"""
Coding Interview Module — Production Router
Full session management, multi-language execution, AI code review, submission history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import os
import json

from app.database import get_db
from app.auth.utils import get_current_user
from app.models.user import User
from app.models.coding_challenge import CodingChallenge, CodingSubmission, CodingSession
from app.models.interview_session import InterviewSession
from app.schemas.coding import (
    CodingChallengeResponse, CodingSessionCreate, CodingSessionResponse,
    CodingRunCreate, CodingRunResponse,
    CodingSubmissionCreate, CodingSubmissionResponse,
    SubmissionHistoryResponse, SubmissionHistoryItem, TestCaseResult,
)
from app.services.code_executor import CodeExecutor
from app.services.ai_service import AIService
from app.core.rate_limit import limiter

router = APIRouter(prefix="/coding", tags=["coding"])

MAX_CODE_SIZE = 50_000  # 50KB limit

# Simple in-memory cache for challenge list
_challenge_cache = {"data": None, "ts": 0}
_CHALLENGE_CACHE_TTL = 300  # 5 minutes


# ─── Seed Data ────────────────────────────────────────────────────────────────

SEED_CHALLENGES = [
    {
        "title": "Two Sum",
        "description": (
            "Given an array of integers `nums` and an integer `target`, return the **indices** "
            "of the two numbers such that they add up to `target`.\n\n"
            "You may assume that each input would have **exactly one solution**, and you may not "
            "use the same element twice.\n\nReturn the answer in **sorted order** (smaller index first)."
        ),
        "difficulty": "Easy",
        "topics": ["Arrays", "Hash Map"],
        "role_tags": ["SDE", "Backend", "Frontend", "Full Stack"],
        "constraints": (
            "2 ≤ nums.length ≤ 10⁴\n"
            "-10⁹ ≤ nums[i] ≤ 10⁹\n"
            "-10⁹ ≤ target ≤ 10⁹\n"
            "Only one valid answer exists."
        ),
        "examples": [
            {"input": "nums = [2,7,11,15], target = 9", "output": "0 1", "explanation": "nums[0] + nums[1] = 2 + 7 = 9"},
            {"input": "nums = [3,2,4], target = 6", "output": "1 2", "explanation": "nums[1] + nums[2] = 2 + 4 = 6"},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "# Read input: first line = space-separated nums, second line = target\n"
                "nums = list(map(int, input().split()))\n"
                "target = int(input())\n\n"
                "def two_sum(nums, target):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "result = two_sum(nums, target)\n"
                "print(*result)"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int[] twoSum(int[] nums, int target) {\n"
                "        // Your solution here\n"
                "        return new int[]{};\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String[] parts = sc.nextLine().trim().split(\" \");\n"
                "        int[] nums = Arrays.stream(parts).mapToInt(Integer::parseInt).toArray();\n"
                "        int target = Integer.parseInt(sc.nextLine().trim());\n"
                "        int[] result = twoSum(nums, target);\n"
                "        System.out.println(result[0] + \" \" + result[1]);\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "vector<int> twoSum(vector<int>& nums, int target) {\n"
                "    // Your solution here\n"
                "    return {};\n"
                "}\n\n"
                "int main() {\n"
                "    vector<int> nums;\n"
                "    string line; getline(cin, line);\n"
                "    istringstream iss(line);\n"
                "    int x; while(iss >> x) nums.push_back(x);\n"
                "    int target; cin >> target;\n"
                "    auto result = twoSum(nums, target);\n"
                "    cout << result[0] << \" \" << result[1] << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const lines = require('fs').readFileSync(0,'utf8').trim().split('\\n');\n"
                "const nums = lines[0].split(' ').map(Number);\n"
                "const target = Number(lines[1]);\n\n"
                "function twoSum(nums, target) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "const result = twoSum(nums, target);\n"
                "console.log(result.join(' '));"
            ),
            "typescript": (
                "// Read input: first line = space-separated nums, second line = target\n"
                "const lines = require('fs').readFileSync(0, 'utf8').trim().split('\\n');\n"
                "const nums: number[] = lines[0].split(' ').map(Number);\n"
                "const target: number = Number(lines[1]);\n\n"
                "function twoSum(nums: number[], target: number): number[] {\n"
                "    // Your solution here (TypeScript typed)\n"
                "    return [];\n"
                "}\n\n"
                "const result = twoSum(nums, target);\n"
                "console.log(result.join(' '));"
            ),
        },
        "test_cases": [
            {"input": "2 7 11 15\n9", "expected": "0 1"},
            {"input": "3 2 4\n6", "expected": "1 2"},
        ],
        "hidden_test_cases": [
            {"input": "3 3\n6", "expected": "0 1"},
            {"input": "-1 -2 -3 -4 -5\n-8", "expected": "2 4"},
            {"input": "1000000000 999999999\n1999999999", "expected": "0 1"},
        ],
    },
    {
        "title": "Valid Parentheses",
        "description": (
            "Given a string `s` containing just the characters `(`, `)`, `{`, `}`, `[`, and `]`, "
            "determine if the input string is valid.\n\n"
            "An input string is valid if:\n"
            "1. Open brackets must be closed by the same type of brackets.\n"
            "2. Open brackets must be closed in the correct order.\n"
            "3. Every close bracket has a corresponding open bracket of the same type."
        ),
        "difficulty": "Easy",
        "topics": ["Stack", "String"],
        "role_tags": ["SDE", "Backend", "Frontend"],
        "constraints": "1 ≤ s.length ≤ 10⁴\ns consists of parentheses only '()[]{}'",
        "examples": [
            {"input": "s = \"()\"", "output": "true", "explanation": "Matched single pair."},
            {"input": "s = \"()[]{}\"", "output": "true", "explanation": "All pairs matched."},
            {"input": "s = \"(]\"", "output": "false", "explanation": "Wrong closing bracket."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "s = input().strip()\n\n"
                "def is_valid(s):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print('true' if is_valid(s) else 'false')"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static boolean isValid(String s) {\n"
                "        // Your solution here\n"
                "        return false;\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String s = sc.nextLine().trim();\n"
                "        System.out.println(isValid(s) ? \"true\" : \"false\");\n"
                "    }\n"
                "}"
            ),
            "typescript": (
                "// Read input: string to validate\n"
                "const s = require('fs').readFileSync(0,'utf8').trim();\n\n"
                "function isValid(s: string): boolean {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(isValid(s) ? 'true' : 'false');"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "bool isValid(string s) {\n"
                "    // Your solution here\n"
                "    return false;\n"
                "}\n\n"
                "int main() {\n"
                "    string s; getline(cin, s);\n"
                "    cout << (isValid(s) ? \"true\" : \"false\") << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const s = require('fs').readFileSync(0,'utf8').trim();\n\n"
                "function isValid(s) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(isValid(s) ? 'true' : 'false');"
            ),
        },
        "test_cases": [
            {"input": "()", "expected": "true"},
            {"input": "()[]{}", "expected": "true"},
            {"input": "(]", "expected": "false"},
        ],
        "hidden_test_cases": [
            {"input": "([)]", "expected": "false"},
            {"input": "{[]}", "expected": "true"},
            {"input": "", "expected": "true"},
        ],
    },
    {
        "title": "Maximum Subarray",
        "description": (
            "Given an integer array `nums`, find the **subarray** with the largest sum, and return its sum.\n\n"
            "A **subarray** is a contiguous part of an array."
        ),
        "difficulty": "Medium",
        "topics": ["Dynamic Programming", "Arrays", "Divide and Conquer"],
        "role_tags": ["SDE", "Backend", "Data Engineer"],
        "constraints": "1 ≤ nums.length ≤ 10⁵\n-10⁴ ≤ nums[i] ≤ 10⁴",
        "examples": [
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "explanation": "Subarray [4,-1,2,1] has the largest sum = 6."},
            {"input": "nums = [1]", "output": "1", "explanation": "Single element."},
            {"input": "nums = [5,4,-1,7,8]", "output": "23", "explanation": "Entire array."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "nums = list(map(int, input().split()))\n\n"
                "def max_subarray(nums):\n"
                "    # Your solution here (Kadane's Algorithm)\n"
                "    pass\n\n"
                "print(max_subarray(nums))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int maxSubArray(int[] nums) {\n"
                "        // Your solution here\n"
                "        return 0;\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n"
                "        System.out.println(maxSubArray(nums));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "int maxSubArray(vector<int>& nums) {\n"
                "    // Your solution here\n"
                "    return 0;\n"
                "}\n\n"
                "int main() {\n"
                "    vector<int> nums;\n"
                "    string line; getline(cin, line);\n"
                "    istringstream iss(line);\n"
                "    int x; while(iss >> x) nums.push_back(x);\n"
                "    cout << maxSubArray(nums) << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const nums = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n\n"
                "function maxSubArray(nums) {\n"
                "    // Your solution here (Kadane's Algorithm)\n"
                "}\n\n"
                "console.log(maxSubArray(nums));"
            ),
        },
        "test_cases": [
            {"input": "-2 1 -3 4 -1 2 1 -5 4", "expected": "6"},
            {"input": "1", "expected": "1"},
        ],
        "hidden_test_cases": [
            {"input": "5 4 -1 7 8", "expected": "23"},
            {"input": "-1 -2 -3 -4", "expected": "-1"},
            {"input": "1 2 3 4 5", "expected": "15"},
        ],
    },
    {
        "title": "Climbing Stairs",
        "description": (
            "You are climbing a staircase. It takes `n` steps to reach the top.\n\n"
            "Each time you can either climb **1** or **2** steps. "
            "In how many **distinct ways** can you climb to the top?"
        ),
        "difficulty": "Easy",
        "topics": ["Dynamic Programming", "Math"],
        "role_tags": ["SDE", "Frontend", "Backend"],
        "constraints": "1 ≤ n ≤ 45",
        "examples": [
            {"input": "n = 2", "output": "2", "explanation": "1+1 or 2"},
            {"input": "n = 3", "output": "3", "explanation": "1+1+1, 1+2, or 2+1"},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "n = int(input())\n\n"
                "def climb_stairs(n):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print(climb_stairs(n))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int climbStairs(int n) {\n"
                "        // Your solution here\n"
                "        return 0;\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int n = sc.nextInt();\n"
                "        System.out.println(climbStairs(n));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "int climbStairs(int n) {\n"
                "    // Your solution here\n"
                "    return 0;\n"
                "}\n\n"
                "int main() {\n"
                "    int n; cin >> n;\n"
                "    cout << climbStairs(n) << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const n = parseInt(require('fs').readFileSync(0,'utf8').trim());\n\n"
                "function climbStairs(n) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(climbStairs(n));"
            ),
        },
        "test_cases": [
            {"input": "2", "expected": "2"},
            {"input": "3", "expected": "3"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected": "1"},
            {"input": "10", "expected": "89"},
            {"input": "45", "expected": "1836311903"},
        ],
    },
    {
        "title": "Merge Intervals",
        "description": (
            "Given an array of `intervals` where `intervals[i] = [start_i, end_i]`, "
            "merge all overlapping intervals, and return an array of the non-overlapping intervals "
            "that cover all the intervals in the input.\n\n"
            "Input format: Each line is `start end` for one interval. "
            "Output format: Each merged interval on its own line as `start end`."
        ),
        "difficulty": "Medium",
        "topics": ["Arrays", "Sorting"],
        "role_tags": ["SDE", "Backend", "Data Engineer"],
        "constraints": "1 ≤ intervals.length ≤ 10⁴\nintervals[i].length == 2\n0 ≤ start_i ≤ end_i ≤ 10⁴",
        "examples": [
            {"input": "1 3\n2 6\n8 10\n15 18", "output": "1 6\n8 10\n15 18", "explanation": "[1,3] and [2,6] overlap → [1,6]."},
            {"input": "1 4\n4 5", "output": "1 5", "explanation": "Touching intervals merge."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "import sys\n"
                "lines = sys.stdin.read().strip().split('\\n')\n"
                "intervals = [list(map(int, line.split())) for line in lines if line.strip()]\n\n"
                "def merge(intervals):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "result = merge(intervals)\n"
                "for interval in result:\n"
                "    print(interval[0], interval[1])"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int[][] merge(int[][] intervals) {\n"
                "        // Your solution here\n"
                "        return new int[][]{};\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        List<int[]> list = new ArrayList<>();\n"
                "        while(sc.hasNextLine()) {\n"
                "            String line = sc.nextLine().trim();\n"
                "            if(line.isEmpty()) break;\n"
                "            String[] parts = line.split(\" \");\n"
                "            list.add(new int[]{Integer.parseInt(parts[0]), Integer.parseInt(parts[1])});\n"
                "        }\n"
                "        int[][] intervals = list.toArray(new int[0][]);\n"
                "        int[][] result = merge(intervals);\n"
                "        for(int[] r : result) System.out.println(r[0] + \" \" + r[1]);\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "vector<vector<int>> merge(vector<vector<int>>& intervals) {\n"
                "    // Your solution here\n"
                "    return {};\n"
                "}\n\n"
                "int main() {\n"
                "    vector<vector<int>> intervals;\n"
                "    int a, b;\n"
                "    while(cin >> a >> b) intervals.push_back({a, b});\n"
                "    auto result = merge(intervals);\n"
                "    for(auto& r : result) cout << r[0] << \" \" << r[1] << '\\n';\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const lines = require('fs').readFileSync(0,'utf8').trim().split('\\n');\n"
                "const intervals = lines.filter(l => l.trim()).map(l => l.trim().split(' ').map(Number));\n\n"
                "function merge(intervals) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "const result = merge(intervals);\n"
                "result.forEach(r => console.log(r[0] + ' ' + r[1]));"
            ),
        },
        "test_cases": [
            {"input": "1 3\n2 6\n8 10\n15 18", "expected": "1 6\n8 10\n15 18"},
            {"input": "1 4\n4 5", "expected": "1 5"},
        ],
        "hidden_test_cases": [
            {"input": "1 4\n2 3", "expected": "1 4"},
            {"input": "1 2\n3 4\n5 6", "expected": "1 2\n3 4\n5 6"},
            {"input": "0 0", "expected": "0 0"},
        ],
    },
    # ─── 6. Reverse Linked List (Linked List) ──────────────────────────────────
    {
        "title": "Reverse Linked List",
        "description": (
            "Given the `head` of a singly linked list, reverse the list, and return the reversed list.\n\n"
            "Input format: First line = space-separated values of linked list nodes.\n"
            "Output format: Space-separated values of the reversed list."
        ),
        "difficulty": "Easy",
        "topics": ["Linked List"],
        "role_tags": ["SDE", "Backend", "Frontend"],
        "constraints": "1 ≤ number of nodes ≤ 5000\n-5000 ≤ Node.val ≤ 5000",
        "examples": [
            {"input": "1 2 3 4 5", "output": "5 4 3 2 1", "explanation": "Reversed the list."},
            {"input": "1 2", "output": "2 1", "explanation": "Two-node list reversed."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "vals = list(map(int, input().split()))\n\n"
                "class ListNode:\n"
                "    def __init__(self, val=0, next=None):\n"
                "        self.val = val\n"
                "        self.next = next\n"
                "    def to_list(self):\n"
                "        out = []\n"
                "        cur = self\n"
                "        while cur:\n"
                "            out.append(str(cur.val))\n"
                "            cur = cur.next\n"
                "        return ' '.join(out)\n\n"
                "def build_list(vals):\n"
                "    if not vals: return None\n"
                "    head = ListNode(vals[0])\n"
                "    cur = head\n"
                "    for v in vals[1:]:\n"
                "        cur.next = ListNode(v)\n"
                "        cur = cur.next\n"
                "    return head\n\n"
                "def reverse_list(head):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "head = build_list(vals)\n"
                "result = reverse_list(head)\n"
                "print(result.to_list() if result else '')"
            ),
            "java": (
                "import java.util.*;\n\n"
                "class ListNode {\n"
                "    int val;\n"
                "    ListNode next;\n"
                "    ListNode(int val) { this.val = val; }\n"
                "}\n\n"
                "public class Solution {\n"
                "    public static ListNode reverseList(ListNode head) {\n"
                "        // Your solution here\n"
                "        return null;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String[] parts = sc.nextLine().trim().split(\" \");\n"
                "        ListNode dummy = new ListNode(0);\n"
                "        ListNode cur = dummy;\n"
                "        for (String p : parts) { cur.next = new ListNode(Integer.parseInt(p)); cur = cur.next; }\n"
                "        ListNode result = reverseList(dummy.next);\n"
                "        List<String> out = new ArrayList<>();\n"
                "        while (result != null) { out.add(String.valueOf(result.val)); result = result.next; }\n"
                "        System.out.println(String.join(\" \", out));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n"
                "struct ListNode { int val; ListNode* next; ListNode(int v) : val(v), next(nullptr) {} };\n\n"
                "ListNode* reverseList(ListNode* head) {\n"
                "    // Your solution here\n"
                "    return nullptr;\n"
                "}\n\n"
                "int main() {\n"
                "    string line; getline(cin, line);\n"
                "    istringstream iss(line);\n"
                "    ListNode dummy(0); ListNode* cur = &dummy;\n"
                "    int x; while (iss >> x) { cur->next = new ListNode(x); cur = cur->next; }\n"
                "    ListNode* result = reverseList(dummy.next);\n"
                "    while (result) { cout << result->val; if (result->next) cout << ' '; result = result->next; }\n"
                "    cout << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const vals = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n"
                "class ListNode { constructor(val, next) { this.val = val; this.next = next || null; } }\n"
                "function buildList(arr) {\n"
                "    if (!arr.length) return null;\n"
                "    let head = new ListNode(arr[0]);\n"
                "    let cur = head;\n"
                "    for (let i = 1; i < arr.length; i++) { cur.next = new ListNode(arr[i]); cur = cur.next; }\n"
                "    return head;\n"
                "}\n"
                "function reverseList(head) {\n"
                "    // Your solution here\n"
                "}\n"
                "const result = reverseList(buildList(vals));\n"
                "const out = [];\n"
                "let cur = result;\n"
                "while (cur) { out.push(cur.val); cur = cur.next; }\n"
                "console.log(out.join(' '));"
            ),
            "typescript": (
                "// Read input: space-separated node values\n"
                "const vals = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n\n"
                "class ListNode {\n"
                "    val: number;\n"
                "    next: ListNode | null;\n"
                "    constructor(val: number, next: ListNode | null = null) {\n"
                "        this.val = val;\n"
                "        this.next = next;\n"
                "    }\n"
                "}\n\n"
                "function buildList(arr: number[]): ListNode | null {\n"
                "    if (!arr.length) return null;\n"
                "    const head = new ListNode(arr[0]);\n"
                "    let cur = head;\n"
                "    for (let i = 1; i < arr.length; i++) {\n"
                "        cur.next = new ListNode(arr[i]);\n"
                "        cur = cur.next;\n"
                "    }\n"
                "    return head;\n"
                "}\n\n"
                "function reverseList(head: ListNode | null): ListNode | null {\n"
                "    // Your solution here (TypeScript typed)\n"
                "    return null;\n"
                "}\n\n"
                "const result = reverseList(buildList(vals));\n"
                "const out: number[] = [];\n"
                "let cur = result;\n"
                "while (cur) { out.push(cur.val); cur = cur.next; }\n"
                "console.log(out.join(' '));"
            ),
        },
        "test_cases": [
            {"input": "1 2 3 4 5", "expected": "5 4 3 2 1"},
            {"input": "1 2", "expected": "2 1"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected": "1"},
            {"input": "", "expected": ""},
            {"input": "10 20 30 40", "expected": "40 30 20 10"},
        ],
    },
    # ─── 7. Invert Binary Tree (Tree) ─────────────────────────────────────────
    {
        "title": "Invert Binary Tree",
        "description": (
            "Given the `root` of a binary tree, invert the tree, and return its root.\n\n"
            "Inverting a binary tree means swapping the left and right children of every node.\n\n"
            "Input format: Level-order traversal of the tree (use -1 for null nodes).\n"
            "Output format: Level-order traversal of the inverted tree."
        ),
        "difficulty": "Easy",
        "topics": ["Tree", "BFS", "Recursion"],
        "role_tags": ["SDE", "Backend", "Frontend"],
        "constraints": "1 ≤ number of nodes ≤ 100\n-100 ≤ Node.val ≤ 100",
        "examples": [
            {"input": "4 2 7 1 3 6 9", "output": "4 7 2 9 6 3 1", "explanation": "Swapped left and right of every node."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "from collections import deque\n"
                "vals = list(map(int, input().split()))\n\n"
                "class TreeNode:\n"
                "    def __init__(self, val=0, left=None, right=None):\n"
                "        self.val = val\n"
                "        self.left = left\n"
                "        self.right = right\n\n"
                "def build_tree(vals):\n"
                "    if not vals: return None\n"
                "    root = TreeNode(vals[0])\n"
                "    q = deque([root])\n"
                "    i = 1\n"
                "    while q and i < len(vals):\n"
                "        node = q.popleft()\n"
                "        if i < len(vals) and vals[i] != -1:\n"
                "            node.left = TreeNode(vals[i])\n"
                "            q.append(node.left)\n"
                "        i += 1\n"
                "        if i < len(vals) and vals[i] != -1:\n"
                "            node.right = TreeNode(vals[i])\n"
                "            q.append(node.right)\n"
                "        i += 1\n"
                "    return root\n\n"
                "def level_order(root):\n"
                "    if not root: return []\n"
                "    q = deque([root])\n"
                "    out = []\n"
                "    while q:\n"
                "        node = q.popleft()\n"
                "        if node:\n"
                "            out.append(str(node.val))\n"
                "            q.append(node.left)\n"
                "            q.append(node.right)\n"
                "        else:\n"
                "            out.append('-1')\n"
                "    while out and out[-1] == '-1': out.pop()\n"
                "    return ' '.join(out)\n\n"
                "def invert_tree(root):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "root = build_tree(vals)\n"
                "result = invert_tree(root)\n"
                "print(level_order(result))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "class TreeNode {\n"
                "    int val; TreeNode left, right;\n"
                "    TreeNode(int v) { val = v; }\n"
                "}\n\n"
                "public class Solution {\n"
                "    public static TreeNode invertTree(TreeNode root) {\n"
                "        // Your solution here\n"
                "        return null;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String[] parts = sc.nextLine().trim().split(\" \");\n"
                "        int[] vals = Arrays.stream(parts).mapToInt(Integer::parseInt).toArray();\n"
                "        if (vals.length == 0) return;\n"
                "        TreeNode root = new TreeNode(vals[0]);\n"
                "        Queue<TreeNode> q = new LinkedList<>();\n"
                "        q.add(root); int i = 1;\n"
                "        while (!q.isEmpty() && i < vals.length) {\n"
                "            TreeNode node = q.poll();\n"
                "            if (i < vals.length && vals[i] != -1) { node.left = new TreeNode(vals[i]); q.add(node.left); } i++;\n"
                "            if (i < vals.length && vals[i] != -1) { node.right = new TreeNode(vals[i]); q.add(node.right); } i++;\n"
                "        }\n"
                "        TreeNode result = invertTree(root);\n"
                "        Queue<TreeNode> q2 = new LinkedList<>();\n"
                "        q2.add(result); List<String> out = new ArrayList<>();\n"
                "        while (!q2.isEmpty()) {\n"
                "            TreeNode n = q2.poll();\n"
                "            if (n != null) { out.add(String.valueOf(n.val)); q2.add(n.left); q2.add(n.right); }\n"
                "            else out.add(\"-1\");\n"
                "        }\n"
                "        while (!out.isEmpty() && out.get(out.size()-1).equals(\"-1\")) out.remove(out.size()-1);\n"
                "        System.out.println(String.join(\" \", out));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n"
                "struct TreeNode { int val; TreeNode *left, *right; TreeNode(int v) : val(v), left(nullptr), right(nullptr) {} };\n\n"
                "TreeNode* invertTree(TreeNode* root) {\n"
                "    // Your solution here\n"
                "    return nullptr;\n"
                "}\n\n"
                "int main() {\n"
                "    string line; getline(cin, line);\n"
                "    istringstream iss(line);\n"
                "    vector<int> vals; int x; while (iss >> x) vals.push_back(x);\n"
                "    if (vals.empty()) return 0;\n"
                "    TreeNode* root = new TreeNode(vals[0]);\n"
                "    queue<TreeNode*> q; q.push(root); int i = 1;\n"
                "    while (!q.empty() && i < (int)vals.size()) {\n"
                "        TreeNode* node = q.front(); q.pop();\n"
                "        if (i < (int)vals.size() && vals[i] != -1) { node->left = new TreeNode(vals[i]); q.push(node->left); } i++;\n"
                "        if (i < (int)vals.size() && vals[i] != -1) { node->right = new TreeNode(vals[i]); q.push(node->right); } i++;\n"
                "    }\n"
                "    TreeNode* result = invertTree(root);\n"
                "    queue<TreeNode*> q2; q2.push(result); vector<string> out;\n"
                "    while (!q2.empty()) {\n"
                "        TreeNode* n = q2.front(); q2.pop();\n"
                "        if (n) { out.push_back(to_string(n->val)); q2.push(n->left); q2.push(n->right); }\n"
                "        else out.push_back(\"-1\");\n"
                "    }\n"
                "    while (!out.empty() && out.back() == \"-1\") out.pop_back();\n"
                "    for (int i = 0; i < (int)out.size(); i++) { if (i) cout << ' '; cout << out[i]; }\n"
                "    cout << endl; return 0;\n"
                "}"
            ),
            "javascript": (
                "const vals = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n"
                "class TreeNode { constructor(val) { this.val = val; this.left = null; this.right = null; } }\n"
                "function buildTree(arr) {\n"
                "    if (!arr.length) return null;\n"
                "    let root = new TreeNode(arr[0]);\n"
                "    let q = [root]; let i = 1;\n"
                "    while (q.length && i < arr.length) {\n"
                "        let node = q.shift();\n"
                "        if (i < arr.length && arr[i] !== -1) { node.left = new TreeNode(arr[i]); q.push(node.left); } i++;\n"
                "        if (i < arr.length && arr[i] !== -1) { node.right = new TreeNode(arr[i]); q.push(node.right); } i++;\n"
                "    }\n"
                "    return root;\n"
                "}\n"
                "function invertTree(root) {\n"
                "    // Your solution here\n"
                "}\n"
                "const result = invertTree(buildTree(vals));\n"
                "const out = []; let q = [result];\n"
                "while (q.length) {\n"
                "    let n = q.shift();\n"
                "    if (n) { out.push(n.val); q.push(n.left); q.push(n.right); }\n"
                "    else out.push(-1);\n"
                "}\n"
                "while (out.length && out[out.length-1] === -1) out.pop();\n"
                "console.log(out.join(' '));"
            ),
        },
        "test_cases": [
            {"input": "4 2 7 1 3 6 9", "output": "4 7 2 9 6 3 1"},
        ],
        "hidden_test_cases": [
            {"input": "2 1 3", "output": "2 3 1"},
            {"input": "1", "output": "1"},
            {"input": "1 2 -1 3", "output": "1 -1 2 -1 -1 3"},
        ],
    },
    # ─── 8. Number of Islands (Graph) ─────────────────────────────────────────
    {
        "title": "Number of Islands",
        "description": (
            "Given an `m x n` 2D binary grid `grid` which represents a map of '1's (land) and '0's (water), "
            "return the number of islands.\n\n"
            "An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.\n\n"
            "Input format: Each line is a row of the grid (space-separated 0s and 1s).\n"
            "Output format: Single integer — the number of islands."
        ),
        "difficulty": "Medium",
        "topics": ["Graph", "DFS", "BFS", "Matrix"],
        "role_tags": ["SDE", "Backend", "Data Engineer", "ML Engineer"],
        "constraints": "m, n ≤ 300\ngrid[i][j] is '0' or '1'",
        "examples": [
            {"input": "1 1 1 1 0\n1 1 0 1 0\n1 1 0 0 0\n0 0 0 0 0", "output": "1", "explanation": "One large island."},
            {"input": "1 1 0 0 0\n1 1 0 0 0\n0 0 1 0 0\n0 0 0 1 1", "output": "3", "explanation": "Three separate islands."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "import sys\n"
                "lines = sys.stdin.read().strip().split('\\n')\n"
                "grid = [list(map(int, line.split())) for line in lines if line.strip()]\n\n"
                "def num_islands(grid):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print(num_islands(grid))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int numIslands(int[][] grid) {\n"
                "        // Your solution here\n"
                "        return 0;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        List<int[]> rows = new ArrayList<>();\n"
                "        while (sc.hasNextLine()) {\n"
                "            String line = sc.nextLine().trim();\n"
                "            if (line.isEmpty()) break;\n"
                "            rows.add(Arrays.stream(line.split(\" \")).mapToInt(Integer::parseInt).toArray());\n"
                "        }\n"
                "        int[][] grid = rows.toArray(new int[0][]);\n"
                "        System.out.println(numIslands(grid));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "int numIslands(vector<vector<int>>& grid) {\n"
                "    // Your solution here\n"
                "    return 0;\n"
                "}\n\n"
                "int main() {\n"
                "    vector<vector<int>> grid;\n"
                "    string line;\n"
                "    while (getline(cin, line) && !line.empty()) {\n"
                "        vector<int> row; istringstream iss(line); int x;\n"
                "        while (iss >> x) row.push_back(x);\n"
                "        grid.push_back(row);\n"
                "    }\n"
                "    cout << numIslands(grid) << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const lines = require('fs').readFileSync(0,'utf8').trim().split('\\n');\n"
                "const grid = lines.filter(l => l.trim()).map(l => l.trim().split(' ').map(Number));\n\n"
                "function numIslands(grid) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(numIslands(grid));"
            ),
        },
        "test_cases": [
            {"input": "1 1 1 1 0\n1 1 0 1 0\n1 1 0 0 0\n0 0 0 0 0", "expected": "1"},
            {"input": "1 1 0 0 0\n1 1 0 0 0\n0 0 1 0 0\n0 0 0 1 1", "expected": "3"},
        ],
        "hidden_test_cases": [
            {"input": "1 0 1 0 1", "expected": "3"},
            {"input": "1 1\n1 1", "expected": "1"},
            {"input": "0 0\n0 0", "expected": "0"},
        ],
    },
    # ─── 9. Best Time to Buy and Sell Stock (Greedy) ──────────────────────────
    {
        "title": "Best Time to Buy and Sell Stock",
        "description": (
            "You are given an array `prices` where `prices[i]` is the price of a given stock on the ith day.\n\n"
            "You want to maximize your profit by choosing a single day to buy one stock and choosing a "
            "different day in the future to sell that stock.\n\n"
            "Return the maximum profit you can achieve. If no profit is possible, return 0."
        ),
        "difficulty": "Easy",
        "topics": ["Greedy", "Arrays", "Dynamic Programming"],
        "role_tags": ["SDE", "Backend", "Frontend", "Data Engineer"],
        "constraints": "1 ≤ prices.length ≤ 10⁵\n0 ≤ prices[i] ≤ 10⁴",
        "examples": [
            {"input": "7 1 5 3 6 4", "output": "5", "explanation": "Buy on day 2 (price=1), sell on day 5 (price=6), profit=5."},
            {"input": "7 6 4 3 1", "output": "0", "explanation": "No profit possible."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "prices = list(map(int, input().split()))\n\n"
                "def max_profit(prices):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print(max_profit(prices))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int maxProfit(int[] prices) {\n"
                "        // Your solution here\n"
                "        return 0;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int[] prices = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n"
                "        System.out.println(maxProfit(prices));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "int maxProfit(vector<int>& prices) {\n"
                "    // Your solution here\n"
                "    return 0;\n"
                "}\n\n"
                "int main() {\n"
                "    vector<int> prices; int x; string line; getline(cin, line);\n"
                "    istringstream iss(line); while (iss >> x) prices.push_back(x);\n"
                "    cout << maxProfit(prices) << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const prices = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n\n"
                "function maxProfit(prices) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(maxProfit(prices));"
            ),
        },
        "test_cases": [
            {"input": "7 1 5 3 6 4", "expected": "5"},
            {"input": "7 6 4 3 1", "expected": "0"},
        ],
        "hidden_test_cases": [
            {"input": "2 4 1", "expected": "2"},
            {"input": "1", "expected": "0"},
            {"input": "3 3 5 0 0 3 1 4", "expected": "4"},
        ],
    },
    # ─── 10. Subsets (Backtracking) ───────────────────────────────────────────
    {
        "title": "Subsets",
        "description": (
            "Given an integer array `nums` of unique elements, return all possible subsets (the power set).\n\n"
            "The solution set must not contain duplicate subsets. Return the solution in any order.\n\n"
            "Input format: Space-separated integers.\n"
            "Output format: Each subset on its own line, space-separated."
        ),
        "difficulty": "Medium",
        "topics": ["Backtracking", "Recursion", "Bit Manipulation"],
        "role_tags": ["SDE", "Backend", "ML Engineer"],
        "constraints": "1 ≤ nums.length ≤ 10\n-10 ≤ nums[i] ≤ 10\nAll elements are unique",
        "examples": [
            {"input": "1 2 3", "output": "\n1\n2\n3\n1 2\n1 3\n2 3\n1 2 3", "explanation": "All 8 subsets."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "nums = list(map(int, input().split()))\n\n"
                "def subsets(nums):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "result = subsets(nums)\n"
                "result.sort(key=lambda x: (len(x), x))\n"
                "for s in result:\n"
                "    print(*s if s else [''])"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static List<List<Integer>> subsets(int[] nums) {\n"
                "        // Your solution here\n"
                "        return new ArrayList<>();\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n"
                "        List<List<Integer>> result = subsets(nums);\n"
                "        result.sort(Comparator.comparingInt(List::size));\n"
                "        for (List<Integer> s : result) {\n"
                "            if (s.isEmpty()) System.out.println();\n"
                "            else System.out.println(s.stream().map(String::valueOf).reduce((a,b) -> a+\" \"+b).get());\n"
                "        }\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "vector<vector<int>> subsets(vector<int>& nums) {\n"
                "    // Your solution here\n"
                "    return {};\n"
                "}\n\n"
                "int main() {\n"
                "    vector<int> nums; int x; string line; getline(cin, line);\n"
                "    istringstream iss(line); while (iss >> x) nums.push_back(x);\n"
                "    auto result = subsets(nums);\n"
                "    sort(result.begin(), result.end(), [](auto& a, auto& b) { return a.size() < b.size() || (a.size() == b.size() && a < b); });\n"
                "    for (auto& s : result) {\n"
                "        for (int i = 0; i < (int)s.size(); i++) { if (i) cout << ' '; cout << s[i]; }\n"
                "        cout << '\\n';\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const nums = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n\n"
                "function subsets(nums) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "const result = subsets(nums);\n"
                "result.sort((a,b) => a.length - b.length || a[0] - b[0]);\n"
                "result.forEach(s => console.log(s.join(' ') || ''));"
            ),
        },
        "test_cases": [
            {"input": "1 2 3", "expected": "\n1\n2\n3\n1 2\n1 3\n2 3\n1 2 3"},
        ],
        "hidden_test_cases": [
            {"input": "0", "expected": "\n0"},
            {"input": "1 2", "expected": "\n1\n2\n1 2"},
        ],
    },
    # ─── 11. LRU Cache (Design/HashMap) ───────────────────────────────────────
    {
        "title": "LRU Cache",
        "description": (
            "Design a data structure that follows the constraints of a Least Recently Used (LRU) cache.\n\n"
            "Implement the `LRUCache` class:\n"
            "- `LRUCache(capacity)` — Initialize the LRU cache with positive size capacity.\n"
            "- `get(key)` — Return the value of the key if the key exists, otherwise return -1.\n"
            "- `put(key, value)` — Update the value of the key if it exists. Otherwise, add the key-value pair.\n"
            "  If the number of keys exceeds the capacity, evict the least recently used key.\n\n"
            "Input format: First line = capacity. Subsequent lines = operations: GET key or PUT key value.\n"
            "Output format: Result of each GET operation, one per line."
        ),
        "difficulty": "Medium",
        "topics": ["HashMap", "Design", "Linked List"],
        "role_tags": ["SDE", "Backend", "System Design"],
        "constraints": "1 ≤ capacity ≤ 3000\n0 ≤ key ≤ 10⁴\n0 ≤ value ≤ 10⁵\nAt most 2×10⁵ calls to get and put",
        "examples": [
            {"input": "2\nPUT 1 1\nPUT 2 2\nGET 1\nPUT 3 3\nGET 2", "output": "1\n-1", "explanation": "GET 1 returns 1. PUT 3 evicts key 2. GET 2 returns -1."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "from collections import OrderedDict\n"
                "import sys\n"
                "lines = sys.stdin.read().strip().split('\\n')\n"
                "capacity = int(lines[0])\n\n"
                "class LRUCache:\n"
                "    def __init__(self, capacity):\n"
                "        # Your solution here\n"
                "        pass\n\n"
                "    def get(self, key):\n"
                "        # Your solution here\n"
                "        pass\n\n"
                "    def put(self, key, value):\n"
                "        # Your solution here\n"
                "        pass\n\n"
                "cache = LRUCache(capacity)\n"
                "for line in lines[1:]:\n"
                "    parts = line.split()\n"
                "    if parts[0] == 'GET':\n"
                "        print(cache.get(int(parts[1])))\n"
                "    elif parts[0] == 'PUT':\n"
                "        cache.put(int(parts[1]), int(parts[2]))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    static class LRUCache {\n"
                "        public LRUCache(int capacity) {\n"
                "            // Your solution here\n"
                "        }\n"
                "        public int get(int key) {\n"
                "            // Your solution here\n"
                "            return -1;\n"
                "        }\n"
                "        public void put(int key, int value) {\n"
                "            // Your solution here\n"
                "        }\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int capacity = Integer.parseInt(sc.nextLine().trim());\n"
                "        LRUCache cache = new LRUCache(capacity);\n"
                "        while (sc.hasNextLine()) {\n"
                "            String line = sc.nextLine().trim();\n"
                "            if (line.isEmpty()) break;\n"
                "            String[] parts = line.split(\" \");\n"
                "            if (parts[0].equals(\"GET\")) System.out.println(cache.get(Integer.parseInt(parts[1])));\n"
                "            else if (parts[0].equals(\"PUT\")) cache.put(Integer.parseInt(parts[1]), Integer.parseInt(parts[2]));\n"
                "        }\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "class LRUCache {\n"
                "public:\n"
                "    LRUCache(int capacity) {\n"
                "        // Your solution here\n"
                "    }\n"
                "    int get(int key) {\n"
                "        // Your solution here\n"
                "        return -1;\n"
                "    }\n"
                "    void put(int key, int value) {\n"
                "        // Your solution here\n"
                "    }\n"
                "};\n\n"
                "int main() {\n"
                "    int capacity; cin >> capacity; cin.ignore();\n"
                "    LRUCache cache(capacity);\n"
                "    string line;\n"
                "    while (getline(cin, line) && !line.empty()) {\n"
                "        istringstream iss(line);\n"
                "        string op; iss >> op;\n"
                "        if (op == \"GET\") { int k; iss >> k; cout << cache.get(k) << '\\n'; }\n"
                "        else if (op == \"PUT\") { int k, v; iss >> k >> v; cache.put(k, v); }\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const lines = require('fs').readFileSync(0,'utf8').trim().split('\\n');\n"
                "const capacity = parseInt(lines[0]);\n\n"
                "class LRUCache {\n"
                "    constructor(capacity) {\n"
                "        // Your solution here\n"
                "    }\n"
                "    get(key) {\n"
                "        // Your solution here\n"
                "    }\n"
                "    put(key, value) {\n"
                "        // Your solution here\n"
                "    }\n"
                "}\n\n"
                "const cache = new LRUCache(capacity);\n"
                "for (let i = 1; i < lines.length; i++) {\n"
                "    const parts = lines[i].split(' ');\n"
                "    if (parts[0] === 'GET') console.log(cache.get(parseInt(parts[1])));\n"
                "    else if (parts[0] === 'PUT') cache.put(parseInt(parts[1]), parseInt(parts[2]));\n"
                "}"
            ),
        },
        "test_cases": [
            {"input": "2\nPUT 1 1\nPUT 2 2\nGET 1\nPUT 3 3\nGET 2", "expected": "1\n-1"},
        ],
        "hidden_test_cases": [
            {"input": "1\nPUT 2 1\nGET 2\nPUT 3 2\nGET 2\nGET 3", "expected": "1\n-1\n2"},
            {"input": "2\nPUT 1 1\nPUT 2 2\nGET 1\nPUT 3 3\nGET 2\nPUT 4 4\nGET 1\nGET 3\nGET 4", "expected": "1\n-1\n-1\n3\n4"},
        ],
    },
    # ─── 12. Coin Change (DP) ─────────────────────────────────────────────────
    {
        "title": "Coin Change",
        "description": (
            "You are given an integer array `coins` representing coins of different denominations and "
            "an integer `amount` representing a total amount of money.\n\n"
            "Return the fewest number of coins that you need to make up that amount.\n"
            "If that amount of money cannot be made up by any combination of the coins, return -1.\n\n"
            "You may assume that you have an infinite number of each kind of coin."
        ),
        "difficulty": "Medium",
        "topics": ["Dynamic Programming", "BFS"],
        "role_tags": ["SDE", "Backend", "ML Engineer"],
        "constraints": "1 ≤ coins.length ≤ 12\n1 ≤ coins[i] ≤ 2³¹ - 1\n0 ≤ amount ≤ 10⁴",
        "examples": [
            {"input": "1 2 5\n11", "output": "3", "explanation": "11 = 5 + 5 + 1 (3 coins)."},
            {"input": "2\n3", "output": "-1", "explanation": "Cannot make 3 with only 2-coins."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "import sys\n"
                "lines = sys.stdin.read().strip().split('\\n')\n"
                "coins = list(map(int, lines[0].split()))\n"
                "amount = int(lines[1])\n\n"
                "def coin_change(coins, amount):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print(coin_change(coins, amount))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int coinChange(int[] coins, int amount) {\n"
                "        // Your solution here\n"
                "        return -1;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int[] coins = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n"
                "        int amount = Integer.parseInt(sc.nextLine().trim());\n"
                "        System.out.println(coinChange(coins, amount));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "int coinChange(vector<int>& coins, int amount) {\n"
                "    // Your solution here\n"
                "    return -1;\n"
                "}\n\n"
                "int main() {\n"
                "    vector<int> coins; int x; string line;\n"
                "    getline(cin, line); istringstream iss(line); while (iss >> x) coins.push_back(x);\n"
                "    int amount; cin >> amount;\n"
                "    cout << coinChange(coins, amount) << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const lines = require('fs').readFileSync(0,'utf8').trim().split('\\n');\n"
                "const coins = lines[0].split(' ').map(Number);\n"
                "const amount = parseInt(lines[1]);\n\n"
                "function coinChange(coins, amount) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(coinChange(coins, amount));"
            ),
        },
        "test_cases": [
            {"input": "1 2 5\n11", "expected": "3"},
            {"input": "2\n3", "expected": "-1"},
        ],
        "hidden_test_cases": [
            {"input": "1\n0", "expected": "0"},
            {"input": "1 2 5\n100", "expected": "20"},
            {"input": "186 419 83 408\n6249", "expected": "20"},
        ],
    },
    # ─── 13. Product of Array Except Self (Array) ─────────────────────────────
    {
        "title": "Product of Array Except Self",
        "description": (
            "Given an integer array `nums`, return an array `answer` such that `answer[i]` is equal to "
            "the product of all the elements of `nums` except `nums[i]`.\n\n"
            "The product of any prefix or suffix of `nums` is guaranteed to fit in a 32-bit integer.\n"
            "You must write an algorithm that runs in O(n) time and without using the division operation."
        ),
        "difficulty": "Medium",
        "topics": ["Array", "Prefix Sum"],
        "role_tags": ["SDE", "Backend", "Frontend"],
        "constraints": "2 ≤ nums.length ≤ 10⁵\n-30 ≤ nums[i] ≤ 30\nThe product of any prefix/suffix fits in 32-bit",
        "examples": [
            {"input": "1 2 3 4", "output": "24 12 8 6", "explanation": "answer[0]=2*3*4=24, etc."},
            {"input": "-1 1 0 -3 3", "output": "0 0 9 0 0", "explanation": "Zero in array means most products are 0."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "nums = list(map(int, input().split()))\n\n"
                "def product_except_self(nums):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print(*product_except_self(nums))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int[] productExceptSelf(int[] nums) {\n"
                "        // Your solution here\n"
                "        return new int[]{};\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n"
                "        int[] result = productExceptSelf(nums);\n"
                "        StringBuilder sb = new StringBuilder();\n"
                "        for (int i = 0; i < result.length; i++) { if (i > 0) sb.append(' '); sb.append(result[i]); }\n"
                "        System.out.println(sb);\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "vector<int> productExceptSelf(vector<int>& nums) {\n"
                "    // Your solution here\n"
                "    return {};\n"
                "}\n\n"
                "int main() {\n"
                "    vector<int> nums; int x; string line; getline(cin, line);\n"
                "    istringstream iss(line); while (iss >> x) nums.push_back(x);\n"
                "    auto result = productExceptSelf(nums);\n"
                "    for (int i = 0; i < (int)result.size(); i++) { if (i) cout << ' '; cout << result[i]; }\n"
                "    cout << endl; return 0;\n"
                "}"
            ),
            "javascript": (
                "const nums = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n\n"
                "function productExceptSelf(nums) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(productExceptSelf(nums).join(' '));"
            ),
        },
        "test_cases": [
            {"input": "1 2 3 4", "expected": "24 12 8 6"},
            {"input": "-1 1 0 -3 3", "expected": "0 0 9 0 0"},
        ],
        "hidden_test_cases": [
            {"input": "2 3", "expected": "3 2"},
            {"input": "1 0 0", "expected": "0 0 0"},
        ],
    },
    # ─── 14. Group Anagrams (HashMap/String) ───────────────────────────────────
    {
        "title": "Group Anagrams",
        "description": (
            "Given an array of strings `strs`, group the anagrams together.\n\n"
            "An anagram is a word or phrase formed by rearranging the letters of a different word or phrase, "
            "typically using all the original letters exactly once.\n\n"
            "Input format: Space-separated strings.\n"
            "Output format: Each group on its own line, space-separated words in the group."
        ),
        "difficulty": "Medium",
        "topics": ["HashMap", "String", "Sorting"],
        "role_tags": ["SDE", "Backend", "Frontend"],
        "constraints": "1 ≤ strs.length ≤ 10⁴\n0 ≤ strs[i].length ≤ 100\nstrs[i] consists of lowercase English letters",
        "examples": [
            {"input": "eat tea tan ate nat bat", "output": "eat tea ate\ntan nat\nbat", "explanation": "Grouped by anagram."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "strs = input().split()\n\n"
                "def group_anagrams(strs):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "result = group_anagrams(strs)\n"
                "for group in result:\n"
                "    print(' '.join(sorted(group)))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static List<List<String>> groupAnagrams(String[] strs) {\n"
                "        // Your solution here\n"
                "        return new ArrayList<>();\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String[] strs = sc.nextLine().trim().split(\" \");\n"
                "        List<List<String>> result = groupAnagrams(strs);\n"
                "        for (List<String> group : result) {\n"
                "            Collections.sort(group);\n"
                "            System.out.println(String.join(\" \", group));\n"
                "        }\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "vector<vector<string>> groupAnagrams(vector<string>& strs) {\n"
                "    // Your solution here\n"
                "    return {};\n"
                "}\n\n"
                "int main() {\n"
                "    vector<string> strs; string word, line; getline(cin, line);\n"
                "    istringstream iss(line); while (iss >> word) strs.push_back(word);\n"
                "    auto result = groupAnagrams(strs);\n"
                "    for (auto& group : result) {\n"
                "        sort(group.begin(), group.end());\n"
                "        for (int i = 0; i < (int)group.size(); i++) { if (i) cout << ' '; cout << group[i]; }\n"
                "        cout << '\\n';\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const strs = require('fs').readFileSync(0,'utf8').trim().split(' ');\n\n"
                "function groupAnagrams(strs) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "const result = groupAnagrams(strs);\n"
                "result.forEach(g => console.log(g.sort().join(' ')));"
            ),
        },
        "test_cases": [
            {"input": "eat tea tan ate nat bat", "expected": "eat tea ate\ntan nat\nbat"},
        ],
        "hidden_test_cases": [
            {"input": "a", "expected": "a"},
            {"input": "ab ba abc", "expected": "ab ba\nabc"},
        ],
    },
    # ─── 15. Word Break (DP/String) ───────────────────────────────────────────
    {
        "title": "Word Break",
        "description": (
            "Given a string `s` and a dictionary of strings `wordDict`, return `true` if `s` can be "
            "segmented into a space-separated sequence of one or more dictionary words.\n\n"
            "Input format: First line = string s. Second line = space-separated dictionary words.\n"
            "Output format: true or false."
        ),
        "difficulty": "Medium",
        "topics": ["Dynamic Programming", "String", "HashMap"],
        "role_tags": ["SDE", "Backend", "Frontend", "ML Engineer"],
        "constraints": "1 ≤ s.length ≤ 300\n1 ≤ wordDict.length ≤ 1000\n1 ≤ wordDict[i].length ≤ 20\ns and wordDict[i] consist of lowercase English letters",
        "examples": [
            {"input": "leetcode\nleet code", "output": "true", "explanation": "'leet' and 'code' are in the dictionary."},
            {"input": "catsandog\ncats dog sand and cat", "output": "false", "explanation": "No valid segmentation exists."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "import sys\n"
                "lines = sys.stdin.read().strip().split('\\n')\n"
                "s = lines[0]\n"
                "word_dict = set(lines[1].split())\n\n"
                "def word_break(s, word_dict):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print('true' if word_break(s, word_dict) else 'false')"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static boolean wordBreak(String s, List<String> wordDict) {\n"
                "        // Your solution here\n"
                "        return false;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String s = sc.nextLine().trim();\n"
                "        List<String> wordDict = Arrays.asList(sc.nextLine().trim().split(\" \"));\n"
                "        System.out.println(wordBreak(s, wordDict));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "bool wordBreak(string s, vector<string>& wordDict) {\n"
                "    // Your solution here\n"
                "    return false;\n"
                "}\n\n"
                "int main() {\n"
                "    string s, line;\n"
                "    getline(cin, s); getline(cin, line);\n"
                "    istringstream iss(line);\n"
                "    vector<string> wordDict; string w; while (iss >> w) wordDict.push_back(w);\n"
                "    cout << (wordBreak(s, wordDict) ? \"true\" : \"false\") << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const lines = require('fs').readFileSync(0,'utf8').trim().split('\\n');\n"
                "const s = lines[0];\n"
                "const wordDict = new Set(lines[1].split(' '));\n\n"
                "function wordBreak(s, wordDict) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(wordBreak(s, wordDict) ? 'true' : 'false');"
            ),
        },
        "test_cases": [
            {"input": "leetcode\nleet code", "expected": "true"},
            {"input": "catsandog\ncats dog sand and cat", "expected": "false"},
        ],
        "hidden_test_cases": [
            {"input": "applepenapple\napple pen", "expected": "true"},
            {"input": "a\nb", "expected": "false"},
            {"input": "abcabc\na ab bc", "expected": "true"},
        ],
    },
    # ─── 16. Find Minimum in Rotated Sorted Array (Binary Search) ──────────────
    {
        "title": "Find Minimum in Rotated Sorted Array",
        "description": (
            "Suppose an array of length `n` sorted in ascending order is rotated between 1 and n times.\n\n"
            "Given the sorted rotated array `nums` of unique elements, return the minimum element of this array.\n"
            "You must write an algorithm that runs in O(log n) time."
        ),
        "difficulty": "Medium",
        "topics": ["Binary Search", "Array"],
        "role_tags": ["SDE", "Backend"],
        "constraints": "n == nums.length\n1 ≤ n ≤ 5000\n-5000 ≤ nums[i] ≤ 5000\nAll integers are unique\nnums is sorted and rotated between 1 and n times",
        "examples": [
            {"input": "3 4 5 1 2", "output": "1", "explanation": "Rotated 4 times, minimum is 1."},
            {"input": "4 5 6 7 0 1 2", "output": "0", "explanation": "Rotated 4 times, minimum is 0."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "nums = list(map(int, input().split()))\n\n"
                "def find_min(nums):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print(find_min(nums))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int findMin(int[] nums) {\n"
                "        // Your solution here\n"
                "        return 0;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n"
                "        System.out.println(findMin(nums));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "int findMin(vector<int>& nums) {\n"
                "    // Your solution here\n"
                "    return 0;\n"
                "}\n\n"
                "int main() {\n"
                "    vector<int> nums; int x; string line; getline(cin, line);\n"
                "    istringstream iss(line); while (iss >> x) nums.push_back(x);\n"
                "    cout << findMin(nums) << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const nums = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n\n"
                "function findMin(nums) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(findMin(nums));"
            ),
        },
        "test_cases": [
            {"input": "3 4 5 1 2", "expected": "1"},
            {"input": "4 5 6 7 0 1 2", "expected": "0"},
        ],
        "hidden_test_cases": [
            {"input": "11 13 15 17", "expected": "11"},
            {"input": "2 1", "expected": "1"},
            {"input": "1", "expected": "1"},
        ],
    },
    # ─── 17. Serialize and Deserialize Binary Tree (Hard/Tree) ─────────────────
    {
        "title": "Serialize and Deserialize Binary Tree",
        "description": (
            "Design an algorithm to serialize and deserialize a binary tree.\n\n"
            "Serialization is the process of converting a data structure into a sequence of bits so that it "
            "can be stored or transmitted. Deserialize is the reverse process.\n\n"
            "Input format: Level-order traversal (-1 for null nodes).\n"
            "Output format: Deserialized tree's level-order traversal."
        ),
        "difficulty": "Hard",
        "topics": ["Tree", "BFS", "Design"],
        "role_tags": ["SDE", "Backend", "System Design"],
        "constraints": "1 ≤ number of nodes ≤ 10⁴\n-1000 ≤ Node.val ≤ 1000",
        "examples": [
            {"input": "1 2 3 -1 -1 4 5", "output": "1 2 3 -1 -1 4 5", "explanation": "Round-trip serialization."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "from collections import deque\n"
                "vals = list(map(int, input().split()))\n\n"
                "class TreeNode:\n"
                "    def __init__(self, val=0, left=None, right=None):\n"
                "        self.val = val\n"
                "        self.left = left\n"
                "        self.right = right\n\n"
                "def serialize(root):\n"
                "    # Your solution here — return a string\n"
                "    pass\n\n"
                "def deserialize(data):\n"
                "    # Your solution here — return a TreeNode\n"
                "    pass\n\n"
                "def build_tree(vals):\n"
                "    if not vals or vals[0] == -1: return None\n"
                "    root = TreeNode(vals[0])\n"
                "    q = deque([root])\n"
                "    i = 1\n"
                "    while q and i < len(vals):\n"
                "        node = q.popleft()\n"
                "        if i < len(vals) and vals[i] != -1:\n"
                "            node.left = TreeNode(vals[i])\n"
                "            q.append(node.left)\n"
                "        i += 1\n"
                "        if i < len(vals) and vals[i] != -1:\n"
                "            node.right = TreeNode(vals[i])\n"
                "            q.append(node.right)\n"
                "        i += 1\n"
                "    return root\n\n"
                "def level_order(root):\n"
                "    if not root: return []\n"
                "    q = deque([root])\n"
                "    out = []\n"
                "    while q:\n"
                "        node = q.popleft()\n"
                "        if node:\n"
                "            out.append(str(node.val))\n"
                "            q.append(node.left)\n"
                "            q.append(node.right)\n"
                "        else:\n"
                "            out.append('-1')\n"
                "    while out and out[-1] == '-1': out.pop()\n"
                "    return ' '.join(out)\n\n"
                "root = build_tree(vals)\n"
                "data = serialize(root)\n"
                "root2 = deserialize(data)\n"
                "print(level_order(root2))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "class TreeNode {\n"
                "    int val; TreeNode left, right;\n"
                "    TreeNode(int v) { val = v; }\n"
                "}\n\n"
                "public class Solution {\n"
                "    public static String serialize(TreeNode root) {\n"
                "        // Your solution here\n"
                "        return \"\";\n"
                "    }\n"
                "    public static TreeNode deserialize(String data) {\n"
                "        // Your solution here\n"
                "        return null;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String[] parts = sc.nextLine().trim().split(\" \");\n"
                "        int[] vals = Arrays.stream(parts).mapToInt(Integer::parseInt).toArray();\n"
                "        if (vals.length == 0 || vals[0] == -1) return;\n"
                "        TreeNode root = new TreeNode(vals[0]);\n"
                "        Queue<TreeNode> q = new LinkedList<>();\n"
                "        q.add(root); int i = 1;\n"
                "        while (!q.isEmpty() && i < vals.length) {\n"
                "            TreeNode node = q.poll();\n"
                "            if (i < vals.length && vals[i] != -1) { node.left = new TreeNode(vals[i]); q.add(node.left); } i++;\n"
                "            if (i < vals.length && vals[i] != -1) { node.right = new TreeNode(vals[i]); q.add(node.right); } i++;\n"
                "        }\n"
                "        String data = serialize(root);\n"
                "        TreeNode root2 = deserialize(data);\n"
                "        Queue<TreeNode> q2 = new LinkedList<>();\n"
                "        q2.add(root2); List<String> out = new ArrayList<>();\n"
                "        while (!q2.isEmpty()) {\n"
                "            TreeNode n = q2.poll();\n"
                "            if (n != null) { out.add(String.valueOf(n.val)); q2.add(n.left); q2.add(n.right); }\n"
                "            else out.add(\"-1\");\n"
                "        }\n"
                "        while (!out.isEmpty() && out.get(out.size()-1).equals(\"-1\")) out.remove(out.size()-1);\n"
                "        System.out.println(String.join(\" \", out));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n"
                "struct TreeNode { int val; TreeNode *left, *right; TreeNode(int v) : val(v), left(nullptr), right(nullptr) {} };\n\n"
                "string serialize(TreeNode* root) {\n"
                "    // Your solution here\n"
                "    return \"\";\n"
                "}\n\n"
                "TreeNode* deserialize(string data) {\n"
                "    // Your solution here\n"
                "    return nullptr;\n"
                "}\n\n"
                "int main() {\n"
                "    string line; getline(cin, line);\n"
                "    istringstream iss(line); vector<int> vals; int x; while (iss >> x) vals.push_back(x);\n"
                "    if (vals.empty() || vals[0] == -1) return 0;\n"
                "    TreeNode* root = new TreeNode(vals[0]);\n"
                "    queue<TreeNode*> q; q.push(root); int i = 1;\n"
                "    while (!q.empty() && i < (int)vals.size()) {\n"
                "        TreeNode* node = q.front(); q.pop();\n"
                "        if (i < (int)vals.size() && vals[i] != -1) { node->left = new TreeNode(vals[i]); q.push(node->left); } i++;\n"
                "        if (i < (int)vals.size() && vals[i] != -1) { node->right = new TreeNode(vals[i]); q.push(node->right); } i++;\n"
                "    }\n"
                "    string data = serialize(root);\n"
                "    TreeNode* root2 = deserialize(data);\n"
                "    queue<TreeNode*> q2; q2.push(root2); vector<string> out;\n"
                "    while (!q2.empty()) {\n"
                "        TreeNode* n = q2.front(); q2.pop();\n"
                "        if (n) { out.push_back(to_string(n->val)); q2.push(n->left); q2.push(n->right); }\n"
                "        else out.push_back(\"-1\");\n"
                "    }\n"
                "    while (!out.empty() && out.back() == \"-1\") out.pop_back();\n"
                "    for (int i = 0; i < (int)out.size(); i++) { if (i) cout << ' '; cout << out[i]; }\n"
                "    cout << endl; return 0;\n"
                "}"
            ),
            "javascript": (
                "const vals = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n"
                "class TreeNode { constructor(val) { this.val = val; this.left = null; this.right = null; } }\n"
                "function buildTree(arr) {\n"
                "    if (!arr.length || arr[0] === -1) return null;\n"
                "    let root = new TreeNode(arr[0]);\n"
                "    let q = [root]; let i = 1;\n"
                "    while (q.length && i < arr.length) {\n"
                "        let node = q.shift();\n"
                "        if (i < arr.length && arr[i] !== -1) { node.left = new TreeNode(arr[i]); q.push(node.left); } i++;\n"
                "        if (i < arr.length && arr[i] !== -1) { node.right = new TreeNode(arr[i]); q.push(node.right); } i++;\n"
                "    }\n"
                "    return root;\n"
                "}\n"
                "function serialize(root) {\n"
                "    // Your solution here\n"
                "}\n"
                "function deserialize(data) {\n"
                "    // Your solution here\n"
                "}\n"
                "function levelOrder(root) {\n"
                "    if (!root) return [];\n"
                "    let q = [root]; let out = [];\n"
                "    while (q.length) {\n"
                "        let n = q.shift();\n"
                "        if (n) { out.push(n.val); q.push(n.left); q.push(n.right); }\n"
                "        else out.push(-1);\n"
                "    }\n"
                "    while (out.length && out[out.length-1] === -1) out.pop();\n"
                "    return out;\n"
                "}\n"
                "const root = buildTree(vals);\n"
                "const data = serialize(root);\n"
                "const root2 = deserialize(data);\n"
                "console.log(levelOrder(root2).join(' '));"
            ),
        },
        "test_cases": [
            {"input": "1 2 3 -1 -1 4 5", "expected": "1 2 3 -1 -1 4 5"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected": "1"},
            {"input": "1 2", "expected": "1 2"},
        ],
    },
    # ─── 18. Trapping Rain Water (Hard/Array) ─────────────────────────────────
    {
        "title": "Trapping Rain Water",
        "description": (
            "Given `n` non-negative integers representing an elevation map where the width of each bar is 1, "
            "compute how much water it can trap after raining."
        ),
        "difficulty": "Hard",
        "topics": ["Array", "Two Pointers", "Stack", "Dynamic Programming"],
        "role_tags": ["SDE", "Backend", "System Design"],
        "constraints": "n == height.length\n1 ≤ n ≤ 2 × 10⁴\n0 ≤ height[i] ≤ 10⁵",
        "examples": [
            {"input": "0 1 0 2 1 0 1 3 2 1 2 1", "output": "6", "explanation": "6 units of water are trapped."},
            {"input": "4 2 0 3 2 5", "output": "9", "explanation": "9 units of water are trapped."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "height = list(map(int, input().split()))\n\n"
                "def trap(height):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print(trap(height))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int trap(int[] height) {\n"
                "        // Your solution here\n"
                "        return 0;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int[] height = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n"
                "        System.out.println(trap(height));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "int trap(vector<int>& height) {\n"
                "    // Your solution here\n"
                "    return 0;\n"
                "}\n\n"
                "int main() {\n"
                "    vector<int> height; int x; string line; getline(cin, line);\n"
                "    istringstream iss(line); while (iss >> x) height.push_back(x);\n"
                "    cout << trap(height) << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const height = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n\n"
                "function trap(height) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(trap(height));"
            ),
        },
        "test_cases": [
            {"input": "0 1 0 2 1 0 1 3 2 1 2 1", "expected": "6"},
            {"input": "4 2 0 3 2 5", "expected": "9"},
        ],
        "hidden_test_cases": [
            {"input": "1", "expected": "0"},
            {"input": "1 2", "expected": "0"},
            {"input": "5 4 3 2 1", "expected": "0"},
        ],
    },
    # ─── 19. Longest Increasing Subsequence (DP) ──────────────────────────────
    {
        "title": "Longest Increasing Subsequence",
        "description": (
            "Given an integer array `nums`, return the length of the longest strictly increasing subsequence.\n\n"
            "A subsequence is a sequence that can be derived from an array by deleting some or no elements "
            "without changing the order of the remaining elements."
        ),
        "difficulty": "Medium",
        "topics": ["Dynamic Programming", "Binary Search"],
        "role_tags": ["SDE", "Backend", "ML Engineer", "Data Engineer"],
        "constraints": "1 ≤ nums.length ≤ 2500\n-10⁴ ≤ nums[i] ≤ 10⁴",
        "examples": [
            {"input": "10 9 2 5 3 7 101 18", "output": "4", "explanation": "LIS is [2,3,7,101] length 4."},
            {"input": "0 1 0 3 2 3", "output": "4", "explanation": "LIS is [0,1,2,3] length 4."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "nums = list(map(int, input().split()))\n\n"
                "def length_of_lis(nums):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print(length_of_lis(nums))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int lengthOfLIS(int[] nums) {\n"
                "        // Your solution here\n"
                "        return 0;\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        int[] nums = Arrays.stream(sc.nextLine().trim().split(\" \")).mapToInt(Integer::parseInt).toArray();\n"
                "        System.out.println(lengthOfLIS(nums));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "int lengthOfLIS(vector<int>& nums) {\n"
                "    // Your solution here\n"
                "    return 0;\n"
                "}\n\n"
                "int main() {\n"
                "    vector<int> nums; int x; string line; getline(cin, line);\n"
                "    istringstream iss(line); while (iss >> x) nums.push_back(x);\n"
                "    cout << lengthOfLIS(nums) << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const nums = require('fs').readFileSync(0,'utf8').trim().split(' ').map(Number);\n\n"
                "function lengthOfLIS(nums) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(lengthOfLIS(nums));"
            ),
        },
        "test_cases": [
            {"input": "10 9 2 5 3 7 101 18", "expected": "4"},
            {"input": "0 1 0 3 2 3", "expected": "4"},
        ],
        "hidden_test_cases": [
            {"input": "7 7 7 7 7", "expected": "1"},
            {"input": "1", "expected": "1"},
            {"input": "3 1 2", "expected": "2"},
        ],
    },
    # ─── 20. Alien Dictionary (Hard/Graph/Topological Sort) ───────────────────
    {
        "title": "Alien Dictionary",
        "description": (
            "Given a sorted list of words from an alien language, derive the order of characters in that language.\n\n"
            "All words are sorted lexicographically by the rules of the alien language. If there is no valid "
            "character ordering, return an empty string.\n\n"
            "Input format: First line = space-separated words in alien dictionary order.\n"
            "Output format: A string representing the character order."
        ),
        "difficulty": "Hard",
        "topics": ["Graph", "Topological Sort", "BFS", "DFS"],
        "role_tags": ["SDE", "Backend", "System Design"],
        "constraints": "1 ≤ words.length ≤ 100\n1 ≤ words[i].length ≤ 20\nwords[i] consists of only lowercase English letters\nAll words are unique",
        "examples": [
            {"input": "wrt wrf er ett rftt", "output": "wertf", "explanation": "From comparisons: w<r, r<t, e<r, t<f."},
            {"input": "z x", "output": "zx", "explanation": "z comes before x."},
        ],
        "supported_languages": ["python", "java", "cpp", "javascript", "typescript"],
        "starter_codes": {
            "python": (
                "words = input().split()\n\n"
                "def alien_order(words):\n"
                "    # Your solution here\n"
                "    pass\n\n"
                "print(alien_order(words))"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static String alienOrder(String[] words) {\n"
                "        // Your solution here\n"
                "        return \"\";\n"
                "    }\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        String[] words = sc.nextLine().trim().split(\" \");\n"
                "        System.out.println(alienOrder(words));\n"
                "    }\n"
                "}"
            ),
            "cpp": (
                "#include <bits/stdc++.h>\nusing namespace std;\n\n"
                "string alienOrder(vector<string>& words) {\n"
                "    // Your solution here\n"
                "    return \"\";\n"
                "}\n\n"
                "int main() {\n"
                "    vector<string> words; string w, line; getline(cin, line);\n"
                "    istringstream iss(line); while (iss >> w) words.push_back(w);\n"
                "    cout << alienOrder(words) << endl;\n"
                "    return 0;\n"
                "}"
            ),
            "javascript": (
                "const words = require('fs').readFileSync(0,'utf8').trim().split(' ');\n\n"
                "function alienOrder(words) {\n"
                "    // Your solution here\n"
                "}\n\n"
                "console.log(alienOrder(words));"
            ),
        },
        "test_cases": [
            {"input": "wrt wrf er ett rftt", "expected": "wertf"},
            {"input": "z x", "expected": "zx"},
        ],
        "hidden_test_cases": [
            {"input": "abc ab", "expected": ""},
            {"input": "a b c d", "expected": "abcd"},
            {"input": "ba bc bd", "expected": "acd"},
        ],
    },
]


def _seed_challenges(db: Session):
    """Seed production challenges if DB is empty."""
    count = db.query(func.count(CodingChallenge.id)).scalar()
    if count and count > 0:
        return

    for ch_data in SEED_CHALLENGES:
        ch = CodingChallenge(
            title=ch_data["title"],
            description=ch_data["description"],
            difficulty=ch_data["difficulty"],
            topics=ch_data.get("topics", []),
            role_tags=ch_data.get("role_tags", []),
            constraints=ch_data.get("constraints"),
            examples=ch_data.get("examples", []),
            supported_languages=ch_data.get("supported_languages", ["python"]),
            starter_codes=ch_data.get("starter_codes", {}),
            starter_code=ch_data.get("starter_codes", {}).get("python", ""),  # legacy
            language="python",
            test_cases=ch_data.get("test_cases", []),
            hidden_test_cases=ch_data.get("hidden_test_cases", []),
            time_limit_ms=5000,
            memory_limit_kb=131072,
        )
        db.add(ch)
    db.commit()


# ─── Challenge Endpoints ───────────────────────────────────────────────────────

@router.get("/challenges", response_model=List[CodingChallengeResponse])
def get_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all challenges (auto-seeds if empty, cached for 5 minutes)."""
    import time
    now = time.time()
    if _challenge_cache["data"] and (now - _challenge_cache["ts"]) < _CHALLENGE_CACHE_TTL:
        return _challenge_cache["data"]

    _seed_challenges(db)
    challenges = db.query(CodingChallenge).all()
    _challenge_cache["data"] = challenges
    _challenge_cache["ts"] = now
    return challenges


@router.get("/challenges/{challenge_id}", response_model=CodingChallengeResponse)
def get_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ch = db.query(CodingChallenge).filter(CodingChallenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return ch


# ─── Session Management ───────────────────────────────────────────────────────

@router.post("/session/start", response_model=CodingSessionResponse)
@limiter.limit("5/minute")
def start_coding_session(
    request: Request,
    body: CodingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a new coding round. AI selects a challenge based on the interview context.
    If interview_session_id is provided, inherits role and difficulty from that session.
    """
    _seed_challenges(db)

    # Determine role and difficulty from interview session
    role = "SDE"
    difficulty = "Medium"
    if body.interview_session_id:
        interview = db.query(InterviewSession).filter(
            InterviewSession.id == body.interview_session_id,
            InterviewSession.user_id == current_user.id,
        ).first()
        if interview:
            role = interview.role or "SDE"
            difficulty = interview.difficulty or "Medium"

    # Check if session already exists for this interview
    if body.interview_session_id:
        existing = db.query(CodingSession).filter(
            CodingSession.interview_session_id == body.interview_session_id,
            CodingSession.user_id == current_user.id,
        ).first()
        if existing:
            return existing

    # AI selects challenge (adapts based on user performance)
    challenge = AIService.select_coding_challenge(role, difficulty, db, user_id=current_user.id)
    if not challenge:
        raise HTTPException(status_code=404, detail="No coding challenges available. Please seed the database.")

    session = CodingSession(
        user_id=current_user.id,
        interview_session_id=body.interview_session_id,
        challenge_id=challenge.id,
        language_used=body.language or "python",
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Eager-load challenge for response
    session.challenge = challenge
    return session


@router.get("/session/{coding_session_id}", response_model=CodingSessionResponse)
def get_coding_session(
    coding_session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(CodingSession).filter(
        CodingSession.id == coding_session_id,
        CodingSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Coding session not found")
    return session


# ─── Code Execution ───────────────────────────────────────────────────────────

@router.post("/run", response_model=CodingRunResponse)
@limiter.limit("10/minute")
def run_code(
    request: Request,
    run_in: CodingRunCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run code against PUBLIC test cases only.
    Hidden test cases are NOT executed on /run — only on final submit.
    """
    if len(run_in.code) > MAX_CODE_SIZE:
        raise HTTPException(status_code=400, detail=f"Code exceeds maximum size of {MAX_CODE_SIZE} characters")

    challenge = db.query(CodingChallenge).filter(CodingChallenge.id == run_in.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    result = CodeExecutor.execute(
        code=run_in.code,
        language=run_in.language,
        public_test_cases=challenge.test_cases or [],
        hidden_test_cases=[],  # Never run hidden on /run
        is_final=False,
    )

    return CodingRunResponse(
        status=result["status"],
        runtime_ms=result.get("runtime_ms"),
        memory_kb=result.get("memory_kb"),
        output=result.get("output"),
        all_passed=result.get("all_passed", False),
        public_results=[TestCaseResult(**r) for r in result.get("public_results", [])],
        hidden_total=len(challenge.hidden_test_cases or []),
        hidden_passed=0,
    )


@router.post("/submit", response_model=CodingSubmissionResponse)
@limiter.limit("5/minute")
def submit_code(
    request: Request,
    submission_in: CodingSubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Final submission: runs all test cases (public + hidden), generates AI code review, saves score.
    """
    if len(submission_in.code) > MAX_CODE_SIZE:
        raise HTTPException(status_code=400, detail=f"Code exceeds maximum size of {MAX_CODE_SIZE} characters")

    challenge = db.query(CodingChallenge).filter(CodingChallenge.id == submission_in.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Execute against ALL test cases
    result = CodeExecutor.execute(
        code=submission_in.code,
        language=submission_in.language,
        public_test_cases=challenge.test_cases or [],
        hidden_test_cases=challenge.hidden_test_cases or [],
        is_final=True,
    )

    # Compute correctness score
    public_results = result.get("public_results", [])
    hidden_passed = result.get("hidden_passed", 0)
    hidden_total = len(challenge.hidden_test_cases or [])
    public_passed = sum(1 for r in public_results if r.get("passed", False))
    public_total = len(public_results)
    total_passed = public_passed + hidden_passed
    total_cases = public_total + hidden_total
    correctness_score = round((total_passed / max(total_cases, 1)) * 100, 1)

    # AI Code Review
    all_results_for_review = [
        {"passed": r.get("passed", False)} for r in public_results
    ] + [{"passed": True}] * hidden_passed + [{"passed": False}] * (hidden_total - hidden_passed)

    ai_review = AIService.review_code(
        code=submission_in.code,
        language=submission_in.language,
        problem_description=challenge.description,
        test_results=all_results_for_review,
    )

    # Save submission
    db_submission = CodingSubmission(
        user_id=current_user.id,
        challenge_id=challenge.id,
        session_id=submission_in.session_id,
        coding_session_id=submission_in.coding_session_id,
        code=submission_in.code,
        language=submission_in.language,
        status=result["status"],
        runtime_ms=result.get("runtime_ms"),
        memory_kb=result.get("memory_kb"),
        output=result.get("output"),
        test_results=[{**r, "input": None, "expected": None, "actual": None} for r in result.get("public_results", [])]
                   + [{"test_number": public_total + i + 1, "passed": i < hidden_passed} for i in range(hidden_total)],
        correctness_score=correctness_score,
        ai_feedback=ai_review.get("feedback"),
        ai_score=ai_review.get("score"),
        time_complexity=ai_review.get("time_complexity"),
        space_complexity=ai_review.get("space_complexity"),
        is_final=True,
    )
    db.add(db_submission)
    db.flush()

    # Update coding session
    if submission_in.coding_session_id:
        coding_session = db.query(CodingSession).filter(
            CodingSession.id == submission_in.coding_session_id
        ).first()
        if coding_session:
            # Combined score: 70% correctness + 30% AI quality
            combined_score = round((correctness_score / 100) * 7.0 + (ai_review.get("score", 5.0) / 10) * 3.0, 2)
            coding_session.status = "submitted"
            coding_session.ended_at = datetime.utcnow()
            coding_session.language_used = submission_in.language
            coding_session.coding_score = combined_score
            coding_session.final_submission_id = db_submission.id

            # Update parent interview session if linked
            if coding_session.interview_session_id:
                interview_session = db.query(InterviewSession).filter(
                    InterviewSession.id == coding_session.interview_session_id
                ).first()
                if interview_session:
                    interview_session.score = combined_score

    db.commit()
    db.refresh(db_submission)

    # Trigger automation: update skill gap and career readiness
    if submission_in.coding_session_id:
        try:
            from app.services.automation_service import AutomationService
            automation = AutomationService(db)
            automation.on_coding_complete(current_user.id, submission_in.coding_session_id)
        except Exception as auto_err:
            print(f"Automation trigger (coding) failed: {auto_err}")

        # Auto-generate coding report in background
        try:
            from app.models.generated_report import GeneratedReport
            from app.services.report_service import ReportService
            report = GeneratedReport(
                user_id=current_user.id,
                title=f"Coding Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                report_type="coding",
                status="generating",
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            pdf_buffer = ReportService.generate_coding_report(db, current_user)
            os.makedirs("uploads/reports", exist_ok=True)
            file_path = os.path.join("uploads/reports", f"report_{report.id}.pdf")
            with open(file_path, "wb") as f:
                f.write(pdf_buffer.getvalue())
            report.file_path = file_path
            report.file_size = os.path.getsize(file_path)
            report.status = "ready"
            report.scores_snapshot = json.dumps(ReportService._capture_scores_snapshot(db, current_user))
            db.commit()
        except Exception as report_err:
            print(f"Auto-report generation (coding) failed: {report_err}")
            try:
                if report and report.id:
                    report.status = "failed"
                    db.commit()
            except Exception:
                pass

    # Build full response including public test results
    public_tc_results = [
        TestCaseResult(
            test_number=r.get("test_number", i + 1),
            passed=r.get("passed", False),
            runtime_ms=r.get("runtime_ms"),
            memory_kb=r.get("memory_kb"),
            input=r.get("input"),
            expected=r.get("expected"),
            actual=r.get("actual"),
            error=r.get("error"),
        )
        for i, r in enumerate(public_results)
    ] + [
        TestCaseResult(
            test_number=public_total + i + 1,
            passed=i < hidden_passed,
            input=None,  # Hidden
            expected=None,
            actual=None,
        )
        for i in range(hidden_total)
    ]

    return CodingSubmissionResponse(
        id=db_submission.id,
        status=db_submission.status,
        language=db_submission.language,
        runtime_ms=db_submission.runtime_ms,
        memory_kb=db_submission.memory_kb,
        output=db_submission.output,
        correctness_score=correctness_score,
        ai_feedback=ai_review.get("feedback"),
        ai_score=ai_review.get("score"),
        time_complexity=ai_review.get("time_complexity"),
        space_complexity=ai_review.get("space_complexity"),
        is_final=True,
        test_results=public_tc_results,
        created_at=db_submission.created_at,
    )


# ─── Submission History ───────────────────────────────────────────────────────

@router.get("/submissions", response_model=SubmissionHistoryResponse)
def get_submissions(
    coding_session_id: Optional[int] = Query(None),
    challenge_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get submission history for the current user, optionally filtered by session or challenge."""
    query = db.query(CodingSubmission).filter(CodingSubmission.user_id == current_user.id)
    if coding_session_id:
        query = query.filter(CodingSubmission.coding_session_id == coding_session_id)
    if challenge_id:
        query = query.filter(CodingSubmission.challenge_id == challenge_id)

    submissions = query.order_by(CodingSubmission.created_at.desc()).all()
    items = [
        SubmissionHistoryItem(
            id=s.id,
            status=s.status,
            language=s.language,
            runtime_ms=s.runtime_ms,
            memory_kb=s.memory_kb,
            correctness_score=s.correctness_score,
            ai_score=s.ai_score,
            is_final=s.is_final or False,
            created_at=s.created_at,
        )
        for s in submissions
    ]
    return SubmissionHistoryResponse(submissions=items, total=len(items))


# ─── Retry ──────────────────────────────────────────────────────────────────

@router.post("/retry", response_model=CodingSessionResponse)
@limiter.limit("5/minute")
def retry_coding_session(
    request: Request,
    body: CodingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retry the coding round with a fresh session and new challenge.
    """
    _seed_challenges(db)

    role = "SDE"
    difficulty = "Medium"
    if body.interview_session_id:
        interview = db.query(InterviewSession).filter(
            InterviewSession.id == body.interview_session_id,
            InterviewSession.user_id == current_user.id,
        ).first()
        if interview:
            role = interview.role or "SDE"
            difficulty = interview.difficulty or "Medium"

    challenge = AIService.select_coding_challenge(role, difficulty, db, user_id=current_user.id)
    if not challenge:
        raise HTTPException(status_code=404, detail="No coding challenges available")

    session = CodingSession(
        user_id=current_user.id,
        interview_session_id=body.interview_session_id,
        challenge_id=challenge.id,
        language_used=body.language or "python",
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    session.challenge = challenge
    return session


# ─── Get Latest Submission ─────────────────────────────────────────────────

@router.get("/latest-submission")
def get_latest_submission(
    coding_session_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the latest final submission for a coding session."""
    submission = db.query(CodingSubmission).filter(
        CodingSubmission.coding_session_id == coding_session_id,
        CodingSubmission.user_id == current_user.id,
        CodingSubmission.is_final == True,
    ).order_by(CodingSubmission.created_at.desc()).first()

    if not submission:
        raise HTTPException(status_code=404, detail="No submission found")

    return {
        "id": submission.id,
        "status": submission.status,
        "correctness_score": submission.correctness_score,
        "ai_score": submission.ai_score,
        "ai_feedback": submission.ai_feedback,
        "time_complexity": submission.time_complexity,
        "space_complexity": submission.space_complexity,
        "runtime_ms": submission.runtime_ms,
        "memory_kb": submission.memory_kb,
        "created_at": submission.created_at,
    }
