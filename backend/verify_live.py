import urllib.request, json

# Login
data = json.dumps({'email': 'admin@ai-platform.com', 'password': 'admin123'}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/auth/login', data=data, method='POST')
req.add_header('Content-Type', 'application/json')
r = urllib.request.urlopen(req)
resp = json.loads(r.read().decode())
token = resp['access_token']
print("LOGIN OK - admin@ai-platform.com")
print()

# Analytics
req2 = urllib.request.Request('http://127.0.0.1:8000/admin/coding/analytics')
req2.add_header('Authorization', 'Bearer ' + token)
r2 = urllib.request.urlopen(req2)
analytics = json.loads(r2.read().decode())
print("=== ADMIN CODING ANALYTICS ===")
for k, v in analytics.items():
    print(f"  {k}: {v}")
print()

# Submissions
req3 = urllib.request.Request('http://127.0.0.1:8000/admin/coding/submissions')
req3.add_header('Authorization', 'Bearer ' + token)
r3 = urllib.request.urlopen(req3)
subs = json.loads(r3.read().decode())
print("=== ADMIN CODING SUBMISSIONS ===")
print("Total:", subs.get('total'))
for s in subs.get('submissions', [])[:5]:
    sid = s["id"]
    email = s["candidate_email"]
    title = s["challenge_title"]
    lang = s["language"]
    status = s["status"]
    score = s.get("ai_score", "N/A")
    print(f"  ID:{sid} | {email} | {title} | lang:{lang} | status:{status} | ai_score:{score}")
print()

# Coding challenges list
req4 = urllib.request.Request('http://127.0.0.1:8000/coding/challenges')
req4.add_header('Authorization', 'Bearer ' + token)
r4 = urllib.request.urlopen(req4)
challenges = json.loads(r4.read().decode())
print("=== CODING CHALLENGES ===")
for c in challenges[:5]:
    print(f"  {c['title']} | difficulty:{c.get('difficulty')} | tags:{c.get('tags')}")

print()
print("ALL CHECKS PASSED - Platform is live!")
