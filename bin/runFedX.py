import os
import subprocess
import argparse
import shlex
from time import time

# Constants
FEDX_COMMAND = 'timeout %s %s -d %s @q %s'
RUN_COUNT = 1

def _build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', type=str,
                      help="query file to execute",)
    parser.add_argument('endpoint', type=str,
                        help="endpoint description file",)
    parser.add_argument('fedx_root', type=str,
                        help='FedX root')
    parser.add_argument('--timeout', dest='timeout', default=300,
                        action='store', type=int,
                        help='running time')
    return parser

def _query_name(f):
    return f.split('/')[-1].split('.')[0]

def main(args):

    # delete FedX warm up database.
    subprocess.call(shlex.split('rm -rf {0}'.format(
        os.path.join(args.fedx_root, 'cache.db')
    )))
    query = _query_name(args.query)

    # run FedX five times
    for _ in xrange(RUN_COUNT):
        start_time = time()
        cmd = FEDX_COMMAND % (args.timeout,
                              os.path.join(args.fedx_root, 'cli.sh'),
                              args.endpoint,
                              args.query,)

        fedx_process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
        output = fedx_process.stdout.readlines()
        ret = fedx_process.wait()
        
        # It all went OK.    
        if (ret == 0 or ret ==124):    
            run_time =  time() - start_time
            card = len([x for x in output if x.strip().startswith('[') and x.strip().endswith(']')])
            print 'fedx,{0},{1},{2},{3}'.format(query, run_time, run_time, card)

            # other error.
        else:
            run_time =  time() - start_time    
            print 'fedx,{0},{1},0 -- ERROR: {2}'.format(query, run_time, ret)

        # if ret == 0 or ret == 124 or ret == 1:
        #     # It all went OK.
        #     run_time =  time() - start_time
        #     card = len([x for x in output if x.strip().startswith('[') and x.strip().endswith(']')])
        #     print 'fedx,{0},{1},{2},{3}'.format(query, run_time, run_time, card)

        # else:
        #     # Timeout or other error.
        #     print 'fedx,{0},0,0 -- ERROR: {1}'.format(query, ret)


if __name__ == '__main__':
    parser = _build_parser()
    args = parser.parse_args()
    main(args)
