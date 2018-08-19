import math
import operator
import random
from collections import namedtuple
from functools import reduce


class ConfigurationFinder:
    """
    The ConfigurationFinder class can construct randomly generated score functions and
    test them against synthetic paths. A genetic algorithm can be used to find children
    of the randomly generated score functions until a suitably fit child is found.
    """
    def __init__(self, configuration_template, mm):
        """
        :param configuration_template: A tuple specifying each function type as a string.
                                       example: ('manipulation', 'manipulation', 'value', 'combiner')
        :param mm: A map matching object.
        """
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

    def score_path(self, candidate, key):
        """
        Given a candidate path and it's solution, give the candidate path a score.
        If d := the length of the longer of the two paths, the score is given by (d - edit_distance) / d.
        """
        def levenshtein_distance(s, t):
            """
            Computes the Levenshtein distance between two paths.
            """
            # distance_matrix is a len(s) x len(t) sized matrix.
            distance_matrix = [[0] * len(t) for _ in range(len(s))]

            for index, section in enumerate(s):
                # The distance between the first k sections of s and an empty path is k.
                distance_matrix[index][0] = index

            for index, section in enumerate(t):
                # The distance between the first k sections to t and an empty path is k.
                distance_matrix[0][index] = index

            for t_index in range(len(t)):
                for s_index in range(len(s)):
                    if s[s_index] == t[t_index]:  # If the paths are the same, no operation is required.
                        distance_matrix[s_index][t_index] = distance_matrix[s_index - 1][t_index - 1]
                    else:  # Otherwise, the paths are not the same so an operation is required.
                        minimum_neighbour = min(
                            distance_matrix[s_index - 1][t_index],  # Delete
                            distance_matrix[s_index][t_index - 1],  # Insert
                            distance_matrix[s_index - 1][t_index - 1])  # Substitute

                        distance_matrix[s_index][t_index] = minimum_neighbour + 1

            return distance_matrix[-1][-1]

        candidate_as_sections = self.mm.network.to_sections(candidate)
        key_as_sections = self.mm.network.to_sections(key)

        edit_distance = levenshtein_distance(candidate_as_sections, key_as_sections)

        maximum_path_distance = max(len(candidate_as_sections), len(key_as_sections))

        return (maximum_path_distance - edit_distance) / maximum_path_distance

    def new_fn_builder(self, configuration, complexity, r, previous_function=None):
        """
        Constructs a random new function.
        :param configuration: The type of function to be constructed.
        :param complexity: The number of levels of nesting in the function.
        :param r: A collection of numbers. Arguments are selected from this value.
        :param previous_function: Used for adding complexity, do not change unless you know what you are doing.
        :return:
        """
        if not self.factory_mappings[configuration].outer:  # Function does not chain, so select base fn and return.
            factory_option = random.choice(self.factory_mappings[configuration].inner)
            number_option = random.choice(r)
            return self.configuration(factory_option.fn(number_option),
                                      '{0}({1})'.format(factory_option.name, number_option), 0)
        elif not previous_function:  # First entry, so randomly select base fn and recurse.
            factory_option = random.choice(self.factory_mappings[configuration].inner)
            number_option = random.choice(r)
            new_fn = self.configuration(factory_option.fn(number_option),
                                        '{0}({1})'.format(factory_option.name, number_option), 0)
        elif complexity <= 0:  # Construction is finished, so return the fn.
            return previous_function
        else:  # Otherwise continue to chain functions.
            factory_option = random.choice(self.factory_mappings[configuration].outer)
            number_option = random.choice(r)
            new_fn = self.configuration(
                factory_option.fn(previous_function.fn, number_option),
                '{0}({1},{2})'.format(factory_option.name, previous_function.as_text, number_option), 0)
        return self.new_fn_builder(configuration, complexity - 1, r, new_fn)

    def child_fn_builder(self, existing_fn, k = 3, include_parent = True):
        """
        Given an existing function, return k children of that function.
        :param existing_fn: A function wrapped in a configuration named tuple.
        :param k: The number of offspring.
        :param include_parent: Whether or not the parent value should be preserved.
        :return:
        """
        pass

    def build_configuration(self, complexity=3, r=[i * .1 for i in range(-100, 100)]):
        """
        Construct a new random function for each function requested in the configuration template.
        :param complexity:
        :param r:
        :return:
        """
        return (self.new_fn_builder(configuration, complexity, r) for configuration in self.configuration_template)




def test():
    value_config = ['value']
    manip_config = ['manipulation']
    combiner_config = ['reduction']

    def fakemm():
        return

    fakemm.network = []

    test.v = ConfigurationFinder(value_config, fakemm)
    test.m = ConfigurationFinder(manip_config, fakemm)
    test.c = ConfigurationFinder(combiner_config, fakemm)

    test.v_result = list(v.build_configuration(complexity=5))
    test.m_result = list(m.build_configuration(complexity=5))
    test.c_result = list(c.build_configuration(complexity=5))

test()
