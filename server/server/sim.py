
# import IPython
import numpy as np
import random
from PIL import Image
from math import floor, ceil

from types import MethodType

from collections import Counter

def most_common(lst):
    data = Counter(lst)
    return max(lst, key=data.get)


NO_VALUE = 0
YES_VALUE = 255


class Default:
    pass


class Space:
    def __init__(self, width, height, default, d={}):
        self.width = width
        self.height = height
        self.default = default
        self.ignore = []
        self.dict = {**d}

    def set(self, x, y, value):
        self.dict[(x, y)] = value

    def clone(self):
        return self.__class__(self.width, self.height, self.default, self.dict)

    def get(self, x, y, default=Default):
        if default == Default:
            default = self.default
        return self.dict.get((x, y), self.default)

    def apply_changes(self, changes):
        self.dict.update(changes)

    def filter_selection(self, sel):
        changes = {}
        if sel:
            for pos, value in self.dict.items():
                if value in sel:
                    changes[pos] = value
            return Space(
                width=self.width,
                height=self.height,
                default=self.default,
                d=changes,
            )
        else:
            return Space(
                width=1,
                height=1,
                default=self.default,
            )

    def set_all_to(self, value):
        self.dict = {
            pos: value for pos, _ in self.dict.items()
        }

    def to_str(self):
        return '\n'.join(
            ' '.join(str(self.get(x, y)) for x in range(self.width))
            for y in range(self.height)
        )

    def to_arr(self):
        return [
            [self.get(x, y) for x in range(self.width)]
            for y in range(self.height)
        ]

    def to_img(self):
        return Image.fromarray(np.array(self.to_arr(), np.uint8))

    @property
    def ignore_json(self):
        return self.ignore

    def to_json(self):
        return {
            "width": self.width,
            "height": self.height,
            "default": self.default,
            "ignore": self.ignore_json,
            "cells": {
                ','.join(str(a) for a in position): value
                for position, value in self.dict.items()
            }
        }

    def random_position(self):
        return random.randrange(self.width), random.randrange(self.height)

    def random_occupied_position(self):
        return random.choice(list(self.dict.keys()))


def boundaries(space, rules, size=1):
    s = size - 1
    arr = []
    for x in range(space.width):
        for y in range(space.height):
            if len(Counter(moore(
                rules=rules,
                space=space,
                x=x,
                y=y,
            ))) > 1:
                for dx in range(x-s, x+s+1):
                    for dy in range(y-s, y+s+1):
                        arr.append((dx, dy))
    return arr


def boundaries_space(space, rules, no_value=NO_VALUE, yes_value=YES_VALUE, size=1):
    s = Space(width=space.width, height=space.height, default=no_value)
    for x, y in boundaries(space=space, rules=rules, size=size):
        s.set(x, y, yes_value)
    return s


def selection_set(selection):
    return set(value_from_json(v) for v in selection)


def value_from_json(value):
    if type(value) is list:
        return tuple(value)


def from_json(json):
    d = {}
    for position, value in json['cells'].items():
        d[tuple(int(a) for a in position.split(','))] = value_from_json(value)
    s = Space(
        width=json['width'],
        height=json['height'],
        default=value_from_json(json['default']),
        d=d,
    )
    s.ignore = [value_from_json(v) for v in json["ignore"]]
    print(s.ignore)
    return s


class SpaceChange:
    def __init__(self, old_space: Space, changes={}, can_change=True):
        self.old_space: Space = old_space
        self.changes = changes
        self.can_change = can_change
        self.new_space_ = None

    @property
    def new_space(self):
        if not self.new_space_:
            self.new_space_ = Space(
                width=self.old_space.width,
                height=self.old_space.height,
                default=self.old_space.default,
                d={
                    **self.old_space.dict,
                    **self.changes
                }
            )
            self.new_space_.ignore = self.old_space.ignore
        return self.new_space_


class GeneralRules:
    def clear_neighbour(self, values, ignore):
        return [a for a in values if a not in ignore]

    def get(space, x, y):
        raise NotImplementedError()


