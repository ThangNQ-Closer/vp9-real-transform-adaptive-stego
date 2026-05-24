#!/bin/bash
set -e
PORT=8000
SERVE=0
if [ "${1:-}" = "--serve" ]; then
    SERVE=1
    if [ -n "${2:-}" ]; then PORT="$2"; fi
fi

INPUT="$HOME/input_video.mp4"
if [ ! -f "$INPUT" ]; then
    if [ -f "input_video.mp4" ]; then
        INPUT="input_video.mp4"
    else
        echo "input_video.mp4 was not found; generating a 5-second demo preview video."
        INPUT="$HOME/video_view/generated_input_video.mp4"
        mkdir -p "$HOME/video_view"
        ffmpeg -y -hide_banner -loglevel error -f lavfi -i testsrc2=size=320x180:rate=15 -t 5 -pix_fmt yuv420p "$INPUT"
    fi
fi

VIEWDIR="$HOME/video_view"
mkdir -p "$VIEWDIR"
cp "$INPUT" "$VIEWDIR/input_video.mp4"
ffmpeg -y -hide_banner -loglevel error -i "$INPUT" -frames:v 1 "$VIEWDIR/input_video_preview.jpg"
ffmpeg -y -hide_banner -loglevel error -i "$INPUT" -t 5 -vf "scale=320:-2,fps=15" -c:v libx264 -pix_fmt yuv420p "$VIEWDIR/input_video_preview.mp4"
cat > "$VIEWDIR/view_input_video.html" <<'HTML'
<!doctype html>
<html>
<head><meta charset="utf-8"><title>VP9 Lab Input Video</title></head>
<body style="font-family:sans-serif;margin:24px">
<h2>VP9 Lab Input Video</h2>
<video width="640" controls src="input_video.mp4"></video>
<p>Fallback preview:</p>
<video width="640" controls src="input_video_preview.mp4"></video>
<p>Still frame:</p>
<img src="input_video_preview.jpg" style="max-width:640px;width:100%">
</body>
</html>
HTML

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$IP" ]; then IP="172.20.0.2"; fi

echo "Created video viewing files in $VIEWDIR"
echo "To view inside the VM browser, run:"
echo "  ./view_input_video.sh --serve"
echo "Then open this URL in Firefox on the Ubuntu VM:"
echo "  http://$IP:$PORT/view_input_video.html"
echo "Press Ctrl-C in this terminal to stop the web server."

if [ "$SERVE" = "1" ]; then
    echo "Starting web server at http://$IP:$PORT/view_input_video.html"
    cd "$VIEWDIR"
    python3 -m http.server "$PORT"
fi
