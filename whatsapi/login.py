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

import base64
import random
import socket
import threading

from whatsapi.utilities import str_base, S40MD5Digest, ByteArray
from whatsapi.protocoltreenode import ProtocolTreeNode
from whatsapi.exceptions import *

class Login(threading.Thread):

    dictionary = [
        None,
        None,
        None,
        None,
        None,
        '1',
        '1.0',
        'ack',
        'action',
        'active',
        'add',
        'all',
        'allow',
        'apple',
        'audio',
        'auth',
        'author',
        'available',
        'bad-request',
        'base64',
        'Bell.caf',
        'bind',
        'body',
        'Boing.caf',
        'cancel',
        'category',
        'challenge',
        'chat',
        'clean',
        'code',
        'composing',
        'config',
        'conflict',
        'contacts',
        'create',
        'creation',
        'default',
        'delay',
        'delete',
        'delivered',
        'deny',
        'DIGEST-MD5',
        'DIGEST-MD5-1',
        'dirty',
        'en',
        'enable',
        'encoding',
        'error',
        'expiration',
        'expired',
        'failure',
        'false',
        'favorites',
        'feature',
        'field',
        'free',
        'from',
        'g.us',
        'get',
        'Glass.caf',
        'google',
        'group',
        'groups',
        'g_sound',
        'Harp.caf',
        'http://etherx.jabber.org/streams',
        'http://jabber.org/protocol/chatstates',
        'id',
        'image',
        'img',
        'inactive',
        'internal-server-error',
        'iq',
        'item',
        'item-not-found',
        'jabber:client',
        'jabber:iq:last',
        'jabber:iq:privacy',
        'jabber:x:delay',
        'jabber:x:event',
        'jid',
        'jid-malformed',
        'kind',
        'leave',
        'leave-all',
        'list',
        'location',
        'max_groups',
        'max_participants',
        'max_subject',
        'mechanism',
        'mechanisms',
        'media',
        'message',
        'message_acks',
        'missing',
        'modify',
        'name',
        'not-acceptable',
        'not-allowed',
        'not-authorized',
        'notify',
        'Offline Storage',
        'order',
        'owner',
        'owning',
        'paid',
        'participant',
        'participants',
        'participating',
        'particpants',
        'paused',
        'picture',
        'ping',
        'PLAIN',
        'platform',
        'presence',
        'preview',
        'probe',
        'prop',
        'props',
        'p_o',
        'p_t',
        'query',
        'raw',
        'receipt',
        'receipt_acks',
        'received',
        'relay',
        'remove',
        'Replaced by new connection',
        'request',
        'resource',
        'resource-constraint',
        'response',
        'result',
        'retry',
        'rim',
        's.whatsapp.net',
        'seconds',
        'server',
        'session',
        'set',
        'show',
        'sid',
        'sound',
        'stamp',
        'starttls',
        'status',
        'stream:error',
        'stream:features',
        'subject',
        'subscribe',
        'success',
        'system-shutdown',
        's_o',
        's_t',
        't',
        'TimePassing.caf',
        'timestamp',
        'to',
        'Tri-tone.caf',
        'type',
        'unavailable',
        'uri',
        'url',
        'urn:ietf:params:xml:ns:xmpp-bind',
        'urn:ietf:params:xml:ns:xmpp-sasl',
        'urn:ietf:params:xml:ns:xmpp-session',
        'urn:ietf:params:xml:ns:xmpp-stanzas',
        'urn:ietf:params:xml:ns:xmpp-streams',
        'urn:xmpp:delay',
        'urn:xmpp:ping',
        'urn:xmpp:receipts',
        'urn:xmpp:whatsapp',
        'urn:xmpp:whatsapp:dirty',
        'urn:xmpp:whatsapp:mms',
        'urn:xmpp:whatsapp:push',
        'value',
        'vcard',
        'version',
        'video',
        'w',
        'w:g',
        'w:p:r',
        'wait',
        'x',
        'xml-not-well-formed',
        'xml:lang',
        'xmlns',
        'xmlns:stream',
        'Xylophone.caf',
        'account',
        'digest',
        'g_notify',
        'method',
        'password',
        'registration',
        'stat',
        'text',
        'user',
        'username',
        'event',
        'latitude',
        'longitude',
        ]

    # unsupported yet:

    nonce_key = 'nonce="'


    def __init__(
        self,
        connection,
        ):
        super(Login, self).__init__()

        self.connection = connection
        self.conn = connection.conn
        self.out = connection.out
        self.inn = connection.inn
        self.digest = S40MD5Digest()

    def run(self):

        (HOST, PORT) = ('bin-nokia.whatsapp.net', 443)
        try:
            self.conn.connect((HOST, PORT))

            self.conn.connected = True
            self.out.streamStart(self.connection.domain,
                                 self.connection.resource)

            self.sendFeatures()
            self.sendAuth()
            self.inn.streamStart()
            challengeData = self.readFeaturesAndChallenge()
            self.sendResponse(challengeData)

            self.readSuccess()
        except socket.error:
            return self.connection.event.connectionError.emit()
        except ConnectionClosedException:
            return self.connection.event.connectionError.emit()

    def sendFeatures(self):
        toWrite = ProtocolTreeNode('stream:features', None,
                                   [ProtocolTreeNode('receipt_acks',
                                   None, None)])
        self.out.write(toWrite)

    def sendAuth(self):
        node = ProtocolTreeNode('auth',
                                {'xmlns': 'urn:ietf:params:xml:ns:xmpp-sasl'
                                , 'mechanism': 'DIGEST-MD5-1'})
        self.out.write(node)

    def readFeaturesAndChallenge(self):
        server_supports_receipt_acks = True
        root = self.inn.nextTree()

        while root is not None:
            if ProtocolTreeNode.tagEquals(root, 'stream:features'):
                server_supports_receipt_acks = \
                    root.getChild('receipt_acks') is not None
                root = self.inn.nextTree()

                continue

            if ProtocolTreeNode.tagEquals(root, 'challenge'):
                self.connection.supports_receipt_acks = \
                    self.connection.supports_receipt_acks \
                    and server_supports_receipt_acks

                # String data = new String(Base64.decode(root.data.getBytes()))

                data = base64.b64decode(root.data)
                return data
        raise Exception('fell out of loop in readFeaturesAndChallenge')

    def sendResponse(self, challengeData):
        response = self.getResponse(challengeData)
        node = ProtocolTreeNode('response',
                                {'xmlns': 'urn:ietf:params:xml:ns:xmpp-sasl'
                                }, None,
                                str(base64.b64encode(response)))

        self.out.write(node)

        self.inn.inn.buf = []

    def getResponse(self, challenge):

        i = challenge.index(Login.nonce_key)

        i += len(Login.nonce_key)
        j = challenge.index('"', i)

        nonce = challenge[i:j]
        cnonce = str_base(abs(random.getrandbits(64)), 36)
        nc = '00000001'
        bos = ByteArray()
        bos.write(self.md5Digest(self.connection.user + ':'
                  + self.connection.domain + ':'
                  + self.connection.password))
        bos.write(58)
        bos.write(nonce)
        bos.write(58)
        bos.write(cnonce)

        digest_uri = 'xmpp/' + self.connection.domain

        A1 = bos.toByteArray()
        A2 = 'AUTHENTICATE:' + digest_uri

        KD = str(self.bytesToHex(self.md5Digest(A1.getBuffer()))) + ':' \
            + nonce + ':' + nc + ':' + cnonce + ':auth:' \
            + str(self.bytesToHex(self.md5Digest(A2)))

        response = str(self.bytesToHex(self.md5Digest(KD)))
        bigger_response = ''
        bigger_response += 'realm="'
        bigger_response += self.connection.domain
        bigger_response += '",response='
        bigger_response += response
        bigger_response += ',nonce="'
        bigger_response += nonce
        bigger_response += '",digest-uri="'
        bigger_response += digest_uri
        bigger_response += '",cnonce="'
        bigger_response += cnonce
        bigger_response += '",qop=auth'
        bigger_response += ',username="'
        bigger_response += self.connection.user
        bigger_response += '",nc='
        bigger_response += nc

        return bigger_response

    def forDigit(self, b):
        if b < 10:
            return 48 + b

        return 97 + b - 10

    def bytesToHex(self, bytes):
        ret = bytearray(len(bytes) * 2)
        i = 0
        for c in range(0, len(bytes)):
            ub = bytes[c]
            if ub < 0:
                ub += 256
            ret[i] = self.forDigit(ub >> 4)
            i += 1
            ret[i] = self.forDigit(ub % 16)
            i += 1

        return ret

    def md5Digest(self, inputx):
        self.digest.reset()
        self.digest.update(inputx)
        return self.digest.digest()

    def readSuccess(self):
        node = self.inn.nextTree()

        if ProtocolTreeNode.tagEquals(node, 'failure'):
            self.connection.event.loginFailed.emit()
            raise LoginException('Login Failure')

        ProtocolTreeNode.require(node, 'success')

        expiration = node.getAttributeValue('expiration')

        if expiration is not None:
            self.connection.expire_date = expiration

        kind = node.getAttributeValue('kind')

        if kind == 'paid':
            self.connection.account_kind = 1
        elif kind == 'free':
            self.connection.account_kind = 0
        else:
            self.connection.account_kind = -1

        status = node.getAttributeValue('status')

        if status == 'expired':
            self.connection.event.loginFailed.emit()
            raise LoginException('Account expired on '
                            + str(self.connection.expire_date))

        if status == 'active':
            if expiration is None:
                pass
        else:
            self.connection.account_kind = 1

        self.inn.inn.buf = []

        self.connection.event.loginSuccess.emit()
