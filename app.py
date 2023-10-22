from flask import Flask, render_template, request, send_file, Response, redirect, url_for
from pytube import YouTube, Playlist
from googleapiclient.discovery import build
import random, requests, re, os, threading, time, json, threading, copy
from flask_socketio import SocketIO
from pydub import AudioSegment

app = Flask(__name__)
socketio = SocketIO(app)

path_to_music = './music/'
movies = [movie for movie in os.listdir(path_to_music) if os.path.isdir(os.path.join(path_to_music, movie))]

player_json_filename = 'players.json'

currents_players = []
all_players = None

room_thread = None
current_random_music = "C:\dev\programs\dmq\music\Snow White and the Seven Dwarfs\Snow White Soundtrack - 01 - Overture.mp3"
current_random_music_name = "Snow White Soundtrack - 01 - Overture"
current_random_movie = ""
current_random_time = 0
initial_waiting_duration = 15
waiting_duration = 7
song_duration = 20
number_of_songs = 10

current_replys_and_points_room = []



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
    ip = request.remote_addr
    print(ip,"entrou no DMQ!")
    
    player = verify_player_exists("ip", ip)
    if player != None:
        print("Found player", player)
        if player["username"] not in currents_players:
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
    if player["username"] not in currents_players: return redirect(url_for('index'))
    return render_template("lobby.html", movies=movies, players=currents_players)

### Main Room / Main Game ###

@app.route("/room")
def room():
    global room_thread
    if room_thread is None:
        print("Create Room Thread!")
        room_thread = threading.Thread(target=main_room_thread)
        room_thread.start()
    return render_template("audio.html")

def main_room_thread():
    global current_random_time, room_thread, current_random_music
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
        for i in range(song_duration+1,0,-1):
            current_time = current_random_time + song_duration - i
            socketio.emit('audio_play', '{"command": "play", "time": "' + str(current_time) + '"}', broadcast=True)
            socketio.emit('title_refresh', f"[{n}] Listen Carefully! ({i})", broadcast=True)
            time.sleep(1)
            #print(f'Counter for song {n}: {i}')
        socketio.emit('audio_play', '{"command": "pause"}', broadcast=True)
        verify_replys()
        for i in range(waiting_duration+1,0,-1):
            socketio.emit('title_refresh', current_random_music_name, broadcast=True)
            time.sleep(1)
            #print(f'Counter for wait for song {n}: {i}')
    socketio.emit('title_refresh', f"Acabou!", broadcast=True)
    add_points_player()
    room_thread = None

def choose_random_music():
    global current_random_music, current_random_time, current_random_movie, current_random_music_name, random_movies

    random_movies = copy.deepcopy(movies)
    random.shuffle(random_movies)
    current_random_movie = random_movies[0]
    musics = os.listdir(os.path.join(path_to_music, current_random_movie))
    random.shuffle(musics)
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

def update_replys(username, reply_movie):
    global current_replys_and_points_room
    for reply in current_replys_and_points_room:
        if reply["username"] == username:
            reply["movie"] = reply_movie
            break

def clean_replys():
    global current_replys_and_points_room, currents_players
    for player in currents_players:
        existPlayer = False
        for reply in current_replys_and_points_room:
            if player == reply["username"]:
                reply["movie"] = ""
                reply["correct"] = ""
                existPlayer = True
                break
        if not existPlayer:
            current_replys_and_points_room.append({"username" : player, "movie" : "", "correct" : "", "points" : 0})

def clean_points():
    global current_replys_and_points_room, currents_players
    current_replys_and_points_room = []
    for player in currents_players:
        current_replys_and_points_room.append({"username" : player, "movie" : "", "correct" : "", "points" : 0})   

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

@socketio.on("/send_movie")
def send_movie(intput):
    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    print("Reply from ", player, "with username", player["username"], "with movie", intput)
    update_replys(player["username"], intput)

@app.route("/play")
def play():
    global current_random_music
    print("play:", current_random_music)
    return send_file(current_random_music, as_attachment=False)

@app.route("/song")
def song():
    url = request.args.get('url')
    print(url)
    return send_file(url, as_attachment=False)

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
    global all_players, currents_players
    current_players_points = []
    for player in currents_players:
        for player_in_all in all_players:
            if player == player_in_all["username"]:
                current_players_points.append(player_in_all)
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











# @app.route("/stream")
# def stream():
#     # Inicia uma thread para reproduzir a música.
#     thread = threading.Thread(target=play_music)
#     thread.daemon = True
#     thread.start()

#     # Retorna uma resposta vazia para indicar que a solicitação foi bem-sucedida.
#     return ""

# # Função que reproduz a música.
# def play_music():
#     # Abre o arquivo de música.
#     with open(path_to_music, "rb") as f:
#         # Obtém o conteúdo do arquivo de música.
#         music_data = f.read()

#     # Inicia a reprodução da música.
#     print("Iniciando a reprodução da música.")
#     #flask.current_app.logger.info("Iniciando a reprodução da música.")
#     flask.streaming.stream_response(music_data, mimetype="audio/mp3")

# @app.route("/wav")
def streamwav():
    def generate():
        with open(path_to_music, "rb") as fwav:
            data = fwav.read(1024)
            while data:
                yield data
                data = fwav.read(1024)
    return Response(generate(), mimetype="audio/mpeg")


# Chave da API do YouTube (substitua pela sua própria chave)
YOUTUBE_API_KEY = 'AIzaSyBT2171JBehaT6EFm24iYkG3Cx6LfbQ8Iw'

# @app.route("/test")
def test():

    # URL da playlist do YouTube
    playlist_url = 'https://www.youtube.com/playlist?list=PLBqEHXu79cdu3VA-lVrLNOVU551e3MO5n'

    # Extrai o ID da playlist do URL
    playlist_id_match = re.search(r'[?&]list=([^&]+)', playlist_url)

    if playlist_id_match:
        PLAYLIST_ID = playlist_id_match.group(1)
    else:
        raise ValueError("Não foi possível extrair o ID da playlist do URL")

    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    # Obtém a lista de vídeos da playlist
    playlist_items = youtube.playlistItems().list(playlistId=PLAYLIST_ID, part='snippet').execute()
    videos = [item['snippet']['resourceId']['videoId'] for item in playlist_items['items']]

    print("videos:",videos)
    
    # Embaralha a ordem dos vídeos
    random.shuffle(videos)

    videos[0] = "tgTJUUBEBS8"

    playlist = [
        'https://www.youtube.com/watch?v=' + videos[0],
        'https://www.youtube.com/watch?v=' + videos[1],
        'https://www.youtube.com/watch?v=' + videos[2],
        # Adicione mais URLs conforme necessário
    ]

    

    # Embaralhar a ordem dos áudios
    random.shuffle(playlist)


    # audios = [
    #     {'title': 'Áudio 1', 'video_id': "tgTJUUBEBS8"},
    #     {'title': 'Áudio 2', 'video_id': videos[1]},
    #     {'title': 'Áudio 3', 'video_id': videos[2]}
    # ]

    # # Embaralhar a ordem dos áudios
    # random.shuffle(audios)

    # Retorna a página HTML
    return render_template("test.html", audios=videos)











# if __name__ == "__main__":
#     app.run(host="0.0.0.0", debug=True)

if __name__ == '__main__':
    socketio.run(app, port=44444, host='0.0.0.0', debug=True)