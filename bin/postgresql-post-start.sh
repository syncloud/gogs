#!/snap/gogs/current/python/bin/python

import os, sys
sys.path.append(os.path.join(os.environ['SNAP'], 'hooks'))

from gogs_hooks import database_post_start
database_post_start()

