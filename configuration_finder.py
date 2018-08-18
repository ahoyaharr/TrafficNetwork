import math
import operator
import random
from collections import namedtuple
from functools import reduce


class ConfigurationFinder:
    def __init__(self, configuration_template, mm):
        self.function_factory = namedtuple('function_factory', ['outer', 'inner'])
        self.component_fn = namedtuple('component_fn', ['fn', 'name'])
        self.configuration = namedtuple('configuration', ['fn', 'as_text', 'age'])

        self.best_configurations = []
        self.generation_count = 0
        self.mm = mm
        self.network = mm.network
        self.configuration_template = configuration_template

        # direct mappings. usage: direct_mapping(numbers) -> number
        self.direct_mappings = [self.component_fn(lambda r: r, 'direct_value_id')]

        # inner functions. map one value to one value.
        # usage: inner_fn(arg) -> some_fn. some_fn(another_arg) -> number
        self.value_manipulation = [
            self.component_fn(
                lambda internal_value: lambda input_value: input_value + internal_value,
                'inner_add'),
            self.component_fn(
                lambda internal_value: lambda input_value: input_value * internal_value,
                'inner_mul'),
            self.component_fn(
                lambda internal_value: lambda input_value: input_value ** internal_value,
                'inner_pow'),
            self.component_fn(
                lambda internal_value: lambda input_value: math.log(internal_value + input_value, internal_value),
                'inner_log')
        ]

        # outer functions. map one value to one value.
        # usage: outer_fn(some_fn, arg) -> some_other_fn. some_other_fn(another_arg) -> number
        self.math_options = [
            self.component_fn(
                lambda inner_fn, arg1: lambda arg2: 1 + math.cos(math.radians(inner_fn(arg1))),
                'cosine_similarity'),
            self.component_fn(
                lambda inner_fn, arg1: lambda arg2: arg2 / (math.log(math.e + inner_fn(arg1))),
                'log_inverse'),
            self.component_fn(
                lambda inner_fn, arg1: lambda arg2: inner_fn(arg1),
                'id')
        ]

        # reduction functions. map many values to one value.
        self.combiner_options = [self.component_fn(lambda l: lambda l: reduce(operator.add, l, 0), 'add_combine'),
                                 self.component_fn(lambda l: lambda l: reduce(operator.mul, l, 1), 'mul_combine')]

        self.factory_mappings = {'value': self.function_factory(None, self.direct_mappings),
                                 'manipulation': self.function_factory(self.math_options, self.value_manipulation),
                                 'reduction': self.function_factory(None, self.combiner_options)}

    def fn_builder(self, configuration, complexity, r, previous_function=None):
        if not self.factory_mappings[configuration].outer:  # Function does not chain, so select base fn and return.
            factory_option = random.choice(self.factory_mappings[configuration].inner)
            number_option = random.choice(r)
            return self.configuration(factory_option.fn(number_option), '{0}({1})'.format(factory_option.name, number_option), 0)
        elif not previous_function:  # First entry, so randomly select base fn and recurse.
            factory_option = random.choice(self.factory_mappings[configuration].inner)
            number_option = random.choice(r)
            new_fn = self.configuration(factory_option.fn(number_option), '{0}({1})'.format(factory_option.name, number_option), 0)
        elif complexity <= 0:  # Construction is finished, so return the fn.
            return previous_function
        else:  # Otherwise continue to chain functions.
            factory_option = random.choice(self.factory_mappings[configuration].outer)
            number_option = random.choice(r)
            new_fn = self.configuration(
                factory_option.fn(previous_function.fn, number_option),
                '{0}({1},{2})'.format(factory_option.name, previous_function.as_text, number_option), 0)
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

v_result = list(v.build_configuration(complexity=5))
m_result = list(m.build_configuration(complexity=5))
c_result = list(c.build_configuration(complexity=5))
