List of things that we need to implement in the future:

* Create a storage array for CON messages that must be sent
  * Server will attempt to resend the message until it receives an ACK message - DONE
  * Resend happens according to RFC-7252 rules - DONE
  * Configurable in settings.cfg
  * Resend happens in __threadloop - OBVIOUSLY
* Create a storage array for received messages
  * Used to detect duplicate incoming messages
* Detect faulty packets (unrecognized / unsupported message types, etc.), and send error messages to client
  * Error messages are of class Client Error / Server Error
* Parse incoming messages via callback methods - DONE??
  * Server receives message, and sends an ACK if it's a CON request
  * Afterwards, server calls a dedicated callback function for the message type
  * Messages which don't have a callback are considered as unsupported

... and other things

Notes: