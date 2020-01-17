from ariadne.asgi import GraphQL
from server.schema import schema
from starlette.middleware.cors import CORSMiddleware

# https://www.starlette.io/middleware/#corsmiddleware
# https://github.com/mirumee/ariadne/issues/104
app = CORSMiddleware(GraphQL(schema, debug=True), allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