class Rules(GeneralRules):
    def neighbour(space, x, y):
        raise NotImplementedError()

    def step(self, space):
        ignore = self.ignore + space.ignore
        can_change = False
        changes = {}
        for x in range(space.width):
            for y in range(space.height):
                if self.get(space, x, y) in self.empty:
                    neighbour = [a for a in self.neighbour(self, space, x, y)  if a not in ignore]
                    if neighbour:
                        a = most_common(neighbour)
                        changes[(x, y)] = a
                        can_change = True
        return SpaceChange(
            old_space=space,
            changes=changes,
            can_change=can_change,
        )


class AdvancedRules(GeneralRules):
    def step(self, space):
        ignore = self.ignore + space.ignore
        can_change = False
        changes = {}
        for x in range(space.width):
            for y in range(space.height):
                if self.get(space, x, y) not in self.empty:
                    continue
                n2 = self.clear_neighbour(nearest_moore(self, space, x, y), ignore)
                n3 = self.clear_neighbour(further_moore(self, space, x, y), ignore)
                n1 = n2 + n3
                if n1:
                    can_change = True
                else:
                    continue

                # Rule 1
                value1, count1 = Counter(n1).most_common(1)[0]
                if count1 >= 5:
                    changes[(x, y)] = value1
                    continue
                # Rule 2
                if n2:
                    value2, count2 = Counter(n2).most_common(1)[0]
                    if count2 >= 3:
                        changes[(x, y)] = value2
                        continue
                # Rule 3
                if n3:
                    value3, count3 = Counter(n3).most_common(1)[0]
                    if count3 >= 3:
                        changes[(x, y)] = value3
                        continue
                # Rule 4
                if random.randrange(100) < self.advanced_probability:
                    changes[(x, y)] = value1
                    continue
        return SpaceChange(
            old_space=space,
            changes=changes,
            can_change=can_change,
        )


def absorbing_get(space, x, y):
    return space.get(x, y)


def repeating_get(space, x, y):
    x = x % space.width
    y = y % space.height
    return space.get(x, y)


def gen_neighborhood(cells):
    def n(rules, space, x, y):
        arr = []
        for cell in cells[random.randrange(len(cells))]:
            dx, dy = cell
            arr.append(rules.get(space, x+dx, y+dy))
        return arr
    return n


nearest_moore = von_neumann_neighbour = gen_neighborhood([
    [
        [-1, 0],
        [0, -1],
        [1, 0],
        [0, 1],
    ]
])

moore = gen_neighborhood([
    [
        [-1, -1],
        [-1, 0],
        [-1, 1],
        [0, -1],
        [0, 1],
        [1, -1],
        [1, 0],
        [1, 1],
    ]
])

further_moore = gen_neighborhood([
    [
        [-1, -1],
        [1, 1],
        [1, -1],
        [-1, 1],
    ]
])


def from_str(s, default='.'):
    width = len(s.split('\n')[0].replace(' ', ''))
    height = len(s.split('\n'))
    space = Space(width, height, default)
    for y, line in enumerate(s.split('\n')):
        for x, char in enumerate(line.replace(' ', '')):
            space.set(x, y, char)
    return space


def seed(space, count, gen):
    for i in range(count):
        for i in range(100):
            x, y = random.randrange(space.width), random.randrange(space.height)
            if (x, y) not in space.dict:
                space.set(x, y, gen())
                break


def seed_square(space, gen, count, size, value):
    for i in range(count):
        x0, y0 = gen()
        for x in range(x0, x0+size):
            for y in range(y0, y0+size):
                space.set(x, y, value)
    return space


def seed_circle(space, gen, count, size, value):
    r2 = (size/2)**2
    for i in range(count):
        x0, y0 = gen()
        for x in range(floor(x0-size/2), ceil(x0+size/2)):
            for y in range(floor(y0-size/2), ceil(y0+size/2)):
                if (x-x0)**2 + (y-y0)**2 <= r2:
                    space.set(x, y, value)
    return space


def get_borders(space):
    for x in range(space.width):
        for y in range(space.height):
            if len(Counter([
                space.get(x-1, y),
                space.get(x, y-1),
                space.get(x+1, y),
                space.get(x, y+1),
            ])) > 1:
                space.set(x, y, 255)

