import logging
import socket


LOG = logging.getLogger(__name__)


class Statsd(object):
    def __init__(self, configuration):
        self.host = configuration['host']
        self.port = int(configuration['port'])
        self.socket_type = 'udp'
        LOG.debug("Statsd notifier %s:%s" % (self.host, self.port))

        self._socket = None

    def send(self, metrics):
        for label, data in metrics:
            self._send_item("%s:%.7f|ms" % (label, data))

    def _send_item(self, body):
        # Since we're keeping the socket open for a long time, we try
        # the send twice, reopening the socket in between rounds, if
        # sending fails the first time.
        for rnd in range(2):
            # Get the socket
            sock = self._open_socket()
            if not sock:
                return

            # Send the body
            try:
                sock.sendall(body)
            except socket.error as e:
                if rnd:
                    LOG.error("%s: Error writing to server (%s, %s): %s" % \
                              (self.__class__.__name__, self.host, self.port,
                               e))

                # Try reopening the socket next time
                self._close_socket()
            else:
                # Body successfully sent
                break


    def _open_socket(self):
        """Retrieve a socket for the server.

        Creates the socket, if necessary.
        """

        if not self._socket:
            if self.socket_type == 'udp':
                sock_type = socket.SOCK_DGRAM
            else:
                sock_type = socket.SOCK_STREAM

            sock = socket.socket(socket.AF_INET, sock_type)

            # Connect the socket
            try:
                sock.connect((self.host, self.port))
            except socket.error as e:
                LOG.error("Error connecting to server %s port %s: %s" %
                       (self.host, self.port, e))
                return None

            self._socket= sock

        return self._socket

    def _close_socket(self):
        """Reset server socket.

        Close the existing socket and clear the cache.  Causes the
        socket to be recreated next time self.sock is accessed.
        """

        if self._socket:
            try:
                self._socket.close()
            except Exception:
                # Might already be closed; we don't care
                pass

            # Clear the cache
            self._socket = None

