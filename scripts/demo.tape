# VHS tape — renders a social-ready demo of abom scan + verify.
#
# One-time:  brew install vhs ffmpeg ttyd     (https://github.com/charmbracelet/vhs)
#            pipx install --python python3.12 abom-cli   (any Python >=3.10; pipx puts `abom` on PATH)
# Record:    vhs scripts/demo.tape             (run from the repo root)
# Outputs:   assets/demo.gif  +  assets/demo.mp4  (upload the .mp4 to LinkedIn)

Output assets/demo.gif
Output assets/demo.mp4

Set Shell "bash"
Set FontSize 26
Set Width 1280
Set Height 720
Set Padding 28
Set TypingSpeed 55ms
Set Theme "Dracula"

# --- setup (not recorded): isolate a clean working dir from the example ------
Hide
Type "export PATH=$HOME/.local/bin:$PATH && mkdir -p /tmp/abom-demo && cp -r examples/langchain-support-agent/. /tmp/abom-demo/ && cp examples/policy.json /tmp/abom-demo/ && cd /tmp/abom-demo && export ABOM_KEY=/tmp/abom-demo-key.pem && export PS1='$ ' && clear"
Enter
Sleep 1.5s
Show

# --- the demo ----------------------------------------------------------------
Type "abom scan ."
Sleep 500ms
Enter
Sleep 3s

Type "abom verify abom.json --policy policy.json"
Sleep 500ms
Enter
Sleep 4s
