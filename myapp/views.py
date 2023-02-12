from pypexels import PyPexels
from moviepy.editor import *
import openai
import requests
import pyttsx3
import mimetypes
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .forms import UploadFileForm
from django.contrib.auth import authenticate
from django.conf import settings
from django.http import HttpResponse, Http404

openai.organization = "org-dd720anP6vTVkgfUUteeLbSh"
openai.api_key = "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"
api_key_pexels = 'Lo7Eo8OpLj82bv1X5ZNVG3pkg0Gbv8ZZaJshy6FLIUqeD5LeIYlmRPl4'


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Create your views here.


def signup(request):
    if 'username' in request.session:
        return redirect('index')
    else:
        if request.method == 'GET':
            return render(request, 'signup.html', {
                'form': UserCreationForm,
                "display": "none"
            })
        else:
            if request.POST['password'] == request.POST['confirmPassword']:
                try:
                    # Register user
                    user = User.objects.create_user(
                        username=request.POST['username'], password=request.POST['password'])
                    user.save()
                    request.session['username'] = request.POST['username']
                    request.session.set_expiry(0)
                    return redirect('index')
                except:
                    return render(request, 'signup.html', {
                        'form': UserCreationForm,
                        "error": 'Username already exists',
                        "display": "block"
                    })
            return render(request, 'signup.html', {
                'form': UserCreationForm,
                "error": 'Passwords do not match',
                "display": "block"
            })


def login(request):
    if 'username' in request.session:
        return redirect('index')
    else:
        if request.method == 'GET':
            return render(request, 'login.html', {
                'form': AuthenticationForm,
                "display": "none"
            })
        else:
            user = authenticate(
                request, username=request.POST['username'], password=request.POST['password'])
            if user == None:
                return render(request, 'login.html', {
                    'form': AuthenticationForm,
                    "error": 'Username or password is incorrect',
                    "display": "block"
                })
            else:
                request.session['username'] = request.POST['username']
                request.session.set_expiry(0)
                return redirect('index')


def index(request):
    try:
        if 'username' in request.session:
            username = request.session['username']
            if request.method == 'GET':
                return render(request, 'index.html', {
                    'username': username,
                    'display': "none",
                    'ad': 'none'
                })
            else:
                text = ""
                if request.POST['selects'] == '1':
                    # Texto
                    text = request.POST['text']
                else:
                    # File
                    handle_uploaded_file(request, request.FILES['file'])
                    ip = get_client_ip(request)
                    f = open(f't{ip}.txt')
                    text = f.read()
                    f.close()
                print(text)
                prompt = f'Give me two words per paragraph translated to english that describe the following text: {text}'
                openaiRequest = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=prompt,
                    temperature=0,
                    max_tokens=150
                )
                if 'choices' in openaiRequest:
                    openaiRequest = openaiRequest.choices[0].text
                    openaiRequest = openaiRequest.replace('\n', '')
                    openaiRequest = openaiRequest.replace('\r', '')
                    words = []
                    for x in range(0, openaiRequest.count(',')):
                        words.append(openaiRequest[0:openaiRequest.find(',')])
                        openaiRequest = openaiRequest[openaiRequest.find(
                            ',')+2: len(openaiRequest)]
                    words.append(openaiRequest[0:openaiRequest.find('.')])
                    openaiRequest = openaiRequest[openaiRequest.find(
                        '.')+1: len(openaiRequest)]

                    # Begin video process
                    clips = []
                    i = 0
                    for x in words:
                        i += 1
                        print(x)
                        # instantiate PyPexels object
                        py_pexel = PyPexels(api_key=api_key_pexels)
                        search_videos_page = py_pexel.videos_search(
                            query=x, orientation='landscape', per_page=10)
                        # Searching the video
                        for video in search_videos_page.entries:
                            data_url = 'https://www.pexels.com/video/' + \
                                str(video.id) + '/download'
                            r = requests.get(data_url)
                            # Saving the video
                            with open(f'clip{i}.mp4', 'wb') as outfile:
                                outfile.write(r.content)
                                if VideoFileClip(f'clip{i}.mp4').duration > 10:
                                    clips.append(VideoFileClip(
                                        f'clip{i}.mp4').resize((1920, 1080)).subclip(0, 10))
                                else:
                                    clips.append(VideoFileClip(
                                        f'clip{i}.mp4').resize((1920, 1080)))
                            break
                    engine = pyttsx3.init()
                    voices = engine.getProperty('voices')
                    engine.setProperty('voice', voices[1].id)
                    engine.save_to_file(text, 'voice.mp3')
                    engine.runAndWait()
                    final_clip = concatenate_videoclips(clips)
                    final_clip.write_videofile('pre-result.mp4')
                    videoclip = VideoFileClip('pre-result.mp4')
                    audioclip = AudioFileClip('voice.mp3')
                    new_audioclip = CompositeAudioClip([audioclip])
                    videoclip.audio = new_audioclip
                    videoclip.write_videofile("output.mp4")
                    return render(request, 'index.html', {
                        'username': username,
                        'display': "none",
                        'ad': 'block'
                    })
                return render(request, 'index.html', {
                    'username': username,
                    'display': "block",
                    'error': "we couldn't connect to the AI",
                    'ad': 'none'
                })
        else:
            return redirect('login')
    except:
        return render(request, 'index.html', {
            'username': username,
            'display': "block",
            'error': "we couldn't connect to the AI",
            'ad': 'none'
        })


def download(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filename = 'output.mp4'
    filepath = BASE_DIR + '\\' + filename
    path = open(filepath, 'rb')
    response = HttpResponse(path, content_type='video/mp4')
    response['Content-Disposition'] = f"attachment; filename={filename}"
    return response


def logout(request):
    try:
        del request.session['username']
        return render(request, 'logout.html')
    except:
        return redirect('login')


def handle_uploaded_file(request, f):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    with open(f't{ip}.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
