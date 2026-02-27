import os
import json
import time
import random
import copy
import threading
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    redirect,
    url_for,
    send_from_directory,
)
from flask_socketio import SocketIO

from mutagen.mp3 import MP3



app = Flask(__name__)
socketio = SocketIO(app)

verbose = True

# Thread-safety primitives
state_lock = threading.RLock()  # protects shared in-memory state
file_lock = threading.Lock()   # protects JSON read/write

BASE_DIR = Path(__file__).resolve().parent
MUSIC_DIR = BASE_DIR / "music"
IMG_DIR = BASE_DIR / "img"

movies = [movie for movie in os.listdir(MUSIC_DIR) if os.path.isdir(os.path.join(MUSIC_DIR, movie))]

player_json_filename = "players.json"
musics_json_filename = "musics.json"

currents_players = []
leader = ""
all_players = None

room_thread = None
stop_event = threading.Event()  # signal to stop the room thread
current_random_movie = "Snow White and the Seven Dwarfs"
current_random_music_name = "Snow White Soundtrack - 01 - Overture.mp3"
current_random_music = MUSIC_DIR / current_random_movie / current_random_music_name

movies_filter = []
filter_done_event = threading.Event()  # signal that filtering finished
sort_count = None

alternatives_movies = {}
movies_with_alternatives = []

current_random_time = 0
initial_waiting_duration = 7
waiting_duration = 7
song_duration = 20
music_silence_duration = 0
number_of_songs = 20

default_mode = percentage_mode = easy = medium = hard = percentage_mode_custom = percentage_mode_range = english = portuguese = soundtrack = waltdisneyanimation = disneytoon = pixar = dreamworks = sony = duplicate = None
current_percentage_range = []
current_difficulty = None
current_default_difficulty = None
current_count = None

current_replys_and_points_room = []
players_ready = []



### Auxiliar Functions ###

def update_playersdb():
    global all_players
    with file_lock:
        with open(player_json_filename, 'r', encoding='utf-8') as playersdb:
            players = json.load(playersdb)
    with state_lock:
        all_players = players

def verify_player_exists(way="", input=""):
    with file_lock:
        with open(player_json_filename, 'r', encoding='utf-8') as playersdb:
            players = json.load(playersdb)
    if len(players) > 0:
        for player in players:
            if player.get(way) == input:
                return player
                
def create_player(ip, username):
    player_data = {"ip": ip, "username": username, "points": 0}
    with file_lock:
        with open(player_json_filename, 'r', encoding='utf-8') as playersdb:
            current_data = json.load(playersdb)
        current_data.append(player_data)
        with open(player_json_filename, 'w', encoding='utf-8') as playersdb:
            json.dump(current_data, playersdb, indent=4)
    return player_data

def add_points_player():
    """Persist the points earned in the current room into players.json."""
    global current_replys_and_points_room

    with state_lock:
        replys_snapshot = copy.deepcopy(current_replys_and_points_room)

    with file_lock:
        with open(player_json_filename, 'r', encoding='utf-8') as playersdbread:
            players = json.load(playersdbread)

        if len(players) > 0:
            for player in players:
                for reply in replys_snapshot:
                    if reply["username"] == player.get("username"):
                        player["points"] = int(player.get("points", 0)) + int(reply.get("points", 0))

        with open(player_json_filename, 'w', encoding='utf-8') as playersdbwrite:
            json.dump(players, playersdbwrite, indent=4)



### Index ###


@app.route("/")
def index():
    global currents_players, leader

    ip = request.remote_addr
    print(ip, "enter in DMQ!")

    player = verify_player_exists("ip", ip)
    if player is not None:
        print("Found player", player)
        with state_lock:
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

        with state_lock:
            currents_players.append(player["username"])
        
        return redirect(url_for('lobby'))
    
    mensagem = f"The username {username} already exists. Try again."
    return render_template("index.html", msg=mensagem)



### Lobby ###

@app.route("/lobby")
def lobby():
    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    with state_lock:
        in_game = (player is not None and player["username"] in currents_players)
    if not in_game:
        return redirect(url_for('index'))
    return render_template("lobby.html", movies=alternatives_movies)

@app.route("/lobby/<msg>")
def lobby_msg(msg):
    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    with state_lock:
        in_game = (player is not None and player["username"] in currents_players)
    if not in_game:
        return redirect(url_for('index'))
    return render_template("lobby.html", movies=alternatives_movies)



