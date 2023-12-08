from flask import Flask, render_template, request, send_file, Response, redirect, url_for, jsonify, Blueprint, send_from_directory
from pytube import YouTube, Playlist
from googleapiclient.discovery import build
import random, requests, re, os, threading, time, json, threading, copy
from flask_socketio import SocketIO
from pydub import AudioSegment

app = Flask(__name__)
socketio = SocketIO(app)

path_to_music = "./music/"
movies = [movie for movie in os.listdir(path_to_music) if os.path.isdir(os.path.join(path_to_music, movie))]

player_json_filename = "players.json"
musics_json_filename = "musics.json"

currents_players = []
leader = ""
all_players = None

room_thread = None
stop_thread = False
current_random_music = "music\Snow White and the Seven Dwarfs\Snow White Soundtrack - 01 - Overture.mp3"
current_random_music_name = "Snow White Soundtrack - 01 - Overture.mp3"
current_random_movie = "Snow White and the Seven Dwarfs"

current_random_time = 0
initial_waiting_duration = 10
waiting_duration = 7
song_duration = 20
number_of_songs = 20

default_mode = percentage_mode = easy = medium = hard = False
current_percentage_range = []
current_difficulty = None
current_default_difficulty = None
current_count = None

current_replys_and_points_room = []
players_ready = []




### Auxiliar Functions ###

def update_playersdb():
    global all_players
    with open(player_json_filename, 'r') as playersdb:
        players = json.load(playersdb)
    all_players = players

def verify_player_exists(way="", input=""):
    with open(player_json_filename, 'r') as playersdb:
        players = json.load(playersdb)
        if(len(players) > 0):
            for player in players:
                if player[way] == input:
                    return player
                
def create_player(ip, username):
    player_data = {"ip" : ip, "username" : username, "points" : 0}
    with open(player_json_filename, 'r') as playersdb:
        current_data = json.load(playersdb)
        current_data.append(player_data)
    with open(player_json_filename, 'w') as playersdb:
        json.dump(current_data, playersdb, indent=4)
    return player_data

def add_points_player():
    global current_replys_and_points_room
    with open(player_json_filename, 'r') as playersdbread:
        players = json.load(playersdbread)
        if(len(players) > 0):
            for player in players:
                for reply in current_replys_and_points_room:
                    if reply["username"] == player["username"]:
                        player["points"] += reply["points"]
    with open(player_json_filename, 'w') as playersdbwrite:            
        json.dump(players, playersdbwrite, indent=4)



### Index ###

@app.route("/")
def index():
    global currents_players, leader

    ip = request.remote_addr
    print(ip,"entrou no DMQ!")
    
    player = verify_player_exists("ip", ip)
    if player != None:
        print("Found player", player)
        if player["username"] not in currents_players:
            if len(currents_players) == 0:
                leader = player["username"]
            currents_players.append(player["username"])
        return redirect(url_for('lobby'))

    return render_template("index.html")

@app.route('/processar', methods=['POST'])
def processar():
    username = request.form['input']

    ip = request.remote_addr

    player = verify_player_exists("username", username)
    if player == None:
        player = create_player(ip, username)
        print("Create player", player)

        currents_players.append(player["username"])
        
        return redirect(url_for('lobby'))
    
    mensagem = f"The username {username} already exists. Try again."
    return render_template("index.html", msg=mensagem)



### Lobby ###

@app.route("/lobby")
def lobby():
    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    if player is None or player["username"] not in currents_players: return redirect(url_for('index'))
    return render_template("lobby.html", movies=movies)



### Main Room / Main Game ###

@app.route("/room")
def room():
    if room_thread is None:
        return redirect(url_for('lobby'))
    return render_template("audio.html")

@app.route("/room", methods=['POST'])
def room_post():
    global room_thread, default_mode, percentage_mode, easy, medium, hard, current_percentage_range
    if room_thread is None:
        print("Create Room Thread!")
        default_mode = request.form.get('default')
        percentage_mode = request.form.get('percentage')
        easy = request.form.get('easy')
        medium = request.form.get('medium')
        hard = request.form.get('hard')
        slider_values_str = request.form.get('sliderValue')
        current_percentage_range = list(map(int, slider_values_str.split(',')))
        print(f"default_mode = {default_mode}; percentage_mode = {percentage_mode}; easy = {easy}; medium = {medium}; hard = {hard}; current_percentage_range: {current_percentage_range}")
        room_thread = threading.Thread(target=main_room_thread)
        room_thread.start()
        socketio.emit('go_to_room', "", broadcast=True)
    return redirect(url_for('room'))

