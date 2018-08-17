from itertools import groupby
from functools import reduce
from collections import namedtuple
import operator
import math
import random


class ConfigurationFinder:
    def __init__(self, configuration_template, mm):
        self.best_configurations = []
        self.generation_count = 0
        self.mm = mm
        self.network = mm.network
        self.configuration_template = configuration_template

        # direct mappings. usage: direct_mapping(numbers) -> number
        self.direct_mappings = [lambda r: r]

        # inner functions. map one value to one value.
        # usage: inner_fn(arg) -> some_fn. some_fn(another_arg) -> number
        self.value_manipulation = [lambda internal_value: lambda input_value: input_value + internal_value,
                                   lambda internal_value: lambda input_value: input_value * internal_value,
                                   lambda internal_value: lambda input_value: input_value ** internal_value,
                                   lambda internal_value: lambda input_value: math.log(internal_value + input_value, internal_value)]

        # outer functions. map one value to one value.
        # usage: outer_fn(some_fn, arg) -> some_other_fn. some_other_fn(another_arg) -> number
        self.math_options = [lambda inner_fn, arg1: lambda arg2: 1 + math.cos(math.radians(inner_fn(arg1))),
                             lambda inner_fn, arg1: lambda arg2: arg2 / (math.log(math.e + inner_fn(arg1))),
                             lambda inner_fn, arg1: lambda arg2: inner_fn(arg1)]

        # reduction functions. map many values to one value.
        self.combiner_options = [lambda l: lambda l: reduce(operator.add, l, 0),
                                 lambda l: lambda l: reduce(operator.mul, l, 1)]

        function_factory = namedtuple('function_factory', ['outer', 'inner'])

        self.factory_mappings = {'value': function_factory(None, self.direct_mappings),
                                 'manipulation': function_factory(self.math_options, self.value_manipulation),
                                 'reduction': function_factory(None, self.combiner_options)}

    def fn_builder(self, configuration, complexity, r, previous_function=None):
        if not self.factory_mappings[configuration].outer:  # Function does not chain, so select base fn and return.
            return random.choice(self.factory_mappings[configuration].inner)(random.choice(r))
        elif not previous_function:  # First entry, so randomly select base fn and recurse.
            new_fn = random.choice(self.factory_mappings[configuration].inner)(random.choice(r))
        elif complexity <= 0:  # Construction is finished, so return the fn.
            return previous_function
        else:  #  Otherwise continue to chain functions.
            new_fn = random.choice(self.factory_mappings[configuration].outer)(previous_function, random.choice(r))
        return self.fn_builder(configuration, complexity - 1, r, new_fn)

    def build_configuration(self, complexity=3, r=[i * .1 for i in range(-100, 100)]):
        return (self.fn_builder(configuration, complexity, r) for configuration in self.configuration_template)


value_config = ['value']
manip_config = ['manipulation']
combiner_config = ['reduction']

def fakemm():
    return

fakemm.network = []

v = ConfigurationFinder(value_config, fakemm)
m = ConfigurationFinder(manip_config, fakemm)
c = ConfigurationFinder(combiner_config, fakemm)

v_result = list(v.build_configuration())
m_result = list(m.build_configuration())
c_result = list(c.build_configuration())