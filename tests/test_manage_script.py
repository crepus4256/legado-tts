import unittest
from pathlib import Path


class ManageScriptTests(unittest.TestCase):
    def test_successful_uninstall_exits_before_menu_continues(self):
        script=(Path(__file__).parents[1]/'manage.sh').read_text(encoding='utf-8')
        function=script[script.index('uninstall(){'):script.index('while true;')]
        self.assertIn('if bash "$INSTALL_DIR/uninstall.sh" --yes; then',function)
        self.assertIn('exit 0',function)


if __name__=='__main__':unittest.main()
