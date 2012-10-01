#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2012, Tarek Galal <tarek@wazapp.im>
Modified by Bouke van der Bijl <boukevanderbijl@gmail.com>

This file is part of Wazapp, an IM application for Meego Harmattan platform that
allows communication with Whatsapp users

Wazapp is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 2 of the License, or (at your option) any later
version.

Wazapp is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
Wazapp. If not, see http://www.gnu.org/licenses/.
'''

import time
import threading
import select
import sys

from whatsapi.utilities import S40MD5Digest
from whatsapi.protocoltreenode import BinTreeNodeWriter, BinTreeNodeReader, \
    ProtocolTreeNode
from whatsapi.connengine import MySocketConnection
from whatsapi.login import Login

from whatsapi.message import Message
from whatsapi.exceptions import *
from whatsapi.signalslot import Signal


class WAEventHandler(object):

    def __init__(self, conn):
        self.connecting = Signal()
        self.connected = Signal()
        self.sleeping = Signal()
        self.disconnected = Signal()
        self.reconnecting = Signal()

        '''(remote)'''
        self.typing = Signal()
        '''(remote)'''
        self.typingPaused = Signal()


        '''(remote)'''
        self.available = Signal()
        '''(remote)'''
        self.unavailable = Signal()

        self.messageSent = Signal()

        self.messageDelivered = Signal()

        '''(fmsg)'''
        self.messageReceived = Signal()
        '''messageReceived with fmsg.author'''
        self.groupMessageReceived = Signal()


        '''
        (fmsg)
        -> media_type: image, audio, video, location, vcard
        -> data
            image:
            -> url
            -> preview
            audio, video:
            -> url
            location:
            -> latitude
            -> longitude
            -> preview
            vcard:
            -> contact (vcard format)
        '''
        self.mediaReceived = Signal()

        '''mediaReceived with fmsg.author'''
        self.groupMediaReceived = Signal()

        '''(group, author, subject)'''
        self.newGroupSubject = Signal()

        '''(group, who)'''
        self.groupAdd = Signal()

        '''(group, who)'''
        self.groupRemove = Signal()

        self.groupListReceived = Signal()

        self.lastSeenUpdated = Signal()

        self.sendTyping = Signal()
        self.sendPaused = Signal()
        self.getLastOnline = Signal()

        self.disconnectRequested = Signal()
        self.disconnectRequested.connect(self.onDisconnectRequested)

        self.loginFailed = Signal()
        self.loginSuccess = Signal()
        self.connectionError = Signal()
        self.conn = conn

        self.sendTyping.connect(self.conn.sendTyping)
        self.sendPaused.connect(self.conn.sendPaused)
        self.getLastOnline.connect(self.conn.getLastOnline)

        self.startPingTimer()

    def onDirty(self, categories):
        '''Receive groups??'''
        pass

    def onAccountChanged(self, account_kind, expire):
        pass

    def onRelayRequest(
        self,
        pin,
        timeoutSeconds,
        idx,
        ):
        pass

    def sendPing(self):
        self.startPingTimer()
        self.conn.sendPing()

    def startPingTimer(self):
        self.pingTimer = threading.Timer(180, self.sendPing)
        self.pingTimer.start()

    def onDisconnectRequested(self):
        self.pingTimer.cancel()

    def onPing(self, idx):
        self.conn.sendPong(idx)

    def networkAvailable(self):
        pass

    def networkDisconnected(self):
        self.sleeping.emit()

    def networkUnavailable(self):
        self.disconnected.emit()

    def onUnavailable(self):
        self.conn.sendUnavailable()

    def conversationOpened(self, jid):
        pass

    def onAvailable(self):
        self.conn.sendAvailable()

    def message_received(self, fmsg):
        if hasattr(fmsg, 'type'):
            if fmsg.type == "chat":
                if fmsg.remote.endswith('@g.us'):
                    self.groupMessageReceived.emit(fmsg)
                else:
                    self.messageReceived.emit(fmsg)
            elif fmsg.type == "media":
                if fmsg.remote.endswith('@g.us'):
                    self.groupMediaReceived.emit(fmsg)
                else:
                    self.mediaReceived.emit(fmsg)
        if fmsg.wants_receipt:
            self.conn.sendMessageReceived(fmsg)

    def subjectReceiptRequested(self, to, idx):
        self.conn.sendSubjectReceived(to, idx)

    def presence_available_received(self, remote):
        if remote == self.conn.jid:
            return
        self.available.emit(remote)

    def presence_unavailable_received(self, remote):
        if remote == self.conn.jid:
            return
        self.unavailable.emit(remote)

    def typing_received(self, remote):
        self.typing.emit(remote)

    def paused_received(self, remote):
        self.typingPaused.emit(remote)

    def message_error(self, fmsg, errorCode):
        pass

    def message_status_update(self, fmsg):
        pass


class StanzaReader(threading.Thread):

    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.connection = connection
        self.inn = connection.inn
        self.requests = {}

    def run(self):
        while True:
            if self.connection.disconnectRequested:
                self.connection.conn.close()
                break
            ready = select.select([self.inn.rawIn], [], [])
            if ready[0]:
                try:
                    node = self.inn.nextTree()
                except Exception, e:
                    self.connection.event.reconnecting.emit()
                    self.connection.login()
                    return
                self.lastTreeRead = int(time.time()) * 1000

                if node is not None:
                    if ProtocolTreeNode.tagEquals(node, 'iq'):
                        iqType = node.getAttributeValue('type')
                        idx = node.getAttributeValue('id')
                        jid = node.getAttributeValue('from')

                        if iqType is None:
                            raise Exception("iq doesn't have type")

                        if iqType == 'result':
                            if self.requests.has_key(idx):
                                self.requests[idx](node, jid)
                                del self.requests[idx]
                            elif idx.startswith(self.connection.user):
                                accountNode = node.getChild(0)
                                ProtocolTreeNode.require(accountNode, 'account')
                                kind = accountNode.getAttributeValue('kind')

                                if kind == 'paid':
                                    self.connection.account_kind = 1
                                elif kind == 'free':
                                    self.connection.account_kind = 0
                                else:
                                    self.connection.account_kind = -1

                                expiration = accountNode.getAttributeValue('expiration')

                                if expiration is None:
                                    raise Exception('no expiration')

                                try:
                                    self.connection.expire_date = long(expiration)
                                except ValueError:
                                    raise IOError('invalid expire date %s'% expiration)

                                self.connection.event.onAccountChanged(self.connection.account_kind,
                                        self.connection.expire_date)
                        elif iqType == 'error':
                            if self.requests.has_key(idx):
                                self.requests[idx](node)
                                del self.requests[idx]
                        elif iqType == 'get':
                            childNode = node.getChild(0)
                            if ProtocolTreeNode.tagEquals(childNode,
                                    'ping'):
                                self.connection.event.onPing(idx)
                            elif ProtocolTreeNode.tagEquals(childNode,
                                    'query') and jid is not None \
                                and 'http://jabber.org/protocol/disco#info' \
                                == childNode.getAttributeValue('xmlns'):
                                pin = childNode.getAttributeValue('pin')
                                timeoutString = childNode.getAttributeValue('timeout')
                                try:
                                    timeoutSeconds = (int(timeoutString) if timoutString is not None else None)
                                except ValueError:
                                    raise Exception('relay-iq exception parsing timeout %s ' % timeoutString)

                                if pin is not None:
                                    self.connection.event.onRelayRequest(pin, timeoutSeconds, idx)
                        elif iqType == 'set':
                            childNode = node.getChild(0)
                            if ProtocolTreeNode.tagEquals(childNode, 'query'):
                                xmlns = childNode.getAttributeValue('xmlns')

                                if xmlns == 'jabber:iq:roster':
                                    itemNodes = childNode.getAllChildren('item')
                                    ask = ''
                                    for itemNode in itemNodes:
                                        jid = itemNode.getAttributeValue('jid')
                                        subscription = itemNode.getAttributeValue('subscription')
                                        ask = itemNode.getAttributeValue('ask')
                        else:
                            raise Exception('Unkown iq type %s'
                                    % iqType)
                    elif ProtocolTreeNode.tagEquals(node, 'presence'):

                        xmlns = node.getAttributeValue('xmlns')
                        jid = node.getAttributeValue('from')

                        if (xmlns is None or xmlns == 'urn:xmpp') and jid is not None:
                            presenceType = node.getAttributeValue('type')
                            if presenceType == 'unavailable':
                                self.connection.event.presence_unavailable_received(jid)
                            elif presenceType is None or presenceType \
                                == 'available':
                                self.connection.event.presence_available_received(jid)
                        elif xmlns == 'w' and jid is not None:
                            add = node.getAttributeValue('add')
                            remove = node.getAttributeValue('remove')
                            status = node.getAttributeValue('status')

                            if add is not None:
                                self.connection.event.groupAdd(jid.split('-')[-1], add)
                            elif remove is not None:
                                self.connection.event.groupRemove(jid.split('-')[-1], remove)
                            elif status == 'dirty':
                                categories = self.parseCategories(node)
                                self.connection.event.onDirty(categories)
                    elif ProtocolTreeNode.tagEquals(node, 'message'):
                        self.parseMessage(node)

    def handlePingResponse(self, node, fromm):
        pass

    def handleLastOnline(self, node, jid=None):
        firstChild = node.getChild(0)
        ProtocolTreeNode.require(firstChild, 'query')
        seconds = firstChild.getAttributeValue('seconds')
        status = None
        status = firstChild.data

        if seconds is not None and jid is not None:
            self.connection.event.lastSeenUpdated.emit(int(seconds), jid)

    def parseCategories(self, dirtyNode):
        categories = {}

        if dirtyNode.children is not None:
            for childNode in dirtyNode.getAllChildren():
                if ProtocolTreeNode.tagEquals(childNode, 'category'):
                    cname = childNode.getAttributeValue('name')
                    timestamp = childNode.getAttributeValue('timestamp')
                    categories[cname] = timestamp

        return categories

    def parseMessage(self, messageNode):

        fmsg = Message()

        msg_id = messageNode.getAttributeValue('id')
        attribute_t = messageNode.getAttributeValue('t')
        fromAttribute = messageNode.getAttributeValue('from')
        author = messageNode.getAttributeValue('author')
        typeAttribute = messageNode.getAttributeValue('type')
        if fromAttribute is not None and msg_id is not None:
            fmsg.id = msg_id
            fmsg.remote = fromAttribute

        if typeAttribute == 'error':
            message = None
            errorCode = 0
            errorNodes = messageNode.getAllChildren('error')
            for errorNode in errorNodes:
                codeString = errorNode.getAttributeValue('code')
                try:
                    errorCode = int(codeString)
                except ValueError:
                    message = None


            if message is not None:
                message.status = 7
                self.connection.event.message_error(message, errorCode)
        elif typeAttribute == 'subject':
            receiptRequested = False
            requestNodes = messageNode.getAllChildren('request')
            for requestNode in requestNodes:
                if requestNode.getAttributeValue('xmlns') == 'urn:xmpp:receipts':
                    receiptRequested = True

            bodyNode = messageNode.getChild('body')
            subject = (None if bodyNode is None else bodyNode.data)

            if subject is not None:
                self.connection.event.newGroupSubject.emit(group=fromAttribute, author=author, subject=subject)

            if receiptRequested:
                self.connection.event.subjectReceiptRequested(fromAttribute, msg_id)

        elif typeAttribute == 'chat':
            wants_receipt = False
            messageChildren = ([] if messageNode.children
                               is None else messageNode.children)
            if author:
                fmsg.author = author
            for childNode in messageChildren:
                if ProtocolTreeNode.tagEquals(childNode, 'composing'):
                    if self.connection.event is not None:
                        self.connection.event.typing_received(fromAttribute)
                elif ProtocolTreeNode.tagEquals(childNode, 'paused'):
                    if self.connection.event is not None:
                        self.connection.event.paused_received(fromAttribute)
                elif ProtocolTreeNode.tagEquals(childNode,"media") and msg_id is not None:
                    fmsg.type = "media"

                    url = messageNode.getChild("media").getAttributeValue("url");
                    fmsg.media_type = media_type = messageNode.getChild("media").getAttributeValue("type")
                    data = {}

                    if media_type == "image":
                        data['preview'] = messageNode.getChild("media").data
                        data['url'] = url
                    elif media_type == "audio":
                        data['url'] = url
                    elif media_type == "video":
                        data['url'] = url
                    elif media_type == "location":
                        data['latitude'] = messageNode.getChild("media").getAttributeValue("latitude")
                        data['longitude'] = messageNode.getChild("media").getAttributeValue("longitude")
                        data['preview'] = messageNode.getChild("media").data
                    elif media_type == "vcard":
                        data['contact'] = messageNode.getChild("media").data
                    else:
                        continue
                    fmsg.data = data
                elif ProtocolTreeNode.tagEquals(childNode, 'body')  and msg_id is not None:
                    fmsg.type = "chat"
                    fmsg.data = childNode.data
                elif not ProtocolTreeNode.tagEquals(childNode, 'active'):

                    if ProtocolTreeNode.tagEquals(childNode, 'request'):
                        fmsg.wants_receipt = True
                    elif ProtocolTreeNode.tagEquals(childNode, 'notify'):
                        fmsg.notify_name = childNode.getAttributeValue('name')
                    elif ProtocolTreeNode.tagEquals(childNode, 'x'):
                        xmlns = childNode.getAttributeValue('xmlns')
                        if 'jabber:x:delay' == xmlns:
                            continue
                            stamp_str = \
                                childNode.getAttributeValue('stamp')
                            if stamp_str is not None:
                                stamp = stamp_str
                                fmsg.timestamp = stamp
                                fmsg.offline = True
                    else:
                        if ProtocolTreeNode.tagEquals(childNode, 'delay') \
                            or not ProtocolTreeNode.tagEquals(childNode,
                                'received') or msg_id is None:
                            continue

                        if self.connection.supports_receipt_acks:

                            receipt_type = \
                                childNode.getAttributeValue('type')
                            if receipt_type is None or receipt_type \
                                == 'delivered':
                                self.connection.sendDeliveredReceiptAck(fromAttribute, msg_id)
                            elif receipt_type == 'visible':
                                self.connection.sendVisibleReceiptAck(fromAttribute, msg_id)

            if fmsg.timestamp is None:
                fmsg.timestamp = time.time() * 1000
                fmsg.offline = False

            self.connection.event.message_received(fmsg)


class WAXMPP:
    SERVER = 's.whatsapp.net'
    USER_AGENT = "iPhone-2.8.3"

    def __init__(
        self,
        user,
        push_name,
        password,
        ):

        self.domain = WAXMPP.SERVER
        self.resource = WAXMPP.USER_AGENT
        self.user = user
        self.push_name = push_name
        self.password = password
        self.jid = user + '@' + WAXMPP.SERVER
        self.fromm = user + '@' + WAXMPP.SERVER + '/' + WAXMPP.USER_AGENT
        self.supports_receipt_acks = False
        self.msg_id = 0

        self.retry = True
        self.event = WAEventHandler(self)
        self.stanzaReader = None

        self.disconnectRequested = False

        self.connTries = 0

        self.verbose = True
        self.iqId = 0
        self.lock = threading.Lock()

        self.waiting = 0

        self.conn = None
        self.inn = None
        self.out = None
        self.event.loginSuccess.connect(self.onLoginSuccess)
        self.event.connectionError.connect(self.onConnectionError)

    def onLoginSuccess(self):
        self.connectionTries = 0
        c = StanzaReader(self)

        self.stanzaReader = c

        self.stanzaReader.start()

        self.sendClientConfig('', '', False, '')
        self.sendAvailableForChat()
        self.event.connected.emit()

    def onConnectionError(self):
        pass

    def disconnect(self):
        self.event.disconnectRequested.emit()
        self.disconnectRequested = True

    def login(self):
        self.conn = MySocketConnection()
        self.inn = BinTreeNodeReader(self.conn, Login.dictionary)
        self.out = BinTreeNodeWriter(self.conn, Login.dictionary)

        self.walogin = Login(self)
        self.walogin.start()

    def sendTyping(self, jid):
        composing = ProtocolTreeNode('composing',
                {'xmlns': 'http://jabber.org/protocol/chatstates'})
        message = ProtocolTreeNode('message', {'to': jid, 'type': 'chat'
                                   }, [composing])
        self.out.write(message)

    def sendPaused(self, jid):
        composing = ProtocolTreeNode('paused',
                {'xmlns': 'http://jabber.org/protocol/chatstates'})
        message = ProtocolTreeNode('message', {'to': jid, 'type': 'chat'
                                   }, [composing])
        self.out.write(message)

    def getSubjectMessage(
        self,
        to,
        msg_id,
        child,
        ):
        messageNode = ProtocolTreeNode('message', {'to': to,
                'type': 'subject', 'id': msg_id}, [child])

        return messageNode


    def sendSubjectReceived(self, to, msg_id):
        receivedNode = ProtocolTreeNode('received',
                {'xmlns': 'urn:xmpp:receipts'})
        messageNode = self.getSubjectMessage(to, msg_id, receivedNode)
        self.out.write(messageNode)

    def sendMessageReceived(self, fmsg):
        receivedNode = ProtocolTreeNode('received',
                {'xmlns': 'urn:xmpp:receipts'})
        messageNode = ProtocolTreeNode('message',
                {'to': fmsg.remote, 'type': 'chat',
                'id': fmsg.id}, [receivedNode])

        self.out.write(messageNode)

    def sendDeliveredReceiptAck(self, to, msg_id):
        self.out.write(self.getReceiptAck(to, msg_id, 'delivered'))

    def sendVisibleReceiptAck(self, to, msg_id):
        self.out.write(self.getReceiptAck(to, msg_id, 'visible'))

    def getReceiptAck(
        self,
        to,
        msg_id,
        receiptType,
        ):
        ackNode = ProtocolTreeNode('ack', {'xmlns': 'urn:xmpp:receipts'
                                   , 'type': receiptType})
        messageNode = ProtocolTreeNode('message', {'to': to,
                'type': 'chat', 'id': msg_id}, [ackNode])
        return messageNode

    def makeId(self, prefix):
        self.iqId += 1
        idx = ''
        if self.verbose:
            idx += prefix + str(self.iqId)
        else:
            idx = '%x' % self.iqId

        return idx

    def sendPing(self):
        idx = self.makeId('ping_')
        self.stanzaReader.requests[idx] = \
            self.stanzaReader.handlePingResponse

        pingNode = ProtocolTreeNode('ping', {'xmlns': 'w:p'})
        iqNode = ProtocolTreeNode('iq', {'id': idx, 'type': 'get',
                                  'to': self.domain}, [pingNode])
        self.out.write(iqNode)

    def sendPong(self, idx):
        iqNode = ProtocolTreeNode('iq', {'type': 'result',
                                  'to': self.domain, 'id': idx})
        self.out.write(iqNode)

    def getLastOnline(self, jid):

        if len(jid.split('-')) == 2:
            return

        self.sendSubscribe(jid)

        idx = self.makeId('last_')
        self.stanzaReader.requests[idx] = \
            self.stanzaReader.handleLastOnline

        query = ProtocolTreeNode('query', {'xmlns': 'jabber:iq:last'})
        iqNode = ProtocolTreeNode('iq', {'id': idx, 'type': 'get',
                                  'to': jid}, [query])
        self.out.write(iqNode)

    def sendIq(self):
        node = ProtocolTreeNode('iq', {'to': 'g.us', 'type': 'get',
                                'id': str(int(time.time())) + '-0'},
                                None, 'expired')
        self.out.write(node)

        node = ProtocolTreeNode('iq', {'to': 's.whatsapp.net',
                                'type': 'set',
                                'id': str(int(time.time())) + '-1'},
                                None, 'expired')
        self.out.write(node)

    def sendAvailableForChat(self):
        presenceNode = ProtocolTreeNode('presence',
                {'name': self.push_name})
        self.out.write(presenceNode)

    def sendAvailable(self):
        presenceNode = ProtocolTreeNode('presence', {'type': 'available'})
        self.out.write(presenceNode)

    def sendUnavailable(self):
        presenceNode = ProtocolTreeNode('presence', {'type': 'unavailable'})
        self.out.write(presenceNode)

    def sendSubscribe(self, to):
        presenceNode = ProtocolTreeNode('presence', {'type': 'subscribe', 'to': to})

        self.out.write(presenceNode)

    def sendMessage(self, fmsg):
        bodyNode = ProtocolTreeNode('body', None, None, fmsg.data)
        msgNode = self.getMessageNode(fmsg, bodyNode)

        self.out.write(msgNode)
        self.msg_id += 1

    def sendClientConfig(
        self,
        sound,
        pushID,
        preview,
        platform,
        ):
        idx = self.makeId('config_')
        configNode = ProtocolTreeNode('config', {
            'xmlns': 'urn:xmpp:whatsapp:push',
            'sound': sound,
            'id': pushID,
            'preview': ('1' if preview else '0'),
            'platform': platform,
            })
        iqNode = ProtocolTreeNode('iq', {'id': idx, 'type': 'set',
                                  'to': self.domain}, [configNode])

        self.out.write(iqNode)

    def getMessageNode(self, fmsg, child):
        requestNode = None
        serverNode = ProtocolTreeNode('server', None)
        xNode = ProtocolTreeNode('x', {'xmlns': 'jabber:x:event'},
                                 [serverNode])
        childCount = ((0 if requestNode is None else 1)) + 2
        messageChildren = [None] * childCount
        i = 0
        if requestNode is not None:
            messageChildren[i] = requestNode
            i += 1

        messageChildren[i] = xNode
        i += 1
        messageChildren[i] = child
        i += 1

        messageNode = ProtocolTreeNode('message',
                {'to': fmsg.remote, 'type': 'chat', 'id': fmsg.id},
                messageChildren)

        return messageNode
