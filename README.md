# VocalLocal

A powerful speech-to-text application that uses OpenAI's Whisper API to provide accurate transcriptions in multiple languages.

## Features

- Real-time audio transcription
- Support for 60+ languages
- Multiple recording modes (fixed duration or key-triggered)
- Save transcripts to files
- Simple and intuitive interface

## Requirements

- Python 3.8+
- OpenAI API key
- PyAudio
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/radubobirnac/vocallocal.git
cd vocallocal
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment:
```bash
cp .env.example .env
```
Then edit `.env` and add your OpenAI API key.

## Usage

The project includes several versions of the application:

- `modsimple.py`: Simple modular version with language selection
- `realtimevocal.py`: Real-time transcription version
- `GUI.py`: Graphical user interface version
- `modular_vocal.py`: Core modular implementation

To run the simple modular version:
```bash
python modsimple.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/) 