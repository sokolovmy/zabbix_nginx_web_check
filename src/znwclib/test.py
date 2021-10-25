class TestClass:
    def __init__(self):
        self.p1 = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0')
        self.p2 = 'qwertyuuiop'
        pass

    def gen(self, s):
        s = self.p1 if s else self.p2
        for c in s:
            yield c

    def printTest(self):
        for g1 in self.gen(True):
            for g2 in self.gen(False):
                print(f"g1={g1}, g2={g2}")


if __name__ == '__main__':
    tc = TestClass()
    tc.printTest()