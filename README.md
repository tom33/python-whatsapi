This is an implementation of the Whatsapp API based on [Wazapp](https://github.com/tgalal/wazapp). I mostly cleaned up the code, removed dependency on Qt and made it more usable as an API
The API is event driven, you can hook into events and receive a callback when the event fires.

For an example usage please check example.py

To see a list of all events please look at the WAEventHandler class in whatsapi/waxmpp.py

To register a new number to Whatsapp, use register.py. For now you will have to write your own Python script for this.

TODO:

* Proper documentation
* Tests
* More extensive examples

I don't have time to work on this currently but feel free to submit a pull request.

The license is the same as the Wazapp application