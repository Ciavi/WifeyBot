from dotenv import load_dotenv
from neomodel import IntegerProperty, StringProperty, DateTimeProperty, AsyncStructuredRel, \
    AsyncStructuredNode, AsyncRelationshipTo, AsyncRelationshipFrom, AsyncRelationship, config, AsyncZeroOrOne
from os import environ as env

load_dotenv()

config.DATABASE_URL = env['NEO4J_URI']

class ProperRelationship(AsyncStructuredRel):
    since = DateTimeProperty(
        default_now = True,
        index = True
    )


class User(AsyncStructuredNode):
    user_id = IntegerProperty(required=True, unique_index=True)
    user_name = StringProperty()

    partners = AsyncRelationship('User', 'IS_PARTNER_WITH', model=ProperRelationship)

    children = AsyncRelationshipTo('User', 'HAS_CHILD', model=ProperRelationship)
    parent = AsyncRelationshipFrom('User', 'IS_PARENT_OF', model=ProperRelationship, cardinality=AsyncZeroOrOne)

