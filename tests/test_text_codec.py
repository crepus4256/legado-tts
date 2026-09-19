import unittest
from urllib.parse import parse_qs

from app.text_codec import decode_text


class TextCodecTests(unittest.TestCase):
    def test_double_encoded_form_space_is_restored(self):
        self.assertEqual(decode_text('\u4f60\u597d+\u4e16\u754c',form_encoded=True),'\u4f60\u597d \u4e16\u754c')

    def test_double_encoded_literal_plus_is_preserved(self):
        self.assertEqual(decode_text('C%2B%2B+and+1%2B1',form_encoded=True),'C++ and 1+1')

    def test_percent_encoded_web_preview_remains_supported(self):
        self.assertEqual(decode_text('hello%20world'),'hello world')

    def test_plain_plus_from_get_request_is_preserved(self):
        self.assertEqual(decode_text('C++'),'C++')

    def test_legado_double_encoded_form_round_trip(self):
        parsed=parse_qs('tex=hello%2Bworld%2BC%252B%252B')['tex'][0]
        self.assertEqual(decode_text(parsed,form_encoded=True),'hello world C++')


if __name__=='__main__':unittest.main()
