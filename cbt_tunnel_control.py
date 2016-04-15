"""
CrossBrowserTesting.com local tunnel management in Python

This program defines functions to programatically start and stop the local 
tunnel to crossbrowsertesting.com.

To find your authkey, go to crossbrowsertesting.com/account

below is the best use of this module 

>>> from cbt_tunnel_control import CBTTunnel
>>> cbt = CBTTunnel('<username>','<authkey>')
>>> cbt.start_tunnel()
>>> # then, when you are done with the tunnel:
>>> cbt.shutdown_tunnel()


John Reese | johnr@crossbrowsertesting.com | April 2016 
"""

import os
import requests
from subprocess import Popen
from shutil import copyfileobj
from time import sleep

class CBTTunnel(object):
    def __init__(self, username,authkey):
        self.username = username
        self.authkey = authkey
        self.create_api_session()

    def _shutdown_tunnel_process(self):
        """
        Attempt graceful shutdown of tunnel
        Kill it if it doesn't work
        Called by the non-reserved function shutdown_tunnel(process,session)
        """
        self.tunnel_process.terminate()
        # wait a short bit for the process to terminate...
        sleep(5)
        if self.tunnel_process.poll() == None:
            sleep(5)
            if self.tunnel_process.poll() == None:
                # process isn't shutting down. Time to kill it hard.
                print("Grace failed, killing tunnel hard")
                self.tunnel_process.kill()

    def _shutdown_tunnel_via_api(self):
        """
        Called by shutdown_tunnel(process,session)
        """
        url = 'https://crossbrowsertesting.com/api/v3/tunnels/' + str(self.get_tunnel_id())
        self.session.delete(url)

    def _delete_tunnel_jar(self):
        """
        Called by shutdown_tunnel(process,session)
        """
        os.system('rm cbttunnel.jar')

    def create_api_session(self):
        """
        Create and set an api session object with site credentials
        """
        session = requests.Session()
        session.auth = (self.username,self.authkey)
        self.session = session

    def download_tunnel_jar(self):
        """   
        """
        jar_url = "https://github.com/crossbrowsertesting/cbt-tunnel-java/raw/master/cbttunnel.jar"
        response = requests.get(jar_url,stream=True)
        with open('cbttunnel.jar', 'wb') as out_file:
            copyfileobj(response.raw, out_file)
        del response

    def get_tunnel_id(self):
        """
        Uses a Session object with credentials to check if there is a tunnel running
        Returns tunnel_id if there is a tunnel, otherwise returns false
        This is used both to get a tunnel_id and check if a tunnel is running.

        Note: There shouldn't ever be multiple tunnels running for a single user.
        """
        response = self.session.get('https://crossbrowsertesting.com/api/v3/tunnels/',
            data = {'active' : 'true'})
        active_tunnel = response.json()['tunnels']
        if active_tunnel == []:
            return False
        elif active_tunnel != []:
            return active_tunnel[0]['tunnel_id']

    def start_tunnel(self):
        """
        Checks for the tunnel jar file (downloads it if it isn't present)
        Uses subprocess to start the tunnel jar
        Double checks that the tunnel is running 
        Returns the Popen object of the running tunnel 
        """
        if not os.path.isfile('cbttunnel.jar'):
            self.download_tunnel_jar()
        self.tunnel_process = Popen(['java', '-jar', 'cbttunnel.jar', 
            '-authkey', self.session.auth[1]]) # pulling the authkey out of the self object
        # short wait for the tunnel to start
        sleep(5)
        # The tunnel *should* be started, time to check 
        if self.get_tunnel_id() == False:
            sleep(5)
            if self.get_tunnel_id() == False:
                print("Error: could not establish tunnel. Check that your authkey is correct.")
                raise ConnectionError
        # if the tunnel is running, then we're done here. 

    def shutdown_tunnel(self, delete_jar=False):
        """
        recommended to leave delete_jar false to speed up starting tunnels in the future
        """
        self._shutdown_tunnel_via_api()
        self._shutdown_tunnel_process()

        self.tunnel_process.wait()

        if self.get_tunnel_id() == False:
            if delete_jar == True:
                self._delete_tunnel_jar()
            return
        else:
            print "Error: failed to shutdown the tunnel."
            raise


def main():
    print 'Testing local connection control'
    print 'This will start a tunnel, then shut it down'
    username = raw_input('CBT Username:')
    authkey = raw_input('CBT Authkey:')
    cbt = CBTTunnel(username,authkey)
    cbt.start_tunnel()
    sleep(15)
    cbt.shutdown_tunnel()
    if cbt.get_tunnel_id() == False:
        print 'Done!'

if __name__ == '__main__':
    main()