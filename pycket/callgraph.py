from rpython.rlib import jit
from pycket       import config

class CallGraph(object):
    def __init__(self):
        self.calls     = {}
        self.recursive = {}

    def register_call(self, lam, calling_app, cont):
        if jit.we_are_jitted():
            return
        if not calling_app:
            return
        calling_lam = calling_app.surrounding_lambda
        if not calling_lam:
            return
        subdct = self.calls.get(calling_lam, None)
        if subdct is None:
            self.calls[calling_lam] = subdct = {}
        cont_ast = cont.get_next_executed_ast()
        if lam not in subdct:
            subdct[lam] = None
            if self.is_recursive(calling_lam, lam):
                calling_lam.enable_jitting()
        # It is possible to have multiple consuming continuations for a given
        # function body. This will attempt to mark them all.
        same_lambda = cont_ast and cont_ast.surrounding_lambda is calling_lam
        if same_lambda and self.is_recursive(calling_lam, lam):
            if cont_ast.set_should_enter() and config.log_callgraph:
                print "jitting downrecursion", cont_ast.tostring()

    def is_recursive(self, lam, starting_from=None):
        # quatratic in theory, hopefully not very bad in practice
        visited = {}
        if starting_from is None:
            starting_from = lam
        if (lam, starting_from) in self.recursive:
            return True
        todo = self.calls.get(starting_from, {}).keys()
        while todo:
            current = todo.pop()
            if current is lam:
                self.recursive[(lam, starting_from)] = None
                return True
            if current in visited:
                continue
            todo.extend(self.calls.get(current, {}).keys())
            visited[current] = None
        return False