### Main Room / Main Game ###

@app.route("/room")
def room():
    with state_lock:
        rt = room_thread
    if rt is None:
        return redirect(url_for('lobby'))
    return render_template("audio.html")

@app.route("/room", methods=['POST'])
def room_post():
    global room_thread, default_mode, percentage_mode, easy, medium, hard, percentage_mode_custom, percentage_mode_range, current_percentage_range, english, portuguese, soundtrack, waltdisneyanimation, disneytoon, pixar, dreamworks, sony, duplicate, sort_count
    with state_lock:
        rt_none = (room_thread is None)
    if rt_none:
        default_mode = request.form.get('default')
        percentage_mode = request.form.get('percentage')
        easy = request.form.get('easy')
        medium = request.form.get('medium')
        hard = request.form.get('hard')
        percentage_mode_custom = request.form.get('custom')
        percentage_mode_range = request.form.get('range')
        slider_values_str = request.form.get('sliderValue')
        current_percentage_range = list(map(int, slider_values_str.split(',')))
        english = request.form.get('english')
        portuguese = request.form.get('portuguese')
        soundtrack = request.form.get('soundtrack')
        waltdisneyanimation = request.form.get('waltdisneyanimation')
        disneytoon = request.form.get('disneytoon')
        pixar = request.form.get('pixar')
        dreamworks = request.form.get('dreamworks')
        sony = request.form.get('sony')
        duplicate = request.form.get('duplicate')
        sort_count = request.form.get('sort_count')
        if verbose:
            print(f"default_mode = {default_mode}; percentage_mode = {percentage_mode}; easy = {easy}; medium = {medium}; hard = {hard}; percentage_mode_custom: {percentage_mode_custom}; percentage_mode_range: {percentage_mode_range}; current_percentage_range: {current_percentage_range}; english: {english}; portuguese: {portuguese}; soundtrack: {soundtrack}; waltdisneyanimation: {waltdisneyanimation}; disneytoon: {disneytoon}; pixar: {pixar}; dreamworks: {dreamworks}; sony: {sony}; duplicate: {duplicate}; sort_count: {sort_count}")
        
        # Validate inputs
        if default_mode is None and percentage_mode is None:
            return redirect(url_for('lobby', msg="You have to select one of the modes to play!"))
        elif default_mode is not None and easy is None and medium is None and hard is None:
            return redirect(url_for('lobby', msg="You have to select one of the difficulties to play!"))
        elif percentage_mode is not None and percentage_mode_custom is None and percentage_mode_range is None:
            return redirect(url_for('lobby', msg="You have to select one of the percentage difficulties modes to play!"))
        elif percentage_mode is not None and percentage_mode_range is not None and easy is None and medium is None and hard is None:
            return redirect(url_for('lobby', msg="You have to select one of the difficulties to play!"))
        elif portuguese is None and english is None and soundtrack is None:
            return redirect(url_for('lobby', msg="You have to select at least one language or soundtrack!"))        

        if verbose:
            print("Create Filter Thread!")
        filter_thread = threading.Thread(target=filter_all_movies, daemon=True)
        filter_thread.start()

        if verbose:
            print("Create Room Thread!")
        rt = threading.Thread(target=main_room_thread, daemon=True)
        with state_lock:
            room_thread = rt
        rt.start()
        socketio.emit('go_to_room', "")
    return redirect(url_for('room'))

