# osu-mp3-converter
html application that converts youtube links to (most of the time) rankable 192kbps mp3 files. this is indeed as basic as it gets (i made this in like a day lol)

## running on your own server
just run the following commands and by default it runs on localhost:4444
```
git clone https://github.com/infadel2/osu-mp3-converter
pip install -r requirements.txt
python main.py
```

if you want to specify a specific port to run this converter on, pass -p or --port with your port
```
python main.py -p 3333
```
