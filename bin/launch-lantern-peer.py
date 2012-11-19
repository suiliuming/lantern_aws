#!/usr/bin/env python

# Watch for DRY (Don't Repeat Yourself) violation warnings.  If you change
# these values, make sure to update unpack_template.py accordingly.

import base64
import os
import random
from cStringIO import StringIO
import sys
import tarfile
import tempfile
import zlib

from boto.cloudformation.connection import CloudFormationConnection


assert __name__ == '__main__', "Don't import me, call me as a script."

if len(sys.argv) != 2:
    print "Launch a new lanter-peer node."
    print "Usage: %s <node name>" % sys.argv[0]
    sys.exit(1)

here = os.path.dirname(sys.argv[0])
stack_name = sys.argv[1]

sio = StringIO()

ssl_proxy_port = random.randint(1024, 61024)

# DRY warning: mode.
with tarfile.open(fileobj=sio, mode='w:bz2', dereference=True) as tf:

    #DRY warning: bootstrap directory name.
    tf.add(os.path.join(here, '..', 'bootstrap'),
           arcname='bootstrap')

    _, tmp_name = tempfile.mkstemp()
    file(tmp_name, 'w').write(str(ssl_proxy_port))
    #DRY warning:
    #    - bootstrap directory name,
    #    - path of bootstrap salt module, and
    #    - proxy port filename.
    tf.add(tmp_name, arcname="bootstrap/salt/bootstrap/public-proxy-port")

blob = sio.getvalue()
sanitized_blob = base64.b64encode(blob)

template = file(os.path.join(here, 'unpack_template.py')).read()

# DRY warning: placeholder string.
self_extractable = template.replace("<PUT_BLOB_HERE>", sanitized_blob)

b64_se = base64.b64encode(self_extractable)

# The blob is broken into parts because each cloudformation template parameter
# has a size limit.  This blob is reassembled inside the template to become
# the user-data.
sizelimit = 4096
parts = [b64_se[i*sizelimit:(i+1)*sizelimit]
         for i in xrange(4)]


parameters = ([("LanternSSLProxyPort", ssl_proxy_port)]
              + zip(["Bootstrap", "Bootstrap2", "Bootstrap3", "Bootstrap4"],
                    # Omit empty parts.
                    filter(None, parts)))

template = file(os.path.join(here,
                             '..',
                             'cloudformation',
                             'lantern-peer.json')).read()


conn = CloudFormationConnection()
print conn.create_stack(stack_name,
                        template_body=template,
                        parameters=parameters)
