#!/snap/gogs/current/python/bin/python

import os, sys
sys.path.append(os.path.join(os.environ['SNAP'], 'hooks'))

from installer import Installer

Installer().database_post_start()

