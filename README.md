# Hopper Chat

Chatbot (LLM) based voice assistance and smart speaker. These instructions will show you how to run Docker containers on a host system (e.g. laptop) and then run the Hopper Chat client on a separate system (so far, only tested on a Raspberry Pi).

## Hardware

You'll need a speaker and a microphone. The better the microphone, the better chance you'll have of the STT system understanding you. Here's what I used:

 * Microphone: [Upgraded USB Conference Microphone](https://www.amazon.com/gp/product/B08GPPQH9B/)
 * Speaker: [USB Mini Computer Speaker](https://www.amazon.com/gp/product/B075M7FHM1)

## Getting Started - Server

### Run LLM and TTS Servers

We're going to run the LLM and TTS servers on a more powerful computer (e.g. laptop) in Linux. 

Before you start, get the local IP address of your computer. It's probably listed under something like `wlan0`. Write it down--you'll need it when configuring the client.

```sh
ifconfig
```

You will need to install Docker. Follow one of these tutorials to do so:

 * Ubuntu: https://docs.docker.com/engine/install/debian/#os-requirements
 * Linux Mint: https://linuxiac.com/how-to-install-docker-on-linux-mint-21/

You will probably need to add the user to the `docker` group if you don't want to run Docker with admin privileges. This will solve the `permission denied` error when you try to run the `docker` commands below. From [this thread](https://stackoverflow.com/questions/48957195/how-to-fix-docker-got-permission-denied-issue):

```sh
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

You might need to reboot or restart Docker if you still get `permission denied` errors.

Next, download this repository.

```sh
git clone https://github.com/ShawnHymel/hopper-chat
```

Build the Ollama and Rhasspy Piper servers. It can take 5+ minutes to download the different models.

```sh
cd hopper-chat/
docker build -t ollama -f servers/ollama/Dockerfile .
docker build -t piper-tts -f servers/piper-tts/Dockerfile .
```

> **Note:** To build the servers for the NVIDIA Jetson Nano, use *servers/ollama/Dockerfile.orin* and *servers/piper-tts/Dockerfile.orin* instead. Note that both were tested and version pinned to [JetPack 6.0](https://developer.nvidia.com/embedded/jetpack-sdk-60dp).

Run the Ollama server.

```sh
docker run -it --rm -p 10802:10802 ollama
```

Open a new terminal and run the Rhasspy Piper TTS server.

```sh
docker run -it --rm -p 10803:10803 piper-tts
```

Note: you only need to run the `docker build` commands once. In the future, you can just do `docker run` for each of the servers.

If you need to completely remove the images for some reason, use:

```sh
docker image rm ollama
docker image rm piper-tts
docker builder prune
```

## Getting Started - Client

### Install Client OS

Next, we're going to run the client on a Raspberry Pi that performs STT and talks to the LLM and TTS servers across a local network.

Install [Raspberry Pi OS](https://www.raspberrypi.com/software/). This was tested on Raspberry Pi OS release 2024-03-15. In theory, this should work with the headless version (Raspberry Pi OS Lite), but I have not tested it.

Plug in the microphone and speaker.

### Install Dependencies

Install OS libraries:

```sh
sudo apt install -y libportaudio2 alsa-utils
```

If you are using the **Jetson Orin** as your client, you will need to install *venv*:

```sh
sudo apt install -y python3.10-venv
```

Download this repository.

```sh
git clone https://github.com/ShawnHymel/hopper-chat
cd hopper-chat
```

Make sure *pip* is up to date:

```sh
python -m pip install --upgrade pip
```

**Optional**: install Python packages and run everything in a virtual environment:

```sh
python -m venv venv
source venv/bin/activate
```

If you are running the client on a **Raspberry Pi**, you need to install the following dependencies manually:

```sh
python -m pip install gpiozero==2.0.1
```

If you are running the client on an **NVIDIA Jetson board**, you need to install a special version of *onnx-graphsurgeon* and the GPIO library. You will also need to set the correct user permissions to use the GPIO.

> **WARNING!** The GPIO library does not seem to be working on the Jetson Orin right now. It will run in software, but the pins do not toggle. This is a problem for future Shawn to fix.

```sh
python -m pip install onnx-graphsurgeon==0.5.2 Jetson.GPIO==2.1.6
sudo groupadd -f -r gpio
sudo usermod -a -G gpio $USER
sudo cp /home/$USER/.local/lib/python3.10/site-packages/Jetson/GPIO/99-gpio.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

After that, install the other dependencies. I pinned the versions to ensure everything would work together:

```sh
python -m pip install -r requirements.txt
```

### Setup

To start, you need to figure out the names and index numbers for your microphone and speaker. Run the following:

```sh
python -c "import sounddevice; print(sounddevice.query_devices())"
```

You should see something like the output below. Note the name and index number for each one.

```sh
Available sound devices:
   0 bcm2835 Headphones: - (hw:0,0), ALSA (0 in, 8 out)
   1 UM02: USB Audio (hw:1,0), ALSA (1 in, 0 out)
   2 UACDemoV1.0: USB Audio (hw:2,0), ALSA (0 in, 2 out)
   3 sysdefault, ALSA (0 in, 128 out)
   4 lavrate, ALSA (0 in, 128 out)
   5 samplerate, ALSA (0 in, 128 out)
   6 speexrate, ALSA (0 in, 128 out)
   7 pulse, ALSA (32 in, 32 out)
   8 upmix, ALSA (0 in, 8 out)
   9 vdownmix, ALSA (0 in, 6 out)
* 10 default, ALSA (32 in, 32 out)
```

In the above printout, my USB microphone is `1 UM02` and my USB speaker is `2 UACDemoV1.0`. 

Next, you'll likely want to adjust your speaker volume. Either do that through the desktop GUI or using *alsamixer*:

```sh
alsamixer
```

Press *F6* to view the individual audio devices. Select your speaker and adjust the volume to the desired level. Press *Esc* to save and exit alsamixer.

Edit *hopper-chat.conf*:

```sh
nano hopper-chat.conf
```

Change the input and output index numbers to match your desired audio devices. For example:

```python
AUDIO_INPUT_INDEX = 1
AUDIO_OUTPUT_INDEX = 2
```

Also in *hopper-chat.conf*, change the IP address of your server (the computer that's running Ollama and Piper TTS). For example:

```python
SERVER_IP = "10.0.42.1"
```

If, for some reason, your speaker cannot handle 48 kHz output, you will need to find out the sample rate of your speaker and change the output sample rate value:

```python
AUDIO_OUTPUT_SAMPLE_RATE = 48000
```

### Run!

Run the script, and it should start listening for the wake phrase ("Hey, Hopper!" by default) and responding to queries. Note that this is an LLM-based chatbot, so it can't perform active internet searches (e.g. "What's the weather like right now?").

```sh
python hopper-chat.py
```

> **Important!** You need to run the script once while your client is connected to the Internet so it can download the STT model. Once the model has been saved (cached), you can disconnect the client from the Internet to run the script again.

Note that you can copy the configuration file to somewhere else on your computer (so that your settings will be saved if you update the client code with e.g. `git pull`). You can pass the configuration file path to the application. For example:

```sh
python hopper-chat.py -c ~/Desktop/my-hopper.conf
```

## Troubleshooting

* If the TTS server gives you issues (e.g. you get an error like `Failed to get response from TTS server: 500`), then you can reset it with `sudo systemctl restart piper-tts.service`.

## License

Unless otherwise noted, all code is licensed under the [Zero-Clause BSD](https://opensource.org/license/0bsd) license.

**Zero-Clause BSD**

Permission to use, copy, modify, and/or distribute this software for
any purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED “AS IS” AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE
FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY
DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
