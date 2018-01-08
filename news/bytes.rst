**Added:**

* Added support for JSON to persist Python bytes as base64 strings.
* Added support for JSON to persist UUIDs.

**Changed:**

* ``RequestHandler.write()`` now uses the ``fixie.jsonutils.encode()`` to
  encode dictionaries as JSON. Additionally, a newline is appended to the
  end of the message, so that curl and other utilities look nice on the
  command line.

**Deprecated:** None

**Removed:** None

**Fixed:** None

**Security:** None
