#!/bin/bash

basedir=/home/lenart/NalogeBot

session="discordbot"

if [[ basedir != */ ]]
then
   basedir+="/"
fi

start() {
    tmux new-session -d -s $session

    echo "Starting server"

    tmux send-keys -t $session:0 "cd $basedir" C-m
    tmux send-keys -t $session:0 "/usr/bin/python3 /home/lenart/NalogeBot/bot.py" C-m
}



case "$1" in
start)
    start
;;
attach)
    tmux attach -t $session
;;
*)
echo "Usage: start.sh (start|attach)"
;;
esac