def main_room_thread():
    global current_random_time, room_thread, stop_event, current_random_music, current_difficulty, current_default_difficulty, current_count, players_ready
    stop_event.clear()
    clean_points()
    clean_replys()

    ## Initial Waiting ##

    for i in range(initial_waiting_duration+1,0,-1):
        if filter_done_event.is_set():
            if len(movies_filter) == 0:
                break
        socketio.emit('title_refresh', "Wait " + str(i) + " seconds ...")
        time.sleep(1)
        if verbose:
            print(f'Counter for wait: {i}')

    ## Main Game ##

    socketio.emit('title_refresh', f'Listen Carefully! ({song_duration})')
    for n in range(1,number_of_songs+1):
        clean_replys()
        clear_skips()
        choose_random_music()
        if current_random_music == "":
            break
        socketio.emit('music_content', '{"current_difficulty" : "", "current_default_difficulty" : ""}')

        ## Listen Music ##

        for i in range(song_duration,0,-1):
            current_time = current_random_time + song_duration - i
            if song_duration - (current_time - current_random_time) <= music_silence_duration:
                socketio.emit('audio_play', '{"command": "pause"}')
            else:
                socketio.emit('audio_play', '{"command": "play", "time": "' + str(current_time) + '"}')
            socketio.emit('title_refresh', f"[{n}] Listen Carefully! ({i})")
            time.sleep(1)
            if verbose:
                print(f'Counter for song {n}: {i} ({current_time})')
            if is_all_skiped():
                clear_skips()
                break
        socketio.emit('block_replies', '{"command": "block"}')

        ## Verify Replies ##

        verify_replys()
        calculate_difficulty()

        ## Show Results ##

        for i in range(waiting_duration+1,0,-1):
            socketio.emit('title_refresh', current_random_music_name)
            socketio.emit('music_content', '{"current_difficulty" : "' + str(round(current_difficulty, 2)) + '", "current_default_difficulty" : "' + str(current_default_difficulty) + '", "count" : "' + str(current_count) + '"}')
            time.sleep(1)
            if verbose:
                print(f'Counter for wait for song {n}: {i}')
            if is_all_skiped():
                clear_skips()
                break

        ## Prepare For Next Song ##

        socketio.emit('block_replies', '{"command": "unblock"}')
        socketio.emit('audio_play', '{"command": "pause"}')
        remove_choosen_music_from_filter()
        if stop_event.is_set():
            break
    socketio.emit('title_refresh', f"Acabou!")
    time.sleep(2)
    socketio.emit('go_to_lobby', "")
    add_points_player()
    with state_lock:
        players_ready = []
        room_thread = None
    stop_event.clear()



### Choose Music ###

def filter_all_movies():
    global movies_filter, default_mode, percentage_mode, easy, medium, hard, percentage_mode_custom, current_percentage_range, sort_count
    # Build the filtered list locally first, then publish it atomically under the lock.
    local_movies_filter = []

    # Reset completion flag for the new filter run
    filter_done_event.clear()

    # Read DB under file lock to avoid concurrent reads/writes while difficulty is being recalculated
    with file_lock:
        with open(musics_json_filename, 'r', encoding='utf-8') as musicdb:
            music_data = json.load(musicdb)

    for _, value_movie in enumerate(music_data):
        movie_group = (value_movie["movie"], [])

        if isStudio(value_movie):
            musics = value_movie["musics"]
            if sort_count is not None:
                musics = sorted(musics, key=lambda x: x["count"], reverse=False)

            for _, value_data_music in enumerate(musics):
                if default_mode:
                    if easy == "on" and value_data_music["difficulty_defualt"] == "easy" and isMusicLang(value_data_music):
                        movie_group[1].append(value_data_music["name"])
                    elif medium == "on" and value_data_music["difficulty_defualt"] == "medium" and isMusicLang(value_data_music):
                        movie_group[1].append(value_data_music["name"])
                    elif hard == "on" and value_data_music["difficulty_defualt"] == "hard" and isMusicLang(value_data_music):
                        movie_group[1].append(value_data_music["name"])
                else:
                    if percentage_mode_custom:
                        if easy == "on" and value_data_music["difficulty"] >= 75 and isMusicLang(value_data_music):
                            movie_group[1].append(value_data_music["name"])
                        elif medium == "on" and value_data_music["difficulty"] > 35 and value_data_music["difficulty"] < 75 and isMusicLang(value_data_music):
                            movie_group[1].append(value_data_music["name"])
                        elif hard == "on" and value_data_music["difficulty"] <= 35 and isMusicLang(value_data_music):
                            movie_group[1].append(value_data_music["name"])
                    else:
                        if current_percentage_range[0] <= value_data_music["difficulty"] <= current_percentage_range[1] and isMusicLang(value_data_music):
                            movie_group[1].append(value_data_music["name"])

        if len(movie_group[1]) > 0:
            local_movies_filter.append(movie_group)

    with state_lock:
        movies_filter = local_movies_filter

    filter_done_event.set()
    if verbose:
        print("Finished filtering of all movies...")

def isMusicLang(music):
    global english, portuguese, soundtrack
    return (music["lang"] == "en" and english is not None) or (music["lang"] == "pt" and portuguese is not None) or (music["lang"] == "un" and soundtrack is not None)

