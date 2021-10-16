import timeit
from collections import defaultdict

l = ["one", "two", "one", "three"]


def f1():
    return [*{*l}]

def f2():
    return list(set(l))

def f3():
    return list(defaultdict.fromkeys(l))

def f4():
    return list(dict.fromkeys(l))

if __name__ == '__main__':

    print(l)
    print(f1())
    print(timeit.timeit(f1, number=1000000))
    print(f2())
    print(timeit.timeit(f2, number=1000000))
    print(f3())
    print(timeit.timeit(f3, number=1000000))
    print(f4())
    print(timeit.timeit(f4, number=1000000))
