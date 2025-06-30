from datetime import datetime
from dotenv import load_dotenv
from neomodel import IntegerProperty, StringProperty, DateTimeProperty, AsyncStructuredRel, \
    AsyncStructuredNode, AsyncRelationshipTo, AsyncRelationshipFrom, AsyncRelationship, config
from os import environ as env

load_dotenv()

config.DATABASE_URL = env['NEO4J_URI']

class ProperRelationship(AsyncStructuredRel):
    since = DateTimeProperty(
        default = lambda : datetime.now(),
        index = True
    )


class User(AsyncStructuredNode):
    user_id = IntegerProperty(required=True, unique_index=True)
    user_name = StringProperty()

    partners = AsyncRelationship('User', 'PARTNER', model=ProperRelationship)

    children = AsyncRelationshipTo('User', 'CHILD', model=ProperRelationship)
    parent = AsyncRelationshipFrom('User', 'CHILD', model=ProperRelationship)