def isStudio(music):
    global waltdisneyanimation, disneytoon, pixar, dreamworks, sony
    return (music["studio"] == "Walt Disney Animation Studios" and waltdisneyanimation is not None) or \
            (music["studio"] == "Pixar Animation Studios" and pixar is not None) or \
            (music["studio"] == "DisneyToon Studios" and disneytoon is not None) or \
            (music["studio"] == "DreamWorks Animation" and dreamworks is not None) or \
            (music["studio"] == "Sony Pictures Animation" and sony is not None)

def get_song_duration(movie, music):
    current_music_data = MUSIC_DIR / movie / music
    return int(MP3(current_music_data).info.length)

def choose_random_music():
    global current_random_music, current_random_time, current_random_movie, current_random_music_name, movies_filter, sort_count

    with state_lock:
        # Shuffle in-place so that consecutive picks are randomized
        random.shuffle(movies_filter)

        if len(movies_filter) == 0:
            if verbose:
                print("There are no more movies ...")
            current_random_music = ""
            return

        current_random_movie = movies_filter[0][0]
        if verbose:
            print("Movie:", current_random_movie)

        musics = movies_filter[0][1]
        if len(musics) == 0:
            if verbose:
                print("There are no songs for that percentage or difficulty")
            current_random_music = ""
            return

        if sort_count is None:
            random.shuffle(musics)

        current_random_music_name = musics[0]
        current_random_music = os.path.abspath(os.path.join(MUSIC_DIR, current_random_movie, current_random_music_name))

    # Duration and random start time do not need to hold the lock (they only use the chosen values)
    duration = get_song_duration(current_random_movie, current_random_music_name)
    if verbose:
        print("Duration:", duration)

    if duration <= song_duration:
        current_random_time = 0
    else:
        current_random_time = random.randint(1, max(1, duration - song_duration))

    if verbose:
        print(f"{current_random_music} ( {current_random_time} sec )")


def remove_choosen_music_from_filter():
    global movies_filter, current_random_movie, current_random_music_name, duplicate

    with state_lock:
        if duplicate is not None:
            # remove entire movie group
            movies_filter = [movie_tuple for movie_tuple in movies_filter if movie_tuple[0] != current_random_movie]
        else:
            # remove only the chosen song from that movie group
            for movie_tuple in movies_filter:
                musics = movie_tuple[1]
                if current_random_music_name in musics:
                    musics.remove(current_random_music_name)



### Replies and Points ###

def update_replys(username, reply_movie):
    global current_replys_and_points_room
    with state_lock:
        for reply in current_replys_and_points_room:
            if reply["username"] == username:
                reply["movie"] = reply_movie
                break

def clean_replys():
    global current_replys_and_points_room
    players_in_game = get_players_in_game()
    with state_lock:
        for player in players_in_game:
            existPlayer = False
            for reply in current_replys_and_points_room:
                if player == reply["username"]:
                    reply["movie"] = ""
                    reply["correct"] = ""
                    existPlayer = True
                    break
            if not existPlayer:
                current_replys_and_points_room.append({"username": player, "movie": "", "correct": "", "points": 0, "skip": False})

def clean_points():
    global current_replys_and_points_room
    players_in_game = get_players_in_game()
    with state_lock:
        current_replys_and_points_room = []
        for player in players_in_game:
            current_replys_and_points_room.append({"username": player, "movie": "", "correct": "", "points": 0, "skip": False})


def verify_replys():

    global current_replys_and_points_room, current_random_movie, alternatives_movies

    with state_lock:
        current_movie = current_random_movie
        alt = copy.deepcopy(alternatives_movies)
        # Work on the shared list in-place but under the lock
        for reply in current_replys_and_points_room:
            print(f"{reply['username']} reply {reply['movie']} on {current_movie} song")
            valid_alternatives = [string.lower() for string in alt.get(current_movie, [])]
            if reply["movie"].lower() == current_movie.lower() or reply["movie"].lower() in valid_alternatives:
                reply["correct"] = "true"
                update_player_point(reply["username"])
            else:
                reply["correct"] = "false"


def set_alternatives_movies():

    global alternatives_movies

    with open(musics_json_filename, 'rb') as musicdb:
        music_data = json.loads(musicdb.read().decode('utf-8'))

    for key_movie, value_movie in enumerate(music_data):
        if "alternative_names" in value_movie:
            alternatives_movies[value_movie["movie"]] = value_movie["alternative_names"]
        else:
            alternatives_movies[value_movie["movie"]] = []
    #if verbose:
        #print(f"Alternatives Movies: {alternatives_movies}")

