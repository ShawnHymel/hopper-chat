# Hopper Chat

Chatbot (LLM) based voice assistance and smart speaker.

## Hardware

You'll need a speaker and a microphone. The better the microphone, the better chance you'll have of the STT system understanding you. Here's what I used:

 * Microphone: [Upgraded USB Conference Microphone](https://www.amazon.com/gp/product/B08GPPQH9B/)
 * Speaker: [USB Mini Computer Speaker](https://www.amazon.com/gp/product/B075M7FHM1)

## Getting Started

### Install OS

Install [Raspberry Pi OS](https://www.raspberrypi.com/software/). This was tested on Raspberry Pi OS release 2023-05-03. In theory, this should work with the headless version (Raspberry Pi OS Lite), but I have not tested it.

Plug in the microphone and speaker.

### Install Dependencies

Make sure *pip* is up to date:

```sh
python -m pip install –upgrade pip
```

Install Rust, as we need a Rust compiler for one of the packages. It will take ~30 min on a Pi 4.

```sh
curl https://sh.rustup.rs -sSf | sh
```

**Optional**: install Python packages and run everything in a virtual environment:

```sh
python -m venv venv
source venv/bin/activate
```

Install other dependencies. I pinned the versions to ensure everything would work together:

```sh
python -m pip install sounddevice==0.4.6 TTS==0.22.0 vosk==0.3.45 python-dotenv==1.0.1 openai==1.23.2 resampy==0.4.3
```

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

Sign up for an [OpenAI account](https://openai.com/) and follow [these directions](https://help.socialintents.com/article/188-how-to-find-your-openai-api-key-for-chatgpt) to get your API key. **NOTE**: you will likely need to pay for every API call, but it will be cheap (a few cents).

In *hopper-gpt.py*, paste your key in the settings:

```python
GPT_API_KEY = "PASTE KEY HERE"
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

In the above printout, my USB microphone is `1 UM02` and my USB speaker is `2 UACDemoV1.0`. In *hopper-gpt.py*, change the input and output index numbers to match your desired audio devices:

```python
AUDIO_INPUT_INDEX = 1
AUDIO_OUTPUT_INDEX = 2
```

If, for some reason, your speaker cannot handle 48 kHz output, you will need to find out the sample rate of your speaker and change the output sample rate value:

```python
AUDIO_OUTPUT_SAMPLE_RATE = 48000
```

### Run!

Simply run the script, and it should start listening for the wake phrase ("hey, Hopper!" by default) and responding to queries. Note that this is an LLM-based chatbot, so it can't perform active internet searches (e.g. "What's the weather like right now?").

```sh
python hopper-chat.py
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
