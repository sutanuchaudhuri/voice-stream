#!/bin/bash

FFMPEG_PATH="/opt/homebrew/bin/ffmpeg"
PROFILE_FILE="$HOME/.zshrc" # Or .bash_profile for Bash

echo "Checking FFmpeg installation and PATH..."

# 1. Check if FFmpeg executable exists
if [ -f "$FFMPEG_PATH" ]; then
    echo "FFmpeg executable found at $FFMPEG_PATH."
else
    echo "FFmpeg executable not found at $FFMPEG_PATH."
    echo "Please ensure FFmpeg is installed, e.g., using Homebrew: brew install ffmpeg"
    exit 1
fi

# 2. Check if FFmpeg is already in PATH
if command -v ffmpeg &> /dev/null; then
    echo "FFmpeg is already in your PATH."
else
    echo "FFmpeg is not currently in your PATH. Adding it..."

    # Check if the profile file exists, create if not
    if [ ! -f "$PROFILE_FILE" ]; then
        touch "$PROFILE_FILE"
        echo "Created $PROFILE_FILE."
    fi

    # Add /opt/homebrew/bin to PATH if not already present
    if ! grep -q "export PATH=.*:/opt/homebrew/bin" "$PROFILE_FILE"; then
        echo "export PATH=\"/opt/homebrew/bin:\$PATH\"" >> "$PROFILE_FILE"
        echo "Added /opt/homebrew/bin to PATH in $PROFILE_FILE."
    else
        echo "/opt/homebrew/bin is already included in PATH in $PROFILE_FILE."
    fi

    echo "Please restart your terminal or run 'source $PROFILE_FILE' for changes to take effect."
fi

echo "Validation complete."