How to use the script:
Save the script: Save the code above into a file, for example, add_ffmpeg_to_path.sh.
Make it executable: Open your Terminal and run chmod +x add_ffmpeg_to_path.sh.
Run the script: Execute the script using ./add_ffmpeg_to_path.sh.
Notes:
This script prioritizes .bash_profile for Bash users. If you use Zsh, change PROFILE_FILE="$HOME/.bash_profile" to PROFILE_FILE="$HOME/.zshrc".
The script adds /usr/local/bin to your PATH. If your FFmpeg installation is in a different location, adjust FFMPEG_PATH and the export PATH line accordingly.
After running the script, you must restart your Terminal or run source ~/.bash_profile (or source ~/.zshrc) for the PATH changes to become active in your current session.



