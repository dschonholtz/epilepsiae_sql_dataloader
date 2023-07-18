# FileFerry

## What it does

This module transports files from the epilepseae server to whereever you are locally running your code up to your server.
GetSeizureLists.py does it with the seizurelist files from the epilepsae website via selenium as they aren't in the SFTP download.
PushSeizureListsToServer.py pushes them up to your server.

All of the SFTP commands were done manually, but if you would like to run them in a python process instead of on your server, I would be open to PRs.
