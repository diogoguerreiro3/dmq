# 🎵 DMQ (Disney Music Quiz)

![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A real-time multiplayer music quiz game focused on animation movies soundtracks. Test your knowledge and compete with friends!

## ✨ Features

- 🎮 **Multiplayer Mode**: Play with friends in real-time using WebSockets
- 🎯 **Multiple Difficulty Levels**: Choose between easy, medium, and hard
- 📊 **Scoring System**: Track your progress and compete with other players
- 🎨 **Visual Interface**: Movie posters and user-friendly interface
- ⚙️ **Highly Customizable**: Filter by studio, language, difficulty, and more

## 📋 Prerequisites

- Python 3.13 or higher
- ffmpeg (for audio processing)

### Installing ffmpeg

**Windows:**
```bash
# Using chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

## 🚀 Quick Installation

### Windows

1. Clone the repository:
```bash
git clone https://github.com/diogoguerreiro3/dmq.git
cd dmq
```

2. Run the installation script:
```bash
install.bat
```

### Linux/macOS

1. Clone the repository:
```bash
git clone https://github.com/diogoguerreiro3/dmq.git
cd dmq
```

2. Make the script executable and run:
```bash
chmod +x install.sh
./install.sh
```

## 🎮 How to Use

### Windows
```bash
run.bat
```

### Linux/macOS
```bash
chmod +x run.sh
./run.sh
```

The server will start at `http://localhost:5000`

## 📁 Project Structure

```
dmq/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── install.bat            # Installation script (Windows)
├── install.sh             # Installation script (Linux/Mac)
├── run.bat                # Run script (Windows)
├── run.sh                 # Run script (Linux/Mac)
├── favicon.ico            # Application icon
├── style.css              # CSS styles
├── musics.json            # Music database
├── players.json           # Player data
├── img/                   # Movie posters
│   └── [Movie Posters].jpg
├── music/                 # Audio files (organize by movie)
│   └── [Movie Name]/
│       └── [songs].mp3
└── templates/             # HTML templates
    ├── index.html         # Home page
    ├── lobby.html         # Waiting room
    ├── audio.html         # Game page
    └── bye.html           # Exit page
```

## 🎵 Adding Music

1. Create a folder in `music/` with the movie name (e.g., `music/Frozen/`)
2. Add MP3 files to that folder
3. Add the poster image in `img/` with the same name (e.g., `img/Frozen.jpg`)
4. Add the movie and music to JSON database.

### musics.json Format

```json
{
    "movie": "Movie Name",
    "alternative_names": ["Alternative Name"],
    "studio": "Studio Name",
    "musics": [
        {
            "name": "music_file.mp3",
            "count": 0,
            "difficulty": 0,
            "difficulty_default": "medium",
            "lang": "en"
        }
    ]
}
```

## ⚙️ Configuration

### Environment Variables (Optional)

You can edit these variables in `app.py`:

```python
initial_waiting_duration = 7    # Seconds before starting
song_duration = 20              # Duration of each song
number_of_songs = 20            # Songs per game
```

## 🎯 Game Modes

### By Difficulty
- **Easy**: Most well-known songs
- **Medium**: Mix of well-known and obscure songs
- **Hard**: Less well-known songs

### By Studio
- Walt Disney Animation
- Pixar Animation Studios
- DisneyToon Studios
- Sony Pictures Animation

### By Language
- English
- Portuguese

### Percentage Mode
Set custom difficulty percentage (0-100%)

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 To-Do List

- Improvments in security
- Optimization of code
- Login system with cookies and tokens
- Song history
- Rating system for songs
- Date range filter

## 🐛 Known Issues

See the [Issues](https://github.com/diogoguerreiro3/dmq/issues) section to report bugs or suggest improvements.

## 📄 License

This project is distributed under the MIT License. See the `LICENSE` file for more details.

## 👤 Author

**Your Name**

- GitHub: [@diogoguerreiro3](https://github.com/diogoguerreiro3)

---

⭐ If you enjoyed this project, consider giving it a star!
