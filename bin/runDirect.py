import requests, sys, argparse
from time import time

def run_query(url, query, timeout=300):
    payload = {'query': query, 'format': 'json'}

    try:
        r = requests.post(url, payload, timeout=timeout)
    except requests.exceptions.Timeout:
        return -1

    print r

    if r.status_code == 200:
        return len(r.json()['results']['bindings'])
    return -1


def _build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', type=str,
                      help="query file to execute",)
    parser.add_argument('endpoint', type=str,
                        help="SPARQL endpoint URL",)
    parser.add_argument('--timeout', dest='timeout', default=300,
                        action='store', type=int,
                        help='running time')
    return parser

def _query_name(f):
    return f.split('/')[-1].split('.')[0]


def main(args):
    query = _query_name(args.query)
    start_time = time()
    with open(args.query, 'r') as q:
        content = q.read().strip()
    with open(args.endpoint, 'r') as e:
        endpoint = e.read().strip()
    result = run_query(endpoint, content, args.timeout)
    run_time = time()-start_time
    print 'direct,{0},{1},{2},{3}'.format(query, run_time, run_time, result)

if __name__ == '__main__':
    parser =  _build_parser()
    args = parser.parse_args()
    main(args)
