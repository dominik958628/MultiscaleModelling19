# https://ariadnegraphql.org/
import io
import base64
import asyncio
import time
import random
from io import BytesIO

from PIL import Image

from ariadne import QueryType, SubscriptionType, ObjectType, gql
from ariadne import make_executable_schema
from ariadne import upload_scalar

from server.sim import Rules, absorbing_get, von_neumann_neighbour, Space, seed, seed_square, gen_neighborhood, repeating_get, AdvancedRules, SpaceChange, from_json, seed_circle, boundaries_space, selection_set

MIN_STEP_TIME = 0

type_defs = gql(open('schema.graphql').read())

query = QueryType()


@query.field('hello')
def resolve_hello(_, info):
    return "Hello..."


default_value = (40, 40, 40)
inclusion_value = (0, 0, 0)
phase_value = (255, 0, 0)
range1 = 50
range2 = 250


NULL_SPACE = Space(width=1, height=1, default=default_value)


def gen_inclusion_value():
    return (random.randrange(range1, range2), random.randrange(range1, range2), random.randrange(range1, range2))


@query.field("toggleSelection")
def resolve_toggle_selection(_, info, spaceJson: dict, selection: list, x: int, y: int):
    space = from_json(spaceJson)
    value = space.get(x, y)
    if value != space.default:
        if type(value) is tuple:
            value = list(value)
        if value in selection:
            selection.remove(value)
        else:
            selection.append(value)
    return selection


@query.field("randomSelection")
def resolve_toggle_selection(_, info, spaceJson: dict, size: int):
    space = from_json(spaceJson)

    pop = set(space.dict.values()) - set(space.ignore + [default_value, inclusion_value, phase_value])

    return list(random.choices(population=list(pop), k=size))


@query.field("spaceFromFile")
def resolve_spaceFromFile(_, info, file):
    # print(file)
    # print(type(file))
    _, b64 = file.split(',', 1)
    b = base64.b64decode(b64)
    # https://stackoverflow.com/a/38981166
    # https://stackoverflow.com/a/32908899
    im = Image.open(BytesIO(b))
    px = im.load()
    d = {}
    width, height = im.size
    for x in range(width):
        for y in range(height):
            value = px[x, y]
            if value is not default_value:
                d[(x, y)] = value
    return Space(
        width=width,
        height=height,
        default=default_value,
        d=d,
    )


@query.field("returnSpace")
def resolve_return_space(_, info, spaceJson: dict):
    return from_json(spaceJson)


@query.field("spaceToInclusions")
def resolve_spaceToInclusions(_, info, spaceJson: dict):
    space = from_json(spaceJson)
    space.set_all_to(phase_value)
    space.ignore = [phase_value]
    return space


@query.field("addNucleons")
def resolve_addNucleons(_, info, spaceJson: dict, count: int):
    space = from_json(spaceJson)
    seed(space, count=count, gen=gen_inclusion_value)
    return space


@query.field('generateSpace')
def resolve_generate_space(_, info, width: int, height: int, nucleons: int = 0):
    space = Space(width, height, default=default_value)
    seed(space, count=nucleons, gen=gen_inclusion_value)
    return space


inclusions = {
    "square": seed_square,
    "circle": seed_circle,
}


@query.field('addInclusions')
def resolve_add_inclusions(_, info, spaceJson: dict, type_: str, count: int,  size: int, onBoundary=False, rules: dict = None):
    space = from_json(spaceJson)
    if onBoundary:
        b = boundaries_space(space, rules=get_rules(rules))
        gen = b.random_occupied_position
    else:
        gen = space.random_position
    return inclusions[type_](space, gen, count, size, inclusion_value)


def get_rules(rulesJson: dict):
    cells = rulesJson['cells']
    edge = rulesJson['edge']
    rulesType = rulesJson['rulesType']
    advancedProbability = rulesJson['advancedProbability']

    if rulesType == "advanced":
        rules = AdvancedRules()
        rules.advanced_probability = advancedProbability
    elif rulesType == "normal":
        rules = Rules()
        if cells:
            rules.neighbour = gen_neighborhood(cells)
        else:
            rules.neighbour = von_neumann_neighbour
    else:
        raise NotImplementedError('rulesType must be advanced/normal')

    rules.ignore = [default_value, inclusion_value]
    rules.empty = [default_value]
    rules.get = edges[edge]

    return rules


@query.field('step')
def resolve_step(_, info, spaceJson: dict, rules: dict):
    rules = get_rules(rules)
    return rules.step(from_json(spaceJson))


subscription = SubscriptionType()


@subscription.source('counter')
async def counter_generator(obj, info, add=0):
    for i in range(1, 10):
        await asyncio.sleep(1)
        yield i


@subscription.field('counter')
def counter_resolver(count, info, add=0):
    return count * 10 + add


edges = {
    'absorbing': absorbing_get,
    'repeating': repeating_get,
}


space = ObjectType("Space")


@space.field("str")
def resolve_str(obj: Space, info):
    return obj.to_str()


@space.field("dataUrl")
def resolve_data_url(obj: Space, info):
    img = obj.to_img()
    output = io.BytesIO()
    img.save(output, format="BMP")
    contents = output.getvalue()
    b64 = base64.b64encode(contents)
    return f"data:image/png;base64,{b64.decode('ascii')}"


@space.field("json")
def resolve_json(obj: Space, info):
    return obj.to_json()


@space.field("percentage")
def resolve_json(obj: Space, info):
    return '{0:.2f} %'.format(len(obj.dict) / (obj.width * obj.height))


@space.field("boundaries")
def resolve_boundaries(obj: Space, info, rules: dict, generate=False, size=1):
    if generate:
        return boundaries_space(
            space=obj,
            rules=get_rules(rules),
            no_value=default_value,
            yes_value=inclusion_value,
            size=size,
        )
    else:
        return NULL_SPACE


@space.field("selectedSpace")
def resolve_boundaries(obj: Space, info, selection: list):
    sel = selection_set(selection)
    s = obj.filter_selection(sel)
    s.ignore = list(sel)
    return s


space_change = ObjectType("SpaceChange")


@space_change.field("newSpace")
def resolve_new_space(obj: SpaceChange, info):
    return obj.new_space


@space_change.field("changes")
def resolve_can_change(obj: SpaceChange, info):
    return obj.changes


@space_change.field("canChange")
def resolve_can_change(obj: SpaceChange, info):
    return obj.can_change


schema = make_executable_schema(type_defs, [query, subscription, space, space_change, upload_scalar])
