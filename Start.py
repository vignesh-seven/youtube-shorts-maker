from PIL import Image, ImageOps, ImageFont, ImageDraw
import ffmpeg, io, os, textwrap, shutil, datetime
import pandas as pd

os.system('cls')

SIZE = (1080, 1920)
FONT_COLOR = (255, 255, 255)
FONT = "cambria.ttf"
FONT_SIZE = 100
STROKE_WIDTH = 20
STOKE_COLOR = (0, 0, 0)

background_interval = 5

VIDEO_DURATION = 12

TEXT_SEGMENTS = [
    {
        "start": 0,
        "end": 8
    },
    {
        "start": 9,
        "end": 12
    }
]

OUTPUT_FILE_NAME = "quote_video"

# get a font
FONT = ImageFont.truetype(f"fonts/{FONT}", FONT_SIZE)

# prep work
if os.path.exists("temp/"):
    shutil.rmtree("temp/")
# os.mkdir("out/")
os.mkdir("temp/")

# Load Excel file
data = pd.read_excel('quotes.xlsx')

# get the sources
video_sources_list = os.listdir("videos//")
audio_sources_list = os.listdir("audio//")

background_interval = (
    int(len(data) / len(video_sources_list))
)

# print(background_interval)

def drawText(input_text, output_file):

    # wrap the text
    wrapper = textwrap.TextWrapper(width=15, break_long_words=False)
    input_text = wrapper.fill(input_text)

    # Draw text on image
    txt = Image.new("RGBA", SIZE, (0,0,0,0))
    # get a drawing context
    d = ImageDraw.Draw(txt)
    # draw multiline text
    (
        d.multiline_text (
            ((SIZE[0]/2), (SIZE[1]/2)),
            input_text, font=FONT,
            fill=FONT_COLOR,
            anchor="ms",
            align="center",
            stroke_width=STROKE_WIDTH,
            stroke_fill=STOKE_COLOR
        )
    )
    txt.save(output_file)
    # out = txt
    # # out = Image.alpha_composite(background, txt)
    # return out

def cut_video(input_file, output_file, width, height, start_second, end_second):
    video_start_time = 2
    probe = ffmpeg.probe(input_file)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    s_width = int(video_info['width'])
    s_height = int(video_info['height'])
    center_x = s_width / 2
    center_y = s_height / 2

    crop_x = int(center_x - s_width / 2)
    crop_y = int(center_y - s_height / 2)

    print(f"Duration: {end_second - start_second}")

    out = (
        ffmpeg
        .input(input_file)
        .trim(start=start_second,end=end_second)
        .setpts('PTS-STARTPTS')
        .filter('crop', 'ih*9/16', 'ih') # crop to 9:16 aspect ratio
        .filter("scale", f"{width}", f"{height}")
    )
    (
        out
        
        # .filter('pad', f"{width}", f"{height}", f'((max(0\,(1080-iw)))/2)', f'((max(0\,(1920-ih)))/2)')
        # .filter_complex(f"pad={pad_width}:{pad_height}:(ow-iw)/2:(oh-ih)/2")
        # .filter("pad", pad_width, pad_height, "(ow-iw)/2", "(oh-ih)/2")
        .filter("pad", f"{width}", f"{height}", "(ow-iw)/2", "(oh-ih)/2")
        .filter('fps', fps=30, round='up')
        # .output(output_file, pix_fmt="yuv420p", vcodec="libx265", movflags="faststart", loglevel="quiet")
        # .run()
    ) 
    return out

def cut_audio(input_file, start_time):
    audio_stream = ffmpeg.input(input_file)
    # audio_duration = ffmpeg.probe("audio/audio_src0.mp3")["format"]["duration"]
    # print(audio_duration)
    audio_stream = (
        audio
        # .input("audio/audio_src0.mp3")
        # .trim(start=0,end=VIDEO_DURATION)
        .output(f"{output_folder}/audio_trimmed.mp3", ss=f"{start_time}", t=f"{VIDEO_DURATION}", acodec="copy", movflags="faststart")
    )
    return audio_stream

