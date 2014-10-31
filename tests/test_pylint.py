from unittest import TestCase
from os import walk
from os.path import join

class PylintTest(TestCase):
    def test_package(self):
        from pylint import epylint as lint
        errors = []
        for dirpath,_,filenames in walk('src/manuallabour'):
            for filename in filenames:
                if filename.endswith(".py"):
                    args = []
                    args.append(join(dirpath,filename))
                    args.append('--rcfile ../pylint.rc')
                    (stdout,stderr) = lint.py_run(" ".join(args),True)
                    errors.append(stderr.read())
                    errors.append(stdout.read())
        errors = "\n".join(errors).strip()
        if len(errors) > 0:
            print errors
            raise SyntaxError("PyLint has detected problems")
