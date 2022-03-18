# Chat Server
This is the Server file in the folder.

## What you need to know
You need to run this file first.
it will start an empty command prompt terminal
you can minimize it after this

It will have no other prompts at all. It will only display when someone enters and leaves

# Chat Client
This is the Chat Client file in the folder.

## What you need to know
Only run this after the server file has been run

It will start by asking what you would like your username to be
if the username is not taken it will let you in the Chat server. 
If it has you will get an ERROR and will be prompted to re enter a different username

After this you will be connected to the server and should be prompted as such.
You will be able to type a broadcast message to everyone simply by typing anything that is not a "p" or an "e"

##Private messages
If you type a "p" you will be prompted to enter a user that you would like to message
after you enter in a username you will be prompted to enter a message to send. 
once you send you will see a display of what you sent
if the user is online at the time of sending then it will be delivered
although if they are not online then you will be prompted that it is not a valid username

## Exiting
You can exit the program simply by typing an "e" in the prompt
This will prompt everyone that you have disconnected from the server and will close all sockets
this will also close your terminal by letting all the threads shutdown
