
import json

from .packets import Header


class BytesJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            try:
                return o.decode("utf-8")
            except UnicodeDecodeError:
                return list(map(int, o))
        elif isinstance(o, Header):
            return o._attributes
        return super(BytesJSONEncoder, self).default(o)
