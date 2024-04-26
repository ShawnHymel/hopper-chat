# Hopper Chat

Chatbot (LLM) based voice assistance and smart speaker.

## Hardware

You'll need a speaker and a microphone. The better the microphone, the better chance you'll have of the STT system understanding you. Here's what I used:

 * Microphone: [Upgraded USB Conference Microphone](https://www.amazon.com/gp/product/B08GPPQH9B/)
 * Speaker: [USB Mini Computer Speaker](https://www.amazon.com/gp/product/B075M7FHM1)

## Getting Started

### Run LLM and TTS servers

We're going to run the LLM and TTS servers on a more powerful computer (e.g. laptop) in Linux. 

Before you start, get the local IP address of your computer. It's probably listed under something like `wlan0`. Write it down--you'll need it when configuring the client.

```sh
ifconfig
```

You will need to install Docker. Follow one of these tutorials to do so:

 * Ubuntu: https://docs.docker.com/engine/install/debian/#os-requirements
 * Linux Mint: https://linuxiac.com/how-to-install-docker-on-linux-mint-21/

Next, download this repository.

```sh
git clone https://github.com/ShawnHymel/hopper-chat
```

Run the Ollama server. It will take ~5 min to download the Llama3:8B model during the build phase.

```sh
cd hopper-chat/servers/ollama/
docker build -t ollama .
docker run -it --rm -p 10802:10802 ollama
```

Open a new terminal and run the Rhasspy Piper TTS server.

```sh
cd hopper-chat/servers/piper-tts/
docker build -t piper-tts .
docker run -it --rm -p 10803:10803 piper-tts
```

Note: you only need to run the `docker build` commands once. In the future, you can just do `docker run` for each of the servers.

### Install client OS

Next, we're going to run the client on a Raspberry Pi that performs STT and talks to the LLM and TTS servers across a local network.

Install [Raspberry Pi OS](https://www.raspberrypi.com/software/). This was tested on Raspberry Pi OS release 2023-05-03. In theory, this should work with the headless version (Raspberry Pi OS Lite), but I have not tested it.

Plug in the microphone and speaker.

### Install Dependencies

Make sure *pip* is up to date:

```sh
python -m pip install –upgrade pip
```

**Optional**: install Python packages and run everything in a virtual environment:

```sh
python -m venv venv
source venv/bin/activate
```

Install other dependencies. I pinned the versions to ensure everything would work together:

```sh
python -m pip install requests==2.25.1 sounddevice==0.4.6 vosk==0.3.45 python-dotenv==1.0.1 openai==1.23.2 resampy==0.4.3 ollama==0.1.9
```

TODO: put the above into a *requirements.txt* file.

### Setup

Download this repository.

```sh
git clone https://github.com/ShawnHymel/hopper-chat
cd hopper-chat
```

To start, you'll likely want to adjust your speaker volume. Either do that through the desktop GUI or using *alsamixer*:

```sh
sudo apt install alsa-utils
alsamixer
```

Run the script once to get a printout of available audio systems. Note the index number for each one.

```sh
$ python hopper-gpt.py 
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
...
```

In the above printout, my USB microphone is `1 UM02` and my USB speaker is `2 UACDemoV1.0`. In *hopper-llama.py*, change the input and output index numbers to match your desired audio devices:

```python
AUDIO_INPUT_INDEX = 1
AUDIO_OUTPUT_INDEX = 2
```

Also in *hopper-llama.py*, change the IP address of your server:

```python
SERVER_IP = "10.0.0.143"
```

If, for some reason, your speaker cannot handle 48 kHz output, you will need to find out the sample rate of your speaker and change the output sample rate value:

```python
AUDIO_OUTPUT_SAMPLE_RATE = 48000
```

### Run!

Simply run the script, and it should start listening for the wake phrase ("hey, Hopper!" by default) and responding to queries. Note that this is an LLM-based chatbot, so it can't perform active internet searches (e.g. "What's the weather like right now?").

```sh
python hopper-llama.py
```

## License

Unless otherwise noted, all code is licensed under the [Zero-Clause BSD](https://opensource.org/license/0bsd) license.

Zero-Clause BSD
=============

Permission to use, copy, modify, and/or distribute this software for
any purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED “AS IS” AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE
FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY
DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
