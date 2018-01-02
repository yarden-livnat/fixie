**Added:**

* ``next_jobid()`` provides the next jobid in a thread-safe way.
* ``flock()`` now provides a file-system based mechanism for locking
  files, enabling syncronization across processes and machines that
  need it.

**Changed:** None

* ``ENVVARS`` is now an OrderedDict, in order to apply defaults in the
  correct order.

**Deprecated:** None

**Removed:** None

**Fixed:** None

**Security:** None