def set_movies_with_alternatives():
    global alternatives_movies, movies_with_alternatives
    for movie in alternatives_movies:
        movies_with_alternatives.append(movie)
        for alternative in alternatives_movies[movie]:
            movies_with_alternatives.append(alternative)
    #if verbose:
        #print(f"Movies with Alternatives: {movies_with_alternatives}")

def update_player_point(username):
    global current_replys_and_points_room
    with state_lock:
        for player in current_replys_and_points_room:
            if username == player["username"]:
                player["points"] += 1

def get_players_in_game():
    global currents_players, leader, players_ready
    with state_lock:
        currents_snapshot = list(currents_players)
        leader_snapshot = leader
        ready_snapshot = set(players_ready)

    players_in_game = []
    for player in currents_snapshot:
        if player == leader_snapshot:
            players_in_game.append(player)
        elif player in ready_snapshot:
            players_in_game.append(player)
    return players_in_game



### Difficulties ###


def calculate_difficulty():
    global current_random_movie, current_random_music_name, current_replys_and_points_room, current_difficulty, current_default_difficulty, current_count

    with state_lock:
        movie = current_random_movie
        music_name = current_random_music_name
        replies_snapshot = copy.deepcopy(current_replys_and_points_room)

    with file_lock:
        with open(musics_json_filename, 'r', encoding='utf-8') as musicdb:
            current_data = json.load(musicdb)

        for key_movie, value_movie in enumerate(current_data):
            if value_movie.get("movie") == movie:
                for key_music, value_music in enumerate(current_data[key_movie]["musics"]):
                    if value_music.get("name") == music_name:
                        old_count = int(current_data[key_movie]["musics"][key_music].get("count", 0))
                        old_difficulty = float(current_data[key_movie]["musics"][key_music].get("difficulty", 0))
                        old_correct_count = old_count * old_difficulty / 100.0

                        current_correct_count = 0
                        if verbose:
                            print(f"Calculate Difficulty with {replies_snapshot}")
                        for reply in replies_snapshot:
                            if reply.get("correct") == "true":
                                current_correct_count += 1

                        total_answers = old_count + len(replies_snapshot)
                        new_difficulty = 0.0
                        if total_answers > 0:
                            new_difficulty = (old_correct_count + current_correct_count) / total_answers * 100.0

                        if verbose:
                            print(f"Difficulty = {new_difficulty}")

                        current_data[key_movie]["musics"][key_music]["count"] = old_count + len(replies_snapshot)
                        current_data[key_movie]["musics"][key_music]["difficulty"] = new_difficulty

                        # update globals
                        with state_lock:
                            current_difficulty = new_difficulty
                            current_default_difficulty = current_data[key_movie]["musics"][key_music].get("difficulty_defualt")
                            current_count = current_data[key_movie]["musics"][key_music]["count"]
                        break

        with open(musics_json_filename, 'w', encoding='utf-8') as musicdb:
            json.dump(current_data, musicdb, indent=4)


def create_music_json():

    data = []
    for movie in movies:
        musics_json = []
        musics = os.listdir(os.path.join(MUSIC_DIR, movie))
        for music in musics:
            music_json = {"name" : music, "count" : 0, "difficulty" : 0, "difficulty_defualt" : "hard"}
            musics_json.append(music_json)
        movie_json = {"movie" : movie, "musics" : musics_json}
        data.append(movie_json)

    with open("_musics.json", 'w', encoding='utf-8') as musicsdb:
        json.dump(data, musicsdb, indent=4)

def add_language_music():
    with open(musics_json_filename, 'r', encoding='utf-8') as musicdb:
        music_data = json.load(musicdb)
    for key_movie, value_movie in enumerate(music_data):
        movie_group = (value_movie["movie"], [])
        current_data_movie_musics = value_movie["musics"]
        for key_data_music, value_data_music in enumerate(current_data_movie_musics):
            value_data_music["lang"] = "en"          

    with open("_musics.json", 'w', encoding='utf-8') as musicsdb:
        json.dump(music_data, musicsdb, indent=4)



### Skip ###