def main_room_thread():
    global current_random_time, room_thread, stop_thread, current_random_music, current_difficulty, current_default_difficulty, current_count, players_ready
    stop_thread = False
    clean_points()
    for i in range(initial_waiting_duration+1,0,-1):
        clean_replys()
        socketio.emit('title_refresh', "Wait " + str(i) + " seconds ...", broadcast=True)
        time.sleep(1)
        #print(f'Counter for wait: {i}')
    socketio.emit('title_refresh', f'Listen Carefully! ({song_duration})', broadcast=True)
    for n in range(1,number_of_songs+1):
        clean_replys()
        choose_random_music()
        if current_random_music == "":
            break
        socketio.emit('music_content', '{"current_difficulty" : "", "current_default_difficulty" : ""}', broadcast=True)
        for i in range(song_duration+1,0,-1):
            current_time = current_random_time + song_duration - i
            socketio.emit('audio_play', '{"command": "play", "time": "' + str(current_time) + '"}', broadcast=True)
            socketio.emit('title_refresh', f"[{n}] Listen Carefully! ({i})", broadcast=True)
            time.sleep(1)
            #print(f'Counter for song {n}: {i}')
            if is_all_skiped():
                clear_skips()
                break
        socketio.emit('audio_play', '{"command": "pause"}', broadcast=True)
        verify_replys()
        calculate_difficulty()
        for i in range(waiting_duration+1,0,-1):
            socketio.emit('title_refresh', current_random_music_name, broadcast=True)
            socketio.emit('music_content', '{"current_difficulty" : "'+str(round(current_difficulty, 2))+'", "current_default_difficulty" : "'+str(current_default_difficulty)+'", "count" : "' + str(current_count) + '"}', broadcast=True)
            time.sleep(1)
            #print(f'Counter for wait for song {n}: {i}')
            if is_all_skiped():
                clear_skips()
                break
        if stop_thread:
            break
    socketio.emit('title_refresh', f"Acabou!", broadcast=True)
    time.sleep(2)
    socketio.emit('go_to_lobby', "", broadcast=True)
    add_points_player()
    players_ready = []
    room_thread = None



### Choose Music ###

def choose_random_music():
    global current_random_music, current_random_time, current_random_movie, current_random_music_name, random_movies, default_mode, percentage_mode

    random_movies = copy.deepcopy(movies)
    random.shuffle(random_movies)
    current_random_movie = random_movies[0]
    print("current_random_movie", current_random_movie)
    musics = os.listdir(os.path.join(path_to_music, current_random_movie))
    if default_mode == "on":
        musics = choose_random_music_by_default_mode(musics)
    elif percentage_mode == "on":
        musics = choose_random_music_by_percentage_mode(musics)
    random.shuffle(musics)
    if len(musics) > 0:
        current_random_music_name = musics[0]
        current_random_music = os.path.abspath(os.path.join(path_to_music, current_random_movie, current_random_music_name))
        
        audio = AudioSegment.from_file(current_random_music, format="mp3")
        duration = int(len(audio) / 1000) # seconds
        print("Duration:",duration)
        if duration <= 20:
            current_random_time = 0
        else:
            current_random_time = random.randint(1, duration - song_duration)
        print("current_random_time:",current_random_time)
        print(current_random_music,"(",current_random_time,"sec )")
    else:
        print("THERE ARE NO SONGS FOR THAT PERCENTAGE OR DIFFICULTY")
        current_random_music = ""

def choose_random_music_by_default_mode(musics):
    global easy, medium, hard, current_random_movie
    with open(musics_json_filename, 'r') as musicdb:
        music_data = json.load(musicdb)
    current_data_movie_musics = {}
    for key_movie, value_movie in enumerate(music_data):
        if value_movie["movie"] == current_random_movie:
            current_data_movie_musics = music_data[key_movie]["musics"]
    musics_by_mode = []
    for music in musics:
        for key_data_music, value_data_music in enumerate(current_data_movie_musics):
            if easy == "on" and value_data_music["name"] == music and value_data_music["difficulty_defualt"] == "easy":
                musics_by_mode.append(music)
            elif medium == "on" and value_data_music["name"] == music and value_data_music["difficulty_defualt"] == "medium":
                musics_by_mode.append(music)
            elif hard == "on" and value_data_music["name"] == music and value_data_music["difficulty_defualt"] == "hard":
                musics_by_mode.append(music)
    return musics_by_mode

