================
fixie Change Log
================

.. current developments

v0.0.4
====================

**Added:**

* Added support for JSON to persist Python bytes as base64 strings.
* Added support for JSON to persist UUIDs.
* ``fixie.default_path()`` function enables the creation of path names
  from metadata, if needed.
* ``$FIXIE_HOLDING_TIME`` added for specifying the
  length of time to store databases on the server.
* ``$FIXIE_PATHS_DIR`` for denoting the fixie paths
  directory, where database path metadata is stored.


**Changed:**

* ``RequestHandler.write()`` now uses the ``fixie.jsonutils.encode()`` to
  encode dictionaries as JSON. Additionally, a newline is appended to the
  end of the message, so that curl and other utilities look nice on the
  command line.
* ``fixie`` command line utility now has executable permissions.




v0.0.3
====================

**Added:**

* Added jobid alias handling capabilities.
* New ``fixie.tools.detached_call()`` function for spawning a process in a
  detached state.
* New ``fixie.tools.waitpid()`` function for waiting on arbitrary PIDs,
  even when they weren't spawned by the current process.
* New ``$FIXIE_NJOBS`` environment variable for specifying the
  number of jobs for a server. Defaults to the number of CPUs
  on the machine.
* ``next_jobid()`` provides the next jobid in a thread-safe way.
* ``flock()`` now provides a file-system based mechanism for locking
  files, enabling syncronization across processes and machines that
  need it.
* New ``fixie.jsonutils`` module for handling JSON in a standard way across fixie projects.
* New ``fixie.tools`` module for fixie service tools, including
  a ``fetch()`` function for getting fixie URLs and a simple
  interface for verifying users.
* New ``$FIXIE_{SERVICE}_URL`` environment variables for
  denoting remote locations of fixie services.
* New dependency on ``lazyasd``.


**Changed:**

* Made the ``fixie.eviron.context()`` and related functions reentrant.
* ``ENVVARS`` is now an OrderedDict, in order to apply defaults in the
  correct order.




v0.0.2
====================

**Added:**

* New ``fixie`` command line interface for launching installed fixie services.
* Fixie now has a strict dependence on xonsh.
* Configuration of fixie and fixie services now occurs via environment variables.
  The fixie evironment object is accessible as `fixie.environ.ENV`
* New fixie logger.




v0.0.1
====================

**Added:**

* ``RequestHandler`` class that converts the body from JSON and validates it against
  a schema on the handler itself.




