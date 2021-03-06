
# main for running the TicTacToe server

import socket
from SubServer import SubServer
import select
from Player import Player

max_msg_length = 1000
server_ip = '0.0.0.0'
server_port = 5555
loss_massage = "You have lost the game :("
win_massage = "You have won the game :)"
tie_massage = "It's a tie!"
# setup server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_ip, server_port))
server_socket.listen()


client_sockets_read = []
# has the clients that it has to read from - holds sockets
client_sockets_write = []
# has the clients that it has to write to - holds sockets
player_list = []
# a list that holds new clients/players - holds Players
running_subserver_list = []
# the currently running subservers - holds subservers

stop_loop = False

# a loop that divides the players joining into subservers
while not stop_loop:
    readList, writeList, errorList = select.select([server_socket] + client_sockets_read, client_sockets_write, [])
    # first loop that adds new players

    for currentSocket in readList:

        if currentSocket is server_socket:
            connection, client_address = currentSocket.accept()
            client_sockets_read.append(connection)
            client_sockets_write.append(connection)
            # add a player
            player_list.append(Player(client_address, connection))
            print("A player joined - ", client_address)
            if len(player_list) == 2:  # if two players joined, stop looking for players
                newSubServer = SubServer(player_list.pop(), player_list.pop())  # create a new subserver
                # set up the subserver
                newSubServer.board.create_new_board()  # create the board
                newSubServer.set_signs()
                running_subserver_list.append(newSubServer)  # add to running subserver list
                # removes the players from player_list, puts them in a subserver object and adds them
                # to the running subservers list
                print("A new Subserver has been created - ",
                      newSubServer.player1.player_ip[0],
                      newSubServer.player1.player_sign,
                      newSubServer.player2.player_ip[0],
                      newSubServer.player2.player_sign)
        else:
            # if there are players playing right now
            try:
                for socket_subServer in running_subserver_list:

                    if socket_subServer.player1.mySocket == currentSocket:
                        # read from player1
                        data = socket_subServer.player1.mySocket.recv(max_msg_length).decode()  # receive the massage
                        socket_subServer.board.switch_slot(int(data), socket_subServer.player1.player_sign)
                        # send the player the new board after he chose a slot
                        socket_subServer.player1.mySocket.send(socket_subServer.board.to_string().encode())
                        # switch the turn
                        socket_subServer.turn = socket_subServer.player2

                    if socket_subServer.player2.mySocket == currentSocket:
                        # read from player2
                        data = socket_subServer.player2.mySocket.recv(max_msg_length).decode()  # receive the massage
                        socket_subServer.board.switch_slot(int(data), socket_subServer.player2.player_sign)
                        # send the player the new board after he chose a slot
                        socket_subServer.player2.mySocket.send(socket_subServer.board.to_string().encode())
                        # switch the turn
                        socket_subServer.turn = socket_subServer.player1

            # except ValueError or BrokenPipeError
            except(ValueError, BrokenPipeError, ConnectionError):
                # if one of the players has disconnected, remove both players from the lists /
                # they are in and send a massage to the player that's still playing
                # send massage:
                if socket_subServer.turn == socket_subServer.player1:
                    try:
                        socket_subServer.player2.mySocket.send("The other player has disconnected,"
                                                               " would you like to join another game?".encode())
                    except (BrokenPipeError, ConnectionError):
                        socket_subServer.player1.mySocket.send("The other player has disconnected,"
                                                               " would you like to join another game?".encode())

                else:
                    socket_subServer.player1.mySocket.send("The other player has disconnected,"
                                                           " would you like to join another game?".encode())
                # close the sockets
                socket_subServer.player1.mySocket.close()
                socket_subServer.player2.mySocket.close()
                # remove from subserver list
                running_subserver_list.remove(socket_subServer)
                # remove from the lists that select uses
                client_sockets_read.remove(socket_subServer.player1.mySocket)
                client_sockets_read.remove(socket_subServer.player2.mySocket)

                if socket_subServer.player1.mySocket in client_sockets_write:
                    client_sockets_write.remove(socket_subServer.player1.mySocket)

                if socket_subServer.player2.mySocket in client_sockets_write:
                    client_sockets_write.remove(socket_subServer.player2.mySocket)
                continue

    for currentSocket in writeList:
        # loop on writeable sockets
        for socket_subServer in running_subserver_list:

            if socket_subServer.check_if_over():
                # if someone has won the game
                # send the lost and won massages
                # first send the one which its his turn now that he lost
                socket_subServer.turn.mySocket.send(loss_massage.encode())

                if socket_subServer.turn == socket_subServer.player1:
                    # send win massage
                    socket_subServer.player2.mySocket.send(win_massage.encode())

                else:
                    socket_subServer.player1.mySocket.send(win_massage.encode())

                # close the sockets
                socket_subServer.player1.mySocket.close()
                socket_subServer.player2.mySocket.close()
                # remove from subserver list
                running_subserver_list.remove(socket_subServer)
                # remove from the lists that select uses
                client_sockets_read.remove(socket_subServer.player1.mySocket)
                client_sockets_read.remove(socket_subServer.player2.mySocket)

                if socket_subServer.player1.mySocket in client_sockets_write:
                    client_sockets_write.remove(socket_subServer.player1.mySocket)

                if socket_subServer.player2.mySocket in client_sockets_write:
                    client_sockets_write.remove(socket_subServer.player2.mySocket)
                continue
                # return to the beginning of the loop
            if socket_subServer.check_if_tie():
                # send the players the tie massages
                socket_subServer.player1.mySocket.send(tie_massage.encode())
                socket_subServer.player2.mySocket.send(tie_massage.encode())
                # close the sockets
                socket_subServer.player1.mySocket.close()
                socket_subServer.player2.mySocket.close()
                # remove from subserver list
                running_subserver_list.remove(socket_subServer)
                # remove from the lists that select uses
                client_sockets_read.remove(socket_subServer.player1.mySocket)
                client_sockets_read.remove(socket_subServer.player2.mySocket)

                if socket_subServer.player1.mySocket in client_sockets_write:
                    client_sockets_write.remove(socket_subServer.player1.mySocket)

                if socket_subServer.player2.mySocket in client_sockets_write:
                    client_sockets_write.remove(socket_subServer.player2.mySocket)
                continue
                # return to the beginning of the loop
            if socket_subServer.turn.mySocket == currentSocket:
                # if the socket ready for writing is the player which its his turn

                if socket_subServer.turn == socket_subServer.player1:
                    # remove it so it doesnt send it infinitely
                    if currentSocket in client_sockets_write:
                        client_sockets_write.remove(currentSocket)
                    socket_subServer.player1.mySocket.send(socket_subServer.board.to_string().encode())  # send
                    # the board to the socket
                    # now return the other player's socket to the list that select uses
                    # if its not already there
                    if not (socket_subServer.player2.mySocket in client_sockets_write):
                        client_sockets_write.append(socket_subServer.player2.mySocket)

                if socket_subServer.turn == socket_subServer.player2:
                    # remove it so it doesnt send it infinitly
                    if currentSocket in client_sockets_write:
                        client_sockets_write.remove(currentSocket)
                    socket_subServer.player2.mySocket.send(socket_subServer.board.to_string().encode())  # send
                    # the board to the socket
                    # now return the other player's socket to the list that select uses
                    # if its not already there
                    if not (socket_subServer.player1.mySocket in client_sockets_write):
                        client_sockets_write.append(socket_subServer.player1.mySocket)