def choose_random_music_by_percentage_mode(musics):
    global easy, medium, hard, current_random_movie
    with open(musics_json_filename, 'r') as musicdb:
        music_data = json.load(musicdb)
    current_data_movie_musics = {}
    for key_movie, value_movie in enumerate(music_data):
        if value_movie["movie"] == current_random_movie:
            current_data_movie_musics = music_data[key_movie]["musics"]
    musics_by_mode = []
    for music in musics:
        for key_data_music, value_data_music in enumerate(current_data_movie_musics):
            if easy == "on" or medium == "on" or hard == "on":
                if easy == "on" and value_data_music["name"] == music and value_data_music["difficulty"] >= 75:
                    musics_by_mode.append(music)
                elif medium == "on" and value_data_music["name"] == music and value_data_music["difficulty"] > 35 and value_data_music["difficulty"] < 75:
                    musics_by_mode.append(music)
                elif hard == "on" and value_data_music["name"] == music and value_data_music["difficulty"] <= 35:
                    musics_by_mode.append(music)
            else:
                if value_data_music["name"] == music and value_data_music["difficulty"] >= current_percentage_range[0] and value_data_music["difficulty"] <= current_percentage_range[1]:
                    musics_by_mode.append(music)
    return musics_by_mode



### Replies and Points ###

def update_replys(username, reply_movie):
    global current_replys_and_points_room
    for reply in current_replys_and_points_room:
        if reply["username"] == username:
            reply["movie"] = reply_movie
            break

def clean_replys():
    global current_replys_and_points_room
    players_in_game = get_players_in_game()
    for player in players_in_game:
        existPlayer = False
        for reply in current_replys_and_points_room:
            if player == reply["username"]:
                reply["movie"] = ""
                reply["correct"] = ""
                existPlayer = True
                break
        if not existPlayer:
            current_replys_and_points_room.append({"username" : player, "movie" : "", "correct" : "", "points" : 0, "skip" : False})

def clean_points():
    global current_replys_and_points_room
    current_replys_and_points_room = []
    players_in_game = get_players_in_game()
    for player in players_in_game:
        current_replys_and_points_room.append({"username" : player, "movie" : "", "correct" : "", "points" : 0, "skip" : False})   

def verify_replys():
    global current_replys_and_points_room, current_random_movie
    for reply in current_replys_and_points_room:
        print("Movie Reply:",reply["movie"])
        print("Correct Movie:",current_random_movie)
        if reply["movie"].lower() == current_random_movie.lower():
            reply["correct"] = "true"
            update_player_point(reply["username"])
        else:
            reply["correct"] = "false"

def update_player_point(username):
    for player in current_replys_and_points_room:
        if username == player["username"]:
            player["points"] += 1

def get_players_in_game():
    global currents_players, leader, players_ready
    players_in_game = []
    for player in currents_players:
        if player == leader:
            players_in_game.append(player)
        elif player in players_ready:
            players_in_game.append(player)
    return players_in_game



### Difficulties ###

def calculate_difficulty():
    global current_random_movie, current_random_music_name, current_replys_and_points_room, current_difficulty, current_default_difficulty, current_count

    with open(musics_json_filename, 'r') as musicdb:
        current_data = json.load(musicdb)

    for key_movie, value_movie in enumerate(current_data):
        if value_movie["movie"] == current_random_movie:
            for key_music, value_music in enumerate(current_data[key_movie]["musics"]):
                if value_music["name"] == current_random_music_name:
                    old_count = copy.deepcopy(current_data[key_movie]["musics"][key_music]["count"])
                    old_correct_count = old_count * copy.deepcopy(current_data[key_movie]["musics"][key_music]["difficulty"]) / 100.0

                    current_correct_count = 0
                    print("Calculate Difficulty with", current_replys_and_points_room)
                    for reply in current_replys_and_points_room:
                        if reply["correct"] == "true":
                            current_correct_count+=1
                    new_difficulty = (old_correct_count + current_correct_count) / (old_count + len(current_replys_and_points_room)) * 100
                    
                    print("Difficulty = ", new_difficulty)

                    current_data[key_movie]["musics"][key_music]["count"] += len(current_replys_and_points_room)
                    current_data[key_movie]["musics"][key_music]["difficulty"] = new_difficulty

                    current_difficulty = current_data[key_movie]["musics"][key_music]["difficulty"]
                    current_default_difficulty = current_data[key_movie]["musics"][key_music]["difficulty_defualt"]
                    current_count = current_data[key_movie]["musics"][key_music]["count"]

    with open(musics_json_filename, 'w') as musicdb:
        json.dump(current_data, musicdb, indent=4)

