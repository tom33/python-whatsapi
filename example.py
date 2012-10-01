import whatsapi
import sys

class Example():

    def __init__(self):
        self.whatsapp = whatsapi.WAXMPP(user='12784612847',
            push_name='Example',
            password='abcdefgh')
        self.whatsapp.event.loginSuccess.connect(self.onLoginSuccess)
        self.whatsapp.event.groupAdd.connect(self.onGroupAdd)
        self.whatsapp.event.groupRemove.connect(self.onGroupRemove)
        self.whatsapp.event.messageReceived.connect(self.onReceived)

    def onReceived(self, msg):
        print msg
        msg = whatsapi.Message()
        msg.setData('12512512535346@s.whatsapp.net', 'Hello there')
        self.whatsapp.sendMessage(msg)

    def onLoginSuccess(self):
        print "Login succeeded"

    def onGroupAdd(self, group, who):
        print "%s added to group %s" % (who, group)

    def onGroupRemove(self, group, who):
        print "%s removed from group %s" % (who, group)

e = Example()
e.whatsapp.login()