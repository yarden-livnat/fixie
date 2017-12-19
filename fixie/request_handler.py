"""A request handler for fixie that expects JSON data and validates it."""

import tornado.web
import tornado.escape
import cerberus


class RequestHandler(tornado.web.RequestHandler):
    """A Tornado request handler that prepare the data by loading a
    JSON request and then validating the resultant object against
    the cerberus schema defined on the class as the 'schema' attribute.
    This class is meant to be subclassed.
    """

    @property
    def validator(self):
        v = getattr(self.__class__, '_validator', None)
        if v is None:
            v = cerberus.Validator(self.schema)
            self.__class__._validator = v
        return v

    def prepare(self):
        self.response = {}
        body = self.request.body
        if not body:
            return
        try:
            data = tornado.escape.json_decode(body)
        except ValueError:
            self.send_error(400, message='Unable to parse JSON.')
            return
        if not self.validator.validate(data):
            msg = 'Input to ' + self.__class__.__name__ + ' is not valid: '
            msg += str(self.validator.errors)
            self.send_error(400, message=msg)
            return
        self.request.arguments.clear()
        self.request.arguments.update(data)

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def write_error(self, status_code, **kwargs):
        if 'message' not in kwargs:
            if status_code == 405:
                kwargs['message'] = 'Invalid HTTP method.'
            else:
                kwargs['message'] = 'Unknown error.'
        self.response = kwargs
        self.write(kwargs)
