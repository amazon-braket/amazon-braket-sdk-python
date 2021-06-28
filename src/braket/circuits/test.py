import inspect
class Hihi():

    @classmethod
    def __init_subclass__(cls):
        print(inspect.signature(cls.__init__))

class Hehe(Hihi):
    
    def __init__(self, bye, qubit=1, xixi=2):
        self.bye = bye
        self.qubit = qubit
        self.xixi = xixi
        print("hihi")

h = Hehe(1)

