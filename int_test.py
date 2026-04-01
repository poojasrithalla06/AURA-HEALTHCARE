import urllib.request
import urllib.parse
import json
import http.cookiejar

def test():
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    base_url = 'http://127.0.0.1:5000'

    print("--- 1. Testing Signup ---")
    data = urllib.parse.urlencode({'username': 'testuser1', 'email': 'test1@example.com', 'password': 'pass', 'role': 'user'}).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/signup', data=data)
    try:
        res = opener.open(req)
        print("Signup success")
    except Exception as e:
        print("Signup error:", e)

    print("--- 2. Testing Login ---")
    data = urllib.parse.urlencode({'username': 'testuser1', 'password': 'pass'}).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/login', data=data)
    try:
        res = opener.open(req)
        print("Login success. Redirected to:", res.geturl())
    except Exception as e:
        print("Login error:", e)

    print("--- 3. Testing Dashboard ---")
    req = urllib.request.Request(f'{base_url}/dashboard')
    try:
        res = opener.open(req)
        print("Dashboard success, status:", res.getcode())
    except Exception as e:
        print("Dashboard error:", e)

    print("--- 4. Testing /sos ---")
    # /sos is POST redirecting to dashboard
    req = urllib.request.Request(f'{base_url}/sos', data=b"")
    try:
        res = opener.open(req)
        print("SOS success:", res.getcode())
    except Exception as e:
        print("SOS error:", e)

    print("--- 5. Testing /explain ---")
    # /explain is POST json
    data = json.dumps({'query': 'headache'}).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/explain', data=data, headers={'Content-Type': 'application/json'})
    try:
        res = opener.open(req)
        print("Explain response:", res.read().decode('utf-8'))
    except Exception as e:
        print("Explain error:", e)

    print("--- 6. Testing /chat ---")
    # /chat is POST json
    data = json.dumps({'message': 'hello'}).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/chat', data=data, headers={'Content-Type': 'application/json'})
    try:
        res = opener.open(req)
        print("Chat response:", res.read().decode('utf-8'))
    except Exception as e:
        print("Chat error:", e)

test()
