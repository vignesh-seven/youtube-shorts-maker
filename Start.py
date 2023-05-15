from PIL import Image, ImageOps, ImageFont, ImageDraw
import ffmpeg, io, os, textwrap, shutil
import pandas as pd

DONT_MAKE_VIDEO = True
DEBUG_MODE = True

SIZE = (1080, 1920)
FONT_COLOR = (255, 255, 255)
FONT = "cambria.ttf"
FONT_SIZE = 100
STROKE_WIDTH = 20
STOKE_COLOR = (0, 0, 0)

BACKGROUND_INTERVAL = 5

# get a font
FONT = ImageFont.truetype(f"fonts/{FONT}", FONT_SIZE)

# prep work
if os.path.exists("temp/"):
    shutil.rmtree("temp/")
# os.mkdir("out/")
os.mkdir("temp/")

# Load Excel file
data = pd.read_excel('quotes.xlsx')

sources_list = os.listdir("videos//")

def drawText(input_text):

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
    out = txt
    # out = Image.alpha_composite(background, txt)
    return out

def cutVideo(input_file, output_file, width, height, duration):
    video_start_time = 2
    probe = ffmpeg.probe(input_file)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    s_width = int(video_info['width'])
    s_height = int(video_info['height'])
    center_x = s_width / 2
    center_y = s_height / 2

    crop_x = int(center_x - s_width / 2)
    crop_y = int(center_y - s_height / 2)

    # pad_width = max(width, s_width)
    # pad_height = max(height, s_height)

    out = (
        ffmpeg
        .input(input_file)
        .trim(start=2,end=(video_start_time+duration))
        .filter('crop', 'ih*9/16', 'ih') # crop to 9:16 aspect ratio
        .filter("scale", f"{width}", f"{height}")
    )
    # if s_width <= width:
    #     out.filter('scale', f"{width}", '-1')
    # if s_height <= height:
    #     out.filter('scale', "-1", f"{height}")
    (
        out
        
        # .filter('pad', f"{width}", f"{height}", f'((max(0\,(1080-iw)))/2)', f'((max(0\,(1920-ih)))/2)')
        # .filter_complex(f"pad={pad_width}:{pad_height}:(ow-iw)/2:(oh-ih)/2")
        # .filter("pad", pad_width, pad_height, "(ow-iw)/2", "(oh-ih)/2")
        .filter("pad", f"{width}", f"{height}", "(ow-iw)/2", "(oh-ih)/2")
        .filter('fps', fps=30, round='up')
        .output(output_file, pix_fmt="yuv420p", vcodec="libx265", movflags="faststart")
        .run()
    ) 

# turning them into video

def convertToVideo(input, output, duration):
    return(
        ffmpeg
        .input(input, framerate=30)
        .filter("loop", loop=-1, size=1)
        .output(output, pix_fmt="yuv420p", vcodec="libx265", movflags="faststart", t=duration)
        .overwrite_output()
        .run()
)



# Iterate over rows
for index, row in data.head(20).iterrows():
    # Access data in the row
    TEXT_1 = row['first_part']
    TEXT_2 = row['second_part']

    temp_folder = "temp/"
    output_temp = f"temp/{TEXT_1}"
    output_folder = f"out/"


    # os.mkdir(output_folder)
    os.mkdir(output_temp)

    if (index % BACKGROUND_INTERVAL) == 0:
        background = sources_list.pop(0)

    # for i in range(len(sources_list)):
    print(index, background)
    # print(index % BACKGROUND_INTERVAL)

    continue

    cutVideo("videos/source.mp4", "out/dest.mp4", SIZE[0], SIZE[1], 8)

    # image_1_text = drawText(TEXT_1)
    # image_2_text = drawText(TEXT_2)


    if DEBUG_MODE: 
        image_1_text.save("out/part_1.png")
        continue
    
    image_1_text.save(f"{output_temp}/part_1.png")
    # background.save(f"{output_temp}/blank.png")
    image_2_text.save(f"{output_temp}/part_2.png")

    if DONT_MAKE_VIDEO: continue

    convertToVideo(f"{output_temp}/part_1.png", f"{output_temp}/video_1.mp4", 8)
    convertToVideo(f"{output_temp}/blank.png", f"{output_temp}/video_blank.mp4", 1)
    convertToVideo(f"{output_temp}/part_2.png", f"{output_temp}/video_2.mp4", 4)

    video1 = ffmpeg.input(f"{output_temp}/video_1.mp4")
    video_blank = ffmpeg.input(f"{output_temp}/video_blank.mp4")
    video2 = ffmpeg.input(f"{output_temp}/video_2.mp4")
    
    # Do something with the data in the row
    print(f"{index}: {TEXT_1}, {TEXT_2}")

    (
        ffmpeg
        .concat(video1, video_blank, video2)
        .output(f'{output_folder}/0_{TEXT_1}.mp4', vcodec='libx264', pix_fmt='yuv420p', movflags='faststart')
        .overwrite_output()
        .run()
    )