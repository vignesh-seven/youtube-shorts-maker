from PIL import Image, ImageOps, ImageFont, ImageDraw
import ffmpeg, io, os

import pandas as pd

# Load Excel file
data = pd.read_excel('quotes.xlsx')

SIZE = (1080, 1920)
FONT_COLOR = (255, 255, 255)
FONT = "cambria.ttf"
FONT_SIZE = 120

STROKE_WIDTH = 20
STOKE_COLOR = (0, 0, 0)

# get a font
FONT = ImageFont.truetype(f"fonts/{FONT}", FONT_SIZE)

background_src = Image.open(r"images/1.jpg")

# Crop and resize the image 
background = ImageOps.fit(background_src, SIZE, bleed=0.0, centering=(0.5, 0.5))
background = background.convert("RGBA")

# os.mkdir("out/")
   

def drawText(input_text):
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
    out = Image.alpha_composite(background, txt)
    return out



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
for index, row in data.head(10).iterrows():
    # Access data in the row
    TEXT_1 = row['first_part']
    TEXT_2 = row['second_part']

    temp_folder = "temp/"
    output_temp = f"temp/{TEXT_1}"
    output_folder = f"out/"


    # os.mkdir(output_folder)
    os.mkdir(output_temp)

    image_1 = drawText(TEXT_1)
    image_2 = drawText(TEXT_2)

    image_1.save(f"{output_temp}/part_1.png")
    background.save(f"{output_temp}/blank.png")
    image_2.save(f"{output_temp}/part_2.png")

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