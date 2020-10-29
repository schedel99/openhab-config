from shared.helper import rule
from core.triggers import CronTrigger

@rule("_test.py")
class TestRule:
    def __init__(self):
        self.triggers = [CronTrigger("0 */30 * * * ?")]

    def execute(self, module, input):
        self.log.info("test rule triggered")
