import urllib2

# From: http://lukasklein.com/blog/custom-ios-whatsapp-password/

# number with 00 and countrycode, e.g. 00491234567890
def get_new_code(number, method='voice'):
    url = "https://r.whatsapp.net/v1/code.php?cc=%s&in=%s&to=%s&lc=US&lg=en&mcc=000&mnc=000&imsi=00000000000000&method=%s" % (number[2:][:2], number[4:], number, method)
    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())
    opener.addheaders = [('User-Agent', "WhatsApp/2.8.13 S60Version/5.3 Device/C7-00"),("Content-Type","application/x-www-form-urlencoded"),("Accept","text/xml")]
    connection = opener.open(url)
    response = connection.read()
    connection.close()
    print response

# number with 00 and countrycode like above
# password should be a 32 character md5 lookalike to not draw attention
# code is the 3 digit code you got in your txt
def register_number_with_password(number, password, code):
    url = "https://r.whatsapp.net/v1/register.php?cc=%s&in=%s&udid=%s&code=%s&method=voice"%(number[2:][:2], number[4:], password, code)
    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())
    opener.addheaders = [('User-Agent', "WhatsApp/2.8.13 S60Version/5.3 Device/C7-00"),("Content-Type","application/x-www-form-urlencoded"),("Accept","text/xml")]
    connection = opener.open(url)
    response = connection.read()
    connection.close()
    print response