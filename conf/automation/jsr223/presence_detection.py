from custom.helper import log, rule, getItemState, sendNotification
from core.triggers import ItemStateChangeTrigger


@rule("presence_detection.py")
class PresenceCheckRule:
    def __init__(self):
        self.triggers = [
            ItemStateChangeTrigger("State_Markus_Presence"),
            ItemStateChangeTrigger("State_Dani_Presence")
        ]
        
    def execute(self, module, input):
        itemName = input['event'].getItemName()
        itemState = input['event'].getItemState()
        
        sendNotification(u"{}".format(itemName), u"{}".format(itemState))