@app.route('/skip', methods=['POST'])
def skip():
    global current_replys_and_points_room

    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    
    if player is not None:
        print(player["username"],"skip!")
        with state_lock:
            for reply in current_replys_and_points_room:
                if reply["username"] == player["username"]:
                    reply["skip"] = True
                    break

    return jsonify({'status': 'Message receive with success'})

def is_all_skiped():
    global current_replys_and_points_room
    with state_lock:
        all_skiped = True
        for reply in current_replys_and_points_room:
            if not reply["skip"]:
                all_skiped = False
                break
        return all_skiped

def clear_skips():
    global current_replys_and_points_room
    with state_lock:
        for reply in current_replys_and_points_room:
            reply["skip"] = False



### Music Player ###

@socketio.on("/send_movie")
def send_movie(intput):
    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    print(f"{player['username']} reply the movie {intput}")
    update_replys(player["username"], intput)

@app.route("/play")
def play():
    global current_random_music
    print(f"Play >> {current_random_music}")
    return send_file(current_random_music, as_attachment=False)

@app.route("/music/<path:filename>")
def m(filename):
    return send_from_directory('music', filename)

@app.route("/current_music")
def music():
    global current_random_music_name, current_random_movie
    return jsonify({'url' : 'music/' + current_random_movie + "/" + current_random_music_name})

@app.route("/song")
def song():    
    filename = request.args.get("url")
    print(filename)

    safe_path = (MUSIC_DIR / filename).resolve()

    if not str(safe_path).startswith(str(MUSIC_DIR)):
        return "Forbidden", 403

    if not safe_path.exists():
        return "Not found", 404

    return send_file(safe_path, as_attachment=False)



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
    with state_lock:
        if player and player["username"] in currents_players:
            currents_players.remove(player["username"])
    return render_template("bye.html")



### Gets ###

@app.route('/get_all_players')
def get_all_players():
    update_playersdb()

    ip = request.remote_addr
    player = verify_player_exists("ip", ip)

    with state_lock:
        all_players_snapshot = copy.deepcopy(all_players) if all_players is not None else []
        currents_snapshot = list(currents_players)
        leader_snapshot = leader
        ready_snapshot = list(players_ready)

    current_players_points = [[], "", player["username"], []]
    for p in currents_snapshot:
        for p_all in all_players_snapshot:
            if p == p_all.get("username"):
                current_players_points[0].append(p_all)
    current_players_points[1] = leader_snapshot
    current_players_points[3] = ready_snapshot
    return current_players_points

@app.route('/get_players')
def get_players():
    global currents_players
    with state_lock:
        return list(currents_players)

@app.route('/get_current_time')
def get_current_time():
    global current_random_time
    return current_random_time

@app.route('/get_movies', methods=['GET'])
def get_movies():
    global movies
    return movies

@app.route('/get_movies_with_alternatives', methods=['GET'])
def get_movies_with_alternatives():
    global movies_with_alternatives
    return movies_with_alternatives

@app.route('/get_replys_and_points')
def get_replys():
    global current_replys_and_points_room
    with state_lock:
        return copy.deepcopy(current_replys_and_points_room)

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
    status_ready = request.json.get("status")
    with state_lock:
        if player_ready not in players_ready and status_ready is True:
            players_ready.append(player_ready)
            if verbose:
                print(f"{player_ready} is ready!")
        elif player_ready in players_ready and status_ready is False:
            players_ready.remove(player_ready)
            if verbose:
                print(f"{player_ready} is leave!")
    return jsonify({'status': 'Message receive with success'})

@app.route('/return_lobby', methods=['POST'])
def return_lobby():
    global players_ready, room_thread, stop_event

    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    
    if player is not None:
        if verbose:
            print(f"{player['username']} returned to lobby!")
        if player["username"] in players_ready:
            players_ready.remove(player["username"])
            return jsonify({'status': 'Message receive with success', 'player': 'player'})
    
        if player["username"] == leader:
            stop_event.set()
            socketio.emit('final_message', "")
            return jsonify({'status': 'Message receive with success', 'player': 'leader'})
    
    return jsonify({'status': 'No action'})





if __name__ == '__main__':
    #create_music_json()
    #add_language_music()
    set_alternatives_movies()
    set_movies_with_alternatives()

    if verbose: 
        socketio.run(app, port=44444, host='0.0.0.0', debug=True)
    else:
        socketio.run(app, port=44444, host='0.0.0.0', debug=False)