# A quick and very messy program to evaluate set operations on intervals of continuous objects. Works on any type of
# object (in this case, floating point numbers) without requiring limits as long as they have comparison defined
# ("<", ">", "==", "<=", and ">=" operators)
# Example is located at the bottom

# Made by Tate :D
# and also credit to python.org, Stack Exchange, and GitHub Copilot

import math

inf = math.inf

UPPER_BOUND = True
LOWER_BOUND = False


class ContinuousBoundary:
    # A class to keep track of the boundaries of an interval: their value, whether they are "closed" (boundary value
    # is in set) or "open" (boundary value is not in set), and whether they correspond to an upper or lower end
    # of an interval
    def __init__(self, value, direction, is_open=False):
        self.value = value
        self.direction = direction
        self.open = is_open

    def __lt__(self, other):
        if self.value < other.value:
            return True
        if self.value == other.value:
            # are boundaries for the same value?
            # if they are both upper/lower bounds...
            if self.direction == UPPER_BOUND and other.direction == UPPER_BOUND:
                return self.open and not other.open
            elif self.direction == LOWER_BOUND and other.direction == LOWER_BOUND:
                return not self.open and other.open
            else:
                # if one is an upper bound and the other is a lower bound, then the one that is an upper bound is
                # smaller as it must correspond to an interval containing lower values
                return self.direction == UPPER_BOUND
        return False

    def __gt__(self, other):
        if self.value > other.value:
            return True
        if self.value == other.value:
            # are boundaries for the same value
            # if they are both upper/lower bounds...
            if self.direction == UPPER_BOUND and other.direction == UPPER_BOUND:
                return not self.open and other.open
            elif self.direction == LOWER_BOUND and other.direction == LOWER_BOUND:
                return self.open and not other.open
            else:
                # if one is an upper bound and the other is a lower bound, then the one that is a lower bound is larger
                return self.direction == LOWER_BOUND
        return False

    def __eq__(self, other):
        if self.direction == other.direction:
            return self.value == other.value and self.open == other.open
        return self.value == other.value and not (self.open and other.open)

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def __repr__(self):
        if self.direction == UPPER_BOUND:
            return f'{self.value}{")" if self.open else "]"}'
        return f'{"(" if self.open else "["}{self.value}'

    def __str__(self):
        # return str(self.value)
        if self.direction == UPPER_BOUND:
            return f'{self.value}{")" if self.open else "]"}'
        return f'{"(" if self.open else "["}{self.value}'

    def to_upper_bound(self):
        # turn it into the upper bound of a different interval, such that the two intervals touch but are disjoint
        return ContinuousBoundary(self.value, UPPER_BOUND, not self.open)

    def to_lower_bound(self):
        # turn it into the lower bound of a different interval, such that the two intervals touch but are disjoint
        return ContinuousBoundary(self.value, LOWER_BOUND, not self.open)


class Interval:
    # Used to keep track of ordered pairs of boundaries and also print them with correct notation (do not instantiate)
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper
        self.lower_open = lower.open
        self.upper_open = upper.open
        if lower.direction == UPPER_BOUND and upper.direction == LOWER_BOUND:
            raise ValueError('Must supply boundaries in the correct order')
        if lower >= upper and (lower.open or upper.open):
            raise ValueError('Interval is empty')

    def __repr__(self):
        if self.lower.value == -inf and self.upper.value == inf:
            return 'R'
        if self.lower.value == self.upper.value:
            return "{" + f'{self.lower.value}' + "}"
        return f'{self.lower}, {self.upper}'