def create_music_json():
    data = []
    for movie in movies:
        musics_json = []
        musics = os.listdir(os.path.join(path_to_music, movie))
        for music in musics:
            music_json = {"name" : music, "count" : 0, "difficulty" : 0, "difficulty_defualt" : "hard"}
            musics_json.append(music_json)
        movie_json = {"movie" : movie, "musics" : musics_json}
        data.append(movie_json)

    with open("_musics.json", 'w') as musicsdb:
        json.dump(data, musicsdb, indent=4)



### Skip ###

@app.route('/skip', methods=['POST'])
def skip():
    global current_replys_and_points_room

    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    
    if player is not None:
        print(player["username"],"skip!")
        for reply in current_replys_and_points_room:
            if reply["username"] == player["username"]:
                reply["skip"] = True
                break

    return jsonify({'status': 'Message receive with success'})

def is_all_skiped():
    global current_replys_and_points_room
    all_skiped = True
    for reply in current_replys_and_points_room:
        if not reply["skip"]:
            all_skiped = False
            break
    return all_skiped

def clear_skips():
    global current_replys_and_points_room
    for reply in current_replys_and_points_room:
        reply["skip"] = False



### Music Player ###

@socketio.on("/send_movie")
def send_movie(intput):
    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    print("Reply from ", player, "with username", player["username"], "with movie", intput)
    update_replys(player["username"], intput)

@app.route("/play")
def play():
    global current_random_music
    print("Play:", current_random_music)
    return send_file(current_random_music, as_attachment=False)

@app.route("/song")
def song():
    url = request.args.get('url')
    print(url)
    return send_file(url, as_attachment=False)


### Images ###

@app.route('/img/<path:filename>')
def img(filename):
    return send_from_directory('img', filename)

@app.route('/image', methods=['POST'])
def image():
    return jsonify({'status': 'Message receive with success', 'url' : 'img/' + current_random_movie + '.jpg'})



### Close ###

@app.route("/close")
def close():
    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    currents_players.remove(player["username"])
    return render_template("bye.html")



### Gets ###

@app.route('/get_all_players')
def get_all_players():
    update_playersdb()

    ip = request.remote_addr
    player = verify_player_exists("ip", ip)

    global all_players, currents_players, leader
    current_players_points = [[], "", player["username"], []]
    for player in currents_players:
        for player_in_all in all_players:
            if player == player_in_all["username"]:
                current_players_points[0].append(player_in_all)
    current_players_points[1] = leader
    current_players_points[3] = players_ready
    return current_players_points

@app.route('/get_players')
def get_players():
    global currents_players
    return currents_players

@app.route('/get_current_time')
def get_current_time():
    global current_random_time
    return current_random_time

@app.route('/get_movies', methods=['GET'])
def get_movies():
    global movies
    return movies

@app.route('/get_replys_and_points')
def get_replys():
    global current_replys_and_points_room
    return current_replys_and_points_room

@app.route('/favicon.ico')
def favicon():
    return send_file("favicon.ico", mimetype='image/ico0', as_attachment=False)

@app.route('/style.css')
def style():
    return send_file("style.css", as_attachment=False)



### Sets ###

@app.route('/receive_ready', methods=['POST'])
def receive_ready():
    global players_ready
    player_ready = request.json.get("user")
    print(player_ready,"ready!")
    if player_ready not in players_ready:
        players_ready.append(player_ready)
    return jsonify({'status': 'Message receive with success'})

@app.route('/return_lobby', methods=['POST'])
def return_lobby():
    global players_ready, room_thread, stop_thread

    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    
    if player is not None:
        print(player["username"],"returned to lobby!")
        if player["username"] in players_ready:
            players_ready.remove(player["username"])
    
        if player["username"] == leader:
            stop_thread = True
            socketio.emit('final_message', "", broadcast=True)
    
    return jsonify({'status': 'Message receive with success'})



if __name__ == '__main__':
    #create_music_json()
    socketio.run(app, port=44444, host='0.0.0.0', debug=True)