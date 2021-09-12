import unittest
import ts_minifier


class Parsing(unittest.TestCase):
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
        self.assertEqual(r'c="hello\n\n\nworld\n"', res)

    def test_nodiscard(self):
        res = ts_minifier.whitespacent(r'd=6 e=7')
        self.assertEqual(r'd=6 e=7', res)
        res = ts_minifier.whitespacent(r'f=10- 5 g=-6')
        self.assertEqual(r'f=10- 5 g=-6', res)

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
        smol = ts_minifier.whitespacent(smol)
        self.assertEqual("a=print a(1)a(2)a(3)a(4)", smol)

    def test_var_rename(self):
        parsed = ts_minifier.parser(r'loongname=12')
        self.assertEqual({"loongname": [0], "12": [10]}, parsed[2])
        smol = ts_minifier.minify(parsed[0], parsed[1], parsed[2])
        smol = ts_minifier.whitespacent(smol)
        self.assertEqual("a=12", smol)

    def test_str_IV(self):
        parsed = ts_minifier.parser(r'print("hello world\n"+"hello world\n")')
        self.assertEqual([(6, 21, r'"hello world\n"'), (22, 37, r'"hello world\n"')], parsed[0].strings)
        smol = ts_minifier.minify(parsed[0], parsed[1], parsed[2])
        smol = ts_minifier.whitespacent(smol)
        self.assertEqual(r'a="hello world\n"print(a+a)', smol)

    def test_int_IV(self):
        parsed = ts_minifier.parser(r'print(250+250+250+250)')
        self.assertEqual({"print": [0], "250": [6, 10, 14, 18]}, parsed[2])
        smol = ts_minifier.minify(parsed[0], parsed[1], parsed[2])
        smol = ts_minifier.whitespacent(smol)
        self.assertEqual(r'a=250 print(a+a+a+a)', smol)

    def test_stdlib_var_result(self):
        subcases = [(r'a=pause()b=a.volminus', r'a=pause()b=a.volminus'),
                    (r'longername=pause()langley=a.volminus', r'b=pause()c=a.volminus'),
                    (r'a=readdir()a.files.foreach()', r'a=readdir()a.files.foreach()')]
        for script in subcases:
            with self.subTest(script=script):
                parsed = ts_minifier.parser(script[0])
                smol = ts_minifier.minify(parsed[0], parsed[1], parsed[2])
                smol = ts_minifier.whitespacent(smol)
                self.assertEqual(script[1], smol)

    # making this work without making stdlib_var_result fail is the real issue here
    @unittest.expectedFailure
    def test_user_member_var(self):
        parsed = ts_minifier.parser(r'a=dict()a.othername=3')
        smol = ts_minifier.minify(parsed[0], parsed[1], parsed[2])
        smol = ts_minifier.whitespacent(smol)
        self.assertEqual(r'a=dict()a.b=3', smol)


if __name__ == '__main__':
    unittest.main()
