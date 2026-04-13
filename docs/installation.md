# Installation Guide

## System Requirements

- **Ubuntu 18.04+** or **Debian 10+**
- **Python 3.7+**
- **Working microphone**
- **Git** (for cloning)

## Step-by-Step Installation

### Step 1: Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pip python3-dev
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/francogalfre/jarvis-claude-code.git
cd jarvis-claude-code
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pyaudio numpy scipy pyttsx3
```

### Step 4: Make Installer Executable

```bash
chmod +x install_applause.sh
```

### Step 5: Run the Installer (Optional)

```bash
./install_applause.sh
```

This will:
- Install all dependencies
- Create a command alias
- Set up permissions

## Running the Detector

### Option 1: Direct Command

```bash
python3 src/applause_launcher.py
```

### Option 2: Using Alias (if installed)

```bash
applause
```

### Option 3: Background Process

```bash
nohup python3 src/applause_launcher.py > applause.log 2>&1 &
```

## Auto-Start on Boot

Create a file `~/.config/autostart/applause.desktop`:

```bash
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/applause.desktop << EOF
[Desktop Entry]
Type=Application
Name=Applause Detector
Exec=python3 $HOME/jarvis-claude-code/src/applause_launcher.py
X-GNOME-Autostart-enabled=true
EOF
```

## Verify Microphone

Test your microphone:

```bash
# Record for 3 seconds
arecord -d 3 test.wav

# Play it back
aplay test.wav
```

List audio devices:
```bash
pacmd list-sources | grep "name:"
```

Adjust microphone volume:
```bash
alsamixer
# Use arrow keys to navigate
# Press F4 to see "Capture" (input)
# Use ↑/↓ to adjust volume
# Press ESC to exit
```

## Troubleshooting Installation

### Error: "ModuleNotFoundError: No module named 'pyaudio'"

```bash
pip install --upgrade pip setuptools wheel
pip install pyaudio
```

If still fails:
```bash
sudo apt-get install python3-pyaudio
```

### Error: "portaudio19-dev not found"

```bash
sudo apt-get update
sudo apt-get install portaudio19-dev
```

### Error: "No module named 'scipy'"

```bash
pip install scipy
```

### Error: Permission denied on install_applause.sh

```bash
chmod +x install_applause.sh
./install_applause.sh
```

## Verify Installation

```bash
# Check Python version
python3 --version

# Check if pyaudio is installed
python3 -c "import pyaudio; print('✓ PyAudio OK')"

# Check if other libraries are installed
python3 -c "import numpy, scipy, pyttsx3; print('✓ All libraries OK')"

# Test the detector starts
python3 src/applause_launcher.py
# You should see: "🎤 Microphone initialized"
# Press Ctrl+C to stop
```

## Next Steps

1. **Customize your setup:**
   - Edit `src/applause_launcher.py` to change YouTube song
   - Adjust sensitivity in the same file
   - Change JARVIS phrases

2. **Test the detector:**
   - Run: `python3 src/applause_launcher.py`
   - Clap twice in front of the microphone
   - Should open Claude Code, Cursor, and YouTube

3. **Set up auto-start:**
   - Follow the "Auto-Start on Boot" section above

4. **Report issues:**
   - Open an issue on GitHub
   - Include error messages and your OS version

## Uninstall

```bash
# Remove the repository
rm -rf ~/jarvis-claude-code

# Remove the alias (if created)
# Edit ~/.bashrc and remove the line:
# alias applause='python3 ~/jarvis-claude-code/src/applause_launcher.py'

# Uninstall Python packages (if needed)
pip uninstall pyaudio numpy scipy pyttsx3
```

## Get Help

- **Questions:** [GitHub Discussions](https://github.com/francogalfre/jarvis-claude-code/discussions)
- **Bugs:** [GitHub Issues](https://github.com/francogalfre/jarvis-claude-code/issues)
- **Configuration:** Check [config/config.example.md](../config/config.example.md)