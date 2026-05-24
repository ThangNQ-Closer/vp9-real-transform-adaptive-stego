# vp9-real-transform-adaptive-stego

Real VP9 transform-domain adaptive steganography Labtainer lab using a patched `libvpx` VP9 encoder.

The lab patches `vp9/encoder/vp9_tokenize.c` so the encoder can log and modify real quantized transform coefficients (`qcoeff`) after transform/quantization and before token emission. The embedded payload is:

```text
KHOA ATTT PTIT
```

This public repository intentionally does **not** include the original `sender/input_video.mp4`. If no input video is present, `sender/prepare_input.py` generates a deterministic 5-second `ffmpeg testsrc2` video so the lab can run independently.


## Install Directly With `imodule`

On a Labtainer VM:

```bash
imodule https://raw.githubusercontent.com/ThangNQ-Closer/vp9-real-transform-adaptive-stego/main/imodule/vp9-real-transform-adaptive-stego.tar
labtainer vp9-real-transform-adaptive-stego
```

The imodule start config uses DockerHub registry `closer031004`, so Labtainer can pull these images directly:

```text
closer031004/vp9-real-transform-adaptive-stego.sender.student:latest
closer031004/vp9-real-transform-adaptive-stego.receiver.student:latest
```

## Using Your Own Real MP4 Instead Of The Demo Fallback

This public repository does not ship the original media file. To run the lab with a real MP4 on another machine, place it as `sender/input_video.mp4` and rebuild local images:

```bash
cd ~/labtainer/trunk/labs/vp9-real-transform-adaptive-stego
./scripts/add_input_video_and_rebuild.sh /path/to/input_video.mp4
labtainer vp9-real-transform-adaptive-stego
```

To distribute a private imodule that includes your MP4:

```bash
./scripts/make_private_video_imodule.sh /path/to/input_video.mp4 /tmp/vp9-real-transform-adaptive-stego-with-video.tar
imodule file:///tmp/vp9-real-transform-adaptive-stego-with-video.tar
cd ~/labtainer/trunk/labs/vp9-real-transform-adaptive-stego
./scripts/build_local_images.sh
```

## Quick Start With DockerHub Images

From a Labtainer VM, copy or clone this lab into:

```bash
~/labtainer/trunk/labs/vp9-real-transform-adaptive-stego
```

Pull the prebuilt images and tag them with the names expected by Labtainer:

```bash
cd ~/labtainer/trunk/labs/vp9-real-transform-adaptive-stego
./scripts/pull_dockerhub_images.sh
```

Start the lab:

```bash
labtainer vp9-real-transform-adaptive-stego
```

## Build Images Locally Instead

```bash
cd ~/labtainer/trunk/labs/vp9-real-transform-adaptive-stego
./scripts/build_local_images.sh
```

## Sender Workflow

```bash
./view_input_video.sh --serve
python3 prepare_input.py
./build_libvpx.sh
python3 patch_libvpx.py
./build_libvpx.sh
./encode_cover.sh
./encode_logonly.sh
./encode_stego.sh
python3 inspect_embed_log.py --input embed_log.json
```

To view video from the sender container, keep `./view_input_video.sh --serve` running and open the printed URL in Firefox on the Ubuntu VM, for example:

```text
http://172.20.0.2:8000/view_input_video.html
```

## Receiver Workflow

```bash
python3 verify_stego.py \
  --cover /shared/cover.ivf \
  --stego /shared/stego.ivf \
  --embed-log /shared/embed_log.json \
  --output verify_report.json
python3 extract_metrics.py --report verify_report.json
```

## Checkwork

```bash
checkwork vp9-real-transform-adaptive-stego
```

Expected checks:

```text
Y - input_video_ready
Y - libvpx_built
Y - cover_encoded
Y - stego_encoded
Y - receiver_verified
Y - labtainer_outputs_ready
```

## DockerHub

Prebuilt images are published as:

```text
closer031004/vp9-real-transform-adaptive-stego:sender-student
closer031004/vp9-real-transform-adaptive-stego:receiver-student
```
