# VocalLocal

A powerful speech-to-text application that uses OpenAI's Whisper API to provide accurate transcriptions in multiple languages.

## Features

- Real-time audio transcription
- Support for 60+ languages
- Multiple recording modes (fixed duration or key-triggered)
- Save transcripts to files
- Simple and intuitive interface
- Web interface for deployment on Render

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

### Desktop Applications

The project includes several versions of the application:

- `modsimple.py`: Simple modular version with language selection
- `realtimevocal.py`: Real-time transcription version
- `GUI.py`: Graphical user interface version
- `modular_vocal.py`: Core modular implementation

To run the simple modular version:
```bash
python modsimple.py
```

### Web Application

The project also includes a web interface that can be deployed to Render or run locally:

To run the web application locally:
```bash
flask run
```

## Deployment to Render

1. **Fork or clone this repository**

2. **Create a new Web Service on Render**
   - Sign up for a [Render](https://render.com/) account if you don't have one
   - Go to your Render dashboard and click "New +" > "Web Service"
   - Connect your GitHub repository
   - Name your service (e.g., "vocallocal")
   - Select "Python" as the Environment
   - Set the Build Command to:
     ```
     ./build.sh
     ```
   - Set the Start Command to:
     ```
     gunicorn app:app
     ```

3. **Add Environment Variables**
   - Add your `OPENAI_API_KEY` to the environment variables section
   - Add `SECRET_KEY` for Flask session security

4. **Deploy your service**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

## Troubleshooting Deployment

If you encounter issues with PyAudio installation on Render, try these steps:

1. **Use the build.sh script** - This script installs the necessary system dependencies for PyAudio.

2. **Alternative: Use render.yaml** - This configuration file can also be used to set up your deployment.

3. **Check Render logs** - If your deployment fails, check the logs for specific errors.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Development Workflow

### Git Operations

For quick and efficient git operations, use the `git-push.py` script:

```bash
# Stage, commit, and push all changes in one command
python git-push.py "Your commit message"
```

This script handles:
1. Staging all changes
2. Committing with your message
3. Pushing to the default remote branch

No need for separate git add, commit, and push commands!

## License

[MIT](https://choosealicense.com/licenses/mit/)