def get_duration(input_file):
    return ffmpeg.probe(input_file)["format"]["duration"]

def split_audio_into_streams(input_files):
    # for index in range(len(input_files)):
    audio_streams = []
    for (index, audio_file) in enumerate(input_files):
        print(audio_file)
        # continue
        audio_duration = ffmpeg.probe(f"audio/{audio_file}")["format"]["duration"]

        audio_duration = (int(float(audio_duration)))
        count = int(int(audio_duration) / VIDEO_DURATION) 
        for i in range(count):
            audio_stream = ffmpeg.input(f"audio/{audio_file}")
            audio_stream = (
                audio_stream
                # .input("audio/audio_src0.mp3")
                # .trim(start=0,end=VIDEO_DURATION)
                .output(f"{output_folder}/{index}_{i}_{audio_file}_trimmed.mp3", ss=f"{i * VIDEO_DURATION}", t=f"{VIDEO_DURATION}", acodec="copy", movflags="faststart")
            )
            audio_streams.append(audio_stream)

            audio_stream.run(overwrite_output=True)

            if len(audio_streams) == len(data):
                # print(len(audio_streams))
                return audio_streams
    if len(audio_streams) < len(data):
        no_of_videos_lacking_audio = len(data) - len(audio_streams)
        print("Not enough audio!")
        print(f"Need audio for {no_of_videos_lacking_audio} more videos (Duration: {str(datetime.timedelta(seconds = no_of_videos_lacking_audio * VIDEO_DURATION))})")
    return audio_streams



def add_overlay(input_stream, overlay_image_path,  overlay_start_time, overlay_end_time):
  overlay_image = ffmpeg.input(overlay_image_path, loop=1, framerate=30).trim(start=0, end=1)

  overlay_filter = f'between(t,{overlay_start_time},{overlay_end_time})'

  return(
    input_stream
    .overlay(overlay_image, x=0, y=0, enable=overlay_filter)
    # .output(output_file, framerate=30)
    # .run()
  )


# for index, row in data.head(len(data)).iterrows():
for index, row in data.head(1).iterrows():
    TEXT_1 = row['first_part']
    TEXT_2 = row['second_part']

    temp_folder = "temp/"
    output_temp = f"temp/{TEXT_1}"
    output_folder = f"out/"

    os.mkdir(output_temp)

    # cut_audio(input_file, start_time)
    split_audio_into_streams(audio_sources_list)

    continue

    # save text into images
    text_1_image = drawText(TEXT_1, f"{output_temp}/part_1.png")
    text_2_image = drawText(TEXT_2, f"{output_temp}/part_2.png")

    # load audio
    # audio_path = audio_sources_list.pop()


    # get the background video
    if (index % background_interval) == 0:
        if len(video_sources_list) == 1:
            continue
        background_video = video_sources_list.pop(0)

    print(f"Video No.: {index+1}")
    print(background_video, TEXT_1)

    # cut the background video 
    print(f"Cutting {background_video}...")
    video_stream = cut_video(f"videos/{background_video}", f"{output_temp}/backgound_video_trimmed.mp4", SIZE[0], SIZE[1], 0, VIDEO_DURATION)

    # add overlay images
    print(f"Adding overlays...")
    video_stream = add_overlay(video_stream, f"{output_temp}/part_1.png", TEXT_SEGMENTS[0]["start"], TEXT_SEGMENTS[0]["end"])
    video_stream = add_overlay(video_stream, f"{output_temp}/part_2.png", TEXT_SEGMENTS[1]["start"], TEXT_SEGMENTS[1]["end"])
    # video_stream = add_overlay(video_stream, f"{output_temp}/part_1.png", 0, 5)
    # video_stream = add_overlay(video_stream, f"{output_temp}/part_2.png", 6, 10)

    
    # add audio

    # render the video
    print(f"Rendering Video No.: {index+1}...")
    video_stream.output(f"{output_folder}/{index+1}_{OUTPUT_FILE_NAME}_{index}.mp4", framerate=30, loglevel="quiet").run(overwrite_output=True)
    print(f"Successfully rendered {OUTPUT_FILE_NAME}_{index+1}.mp4!")

