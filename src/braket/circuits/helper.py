import ast
from _ast import ClassDef
from functools import lru_cache


# Define a visitor class to extract class names
class ClassNameVisitor(ast.NodeVisitor):
    def __init__(self):
        self.class_names = []

    def visit_ClassDef(self, node: ClassDef):
        self.class_names.append(node.name)
        self.generic_visit(node)


def get_class_names_from_file(file_path):
    with open(file_path, "r") as file:
        file_contents = file.read()

    # Parse the python code into an AST
    ast_tree = ast.parse(file_contents)

    # Traverse the AST and extract class names
    class_name_visitor = ClassNameVisitor()
    class_name_visitor.visit(ast_tree)

    return class_name_visitor.class_names


# Function to get all subclasses of a class
@lru_cache
def fetch_subclasses(BaseClass):
    return BaseClass.__subclasses__()


@lru_cache
def fetch_subclasses_names(BaseClass):
    return [sub.__name__ for sub in fetch_subclasses(BaseClass)]


@lru_cache
def fetch_subclass(BaseClass, subclass_name):
    for sub in fetch_subclass(BaseClass):
        if sub.__name__.lower() == subclass_name.lower():
            return sub
