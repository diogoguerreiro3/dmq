from flask import Flask, render_template, request, send_file, Response, redirect, url_for
from pytube import YouTube, Playlist
from googleapiclient.discovery import build
import random, requests, re, os, threading, time, json
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

path_to_music = './music/'
movies = [movie for movie in os.listdir(path_to_music) if os.path.isdir(os.path.join(path_to_music, movie))]

player_json_filename = 'players.json'

currents_players = []

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

    # Retorna a página HTML
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
    return mensagem

@app.route("/lobby")
def lobby():
    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    if player["username"] not in currents_players: return redirect(url_for('index'))
    return render_template("lobby.html", movies=movies, players=currents_players)

@app.route("/room")
def room():
    return render_template("audio.html")

@app.route("/close")
def close():
    ip = request.remote_addr
    player = verify_player_exists("ip", ip)
    currents_players.remove(player["username"])
    return render_template("bye.html")

@app.route("/play")
def play():
    random.shuffle(movies)
    random_movie = movies[0]
    musics = os.listdir(os.path.join(path_to_music, random_movie))
    random.shuffle(musics)
    random_music = musics[0]
    print(os.path.join(path_to_music, random_movie, random_music))
    return send_file(os.path.join(path_to_music, random_movie, random_music), as_attachment=False)

@socketio.on('play_audio')
def play_audio(data):
    print("triggered play_audio")
    # Reproduza o áudio quando receber um comando "play_audio" do cliente
    socketio.emit('audio_played', data, broadcast=True)

@app.route('/get_players')
def get_players():
    return currents_players

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