class IntervalSet:
    # Main class: instantiate with some (disjoint) intervals, and keeps track of intervals covered, implementing
    # union, disjunction, and relative complement
    def __init__(self, *intervals):
        # assuming intervals are disjoint
        self.intervals = []
        for i in intervals:
            if isinstance(i, IntervalSet):
                self.intervals.extend(i.intervals)
            else:
                self.intervals.append(i)
        self.intervals.sort(key=lambda x: x.lower)

    def union(self, other):
        if isinstance(other, Interval):
            other = IntervalSet(other)
        elif type(other) is str:
            other = interval_from_string(other)
        disjoint_intervals = []
        intervals = self.intervals.copy() + other.intervals.copy()
        intervals.sort(key=lambda x: x.lower)
        current_lower = intervals[0].lower
        current_upper = intervals[0].upper
        for interval in intervals[1:]:
            if interval.lower <= current_upper:
                current_upper = max(current_upper, interval.upper)
                current_lower = min(current_lower, interval.lower)
            else:
                disjoint_intervals.append(Interval(current_lower, current_upper))
                current_lower = interval.lower
                current_upper = interval.upper
        disjoint_intervals.append(Interval(current_lower, current_upper))
        return IntervalSet(*disjoint_intervals)

    def intersection(self, other):
        if isinstance(other, Interval):
            other = IntervalSet(other)
        elif type(other) is str:
            other = interval_from_string(other)
        disjoint_intervals = []
        for interval in self.intervals:
            for other_interval in other.intervals:
                if (interval.lower <= other_interval.upper and interval.upper >= other_interval.lower) or (
                        other_interval.lower <= interval.upper and other_interval.upper >= interval.lower):
                    lower = max(interval.lower, other_interval.lower)
                    upper = min(interval.upper, other_interval.upper)
                    if lower >= upper and (lower.open or upper.open):
                        continue
                    disjoint_intervals.append(Interval(lower, upper))
        return IntervalSet(*disjoint_intervals)

    def relative_complement(self, other):
        if isinstance(other, Interval):
            other = IntervalSet(other)
        elif type(other) is str:
            other = interval_from_string(other)
        disjoint_intervals = []

        # Deal with empty sets up front b/c they mess up the loops
        if len(self.intervals) == 0:
            return IntervalSet()
        if len(other.intervals) == 0:
            return IntervalSet(*self.intervals)

        for interval in self.intervals:
            for other_interval in other.intervals:
                # if intervals overlap...
                if interval.lower <= other_interval.upper and interval.upper >= other_interval.lower:
                    # if the second interval covers the upper part of the first interval, only add the lower part
                    # that sticks out
                    if interval.lower < other_interval.lower:
                        disjoint_intervals.append(Interval(interval.lower, other_interval.lower.to_upper_bound()))
                    # similarly, if the second interval covers the lower part of the first interval, only add the
                    # upper part
                    if interval.upper > other_interval.upper:
                        disjoint_intervals.append(Interval(other_interval.upper.to_lower_bound(), interval.upper))
                    # if the second interval is completely contained in the first interval, then don't add anything
                # if intervals don't overlap at all, then just add the interval from the first set
                else:
                    disjoint_intervals.append(interval)
        return IntervalSet(*disjoint_intervals)

    def __repr__(self):
        if len(self.intervals) == 0:
            return 'Ø'
        return f'{" U ".join(map(str, self.intervals))}'

    def __add__(self, other):
        return self.union(other)

    def __sub__(self, other):
        return self.relative_complement(other)

    def __xor__(self, other):
        return self.intersection(other)


# vvv   Stuff to make syntax nicer   vvv


def interval_from_string(string):
    try_as_number = to_number(string)
    if try_as_number is not None:
        return IntervalSet(
            Interval(ContinuousBoundary(try_as_number, LOWER_BOUND, False), ContinuousBoundary(try_as_number, UPPER_BOUND, False)))
    lower, upper = string.split(',')
    lower = lower.strip()
    upper = upper.strip()
    lower_value = to_number(lower[1:])
    upper_value = to_number(upper[:-1])
    lower_open = lower[0] == '('
    upper_open = upper[-1] == ')'
    return IntervalSet(Interval(ContinuousBoundary(lower_value, LOWER_BOUND, lower_open),
                                ContinuousBoundary(upper_value, UPPER_BOUND, upper_open)))


def interval_from_tuple(tup, lower_open=False, upper_open=False):
    if len(tup) == 1:
        return IntervalSet(Interval(ContinuousBoundary(tup[0], LOWER_BOUND, False), ContinuousBoundary(tup[0], UPPER_BOUND, False)))
    return IntervalSet(
        Interval(ContinuousBoundary(tup[0], LOWER_BOUND, lower_open), ContinuousBoundary(tup[1], UPPER_BOUND, upper_open)))


def to_number(string, always_number=False):
    # TateUtils
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            if string == '∞' or string == 'oo':
                import math
                return math.inf
            if string == '-∞' or string == '-oo':
                import math
                return -math.inf
            if always_number:
                return 0
            return None


def does_overlap(lower1, upper1, lower2, upper2):
    # TateUtils (this particular function not actually used, will transfer to utils folder b/c it might be useful tho)
    return (lower1 <= upper2 and upper1 >= lower2) or (lower2 <= upper1 and upper2 >= lower1)


if __name__ == '__main__':
    A = interval_from_string('[-3, 2]')
    B = interval_from_string('(-2, 2)')
    C = interval_from_string('[0, 3)')

    # I'm a bit limited by Python syntax here, but we have "+" for union, "^" for intersection, and "-" for relative
    # complement
    # IK it's not pretty but it's the best I could figure out :(

    print(A ^ C)
    print(B ^ C)
    print(A + C)
    print(B + C)

    print(A - B)
    print(B - A)
    print(B - C)
    print(C - B)

    print(A - (B - C))
    print(A - B + C)
    print(B - (B ^ C))
    print((B - A) + (B - C))
