import unittest
import ts_minifier


class BasicParsing(unittest.TestCase):
    def test_funcCall(self):
        res = ts_minifier.parser(r'exit()')
        self.assertEqual({'exit': [0]}, res[2])

    def test_funcWithArgs(self):
        res = ts_minifier.parser(r'println("hello")')
        self.assertEqual({"println": [0]}, res[2])
        self.assertEqual([(8, 15, '"hello"')], res[0].strings)

    def test_intVar(self):
        res = ts_minifier.parser(r'x=5')
        self.assertIn(('x', "var"), res[1].items())
        self.assertIn(('x', [0]), res[2].items())

    def test_strVar(self):
        res = ts_minifier.parser(r'y="random"')
        self.assertEqual([(2, 10, '"random"')], res[0].strings)
        self.assertEqual({'y': "var"}, res[1])
        self.assertEqual({'y': [0]}, res[2])
    
    def test_multiStatement(self):
        res = ts_minifier.parser(r'y="random"print(y)')
        self.assertEqual([(2, 10, '"random"')], res[0].strings)
        self.assertEqual({'y': "var"}, res[1])
        self.assertEqual({'y': [0, 16], "print": [10]}, res[2])

    def test_comment(self):
        res = ts_minifier.parser('# hello world\n')
        self.assertEqual([(0, 14, '# hello world\n')], res[0].comments)

    def test_hexVar(self):
        res = ts_minifier.parser(r'z=0xABCDEF')
        self.assertEqual({'z': "var"}, res[1])
        self.assertEqual({'z': [0]}, res[2])


class WhitespaceTests(unittest.TestCase):
    def test_spaces(self):
        res = ts_minifier.whitespacent(r'  a   =    "hello    world"     ')
        self.assertEqual(r'a="hello    world"', res)

    def test_tabs(self):
        res = ts_minifier.whitespacent('\tb\t=\t\t"hello\tworld"\t')
        self.assertEqual('b="hello\tworld"', res)

    def test_newlines(self):
        res = ts_minifier.whitespacent('\nc\n\n=\n"hello\\n\\n\\nworld\\n"\n\n\n\n')
        self.assertEqual('c="hello\\n\\n\\nworld\\n"', res)

    def test_nodiscard(self):
        res = ts_minifier.whitespacent(r'd=6 e=7')
        self.assertEqual(r'd=6 e=7', res)

    def test_partialdiscard(self):
        res = ts_minifier.whitespacent('d=6  \n  \t \n\t\t\n  e=7')
        self.assertEqual(r'd=6 e=7', res)


class Replacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ts_minifier.auto_replace = True

    @classmethod
    def tearDownClass(cls):
        ts_minifier.auto_replace = False

    def test_stdlib_alias(self):
        parsed = ts_minifier.parser(r'print(1)print(2)print(3)print(4)')
        self.assertIn(("print", [0, 8, 16, 24]), parsed[2].items())
        smol = ts_minifier.minify(parsed[0], parsed[1], parsed[2])
        self.assertEqual("a=print a(1)a(2)a(3)a(4)", smol)

    def test_var_rename(self):
        parsed = ts_minifier.parser(r'loongname=12')
        self.assertEqual({"loongname": [0], "12": [10]}, parsed[2])
        smol = ts_minifier.minify(parsed[0], parsed[1], parsed[2])
        self.assertEqual("a=12", smol)


if __name__ == '__main__':
    unittest.main()
