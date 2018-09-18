import ast


class NodeCounter(ast.NodeVisitor):
    def __init__(self):
        self.count = 0

    def generic_visit(self, node):
        self.count += 1
        super().generic_visit(node)
