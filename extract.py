import sys, os, subprocess;
import pytesseract, ffmpeg;
from PIL import Image, ImageEnhance;


def dl(url):
    #download video
    subprocess.run(["youtube-dl", url, "-o", "/home/yobleck/ASMR_pre/dl/%(id)s.%(ext)s"]); #"-q",  .%(ext)s   "-f", "bestvideo",
    
    #get video title and id
    vid_id = subprocess.run(["youtube-dl", "--skip-download", "--get-id", url], 
                            stdout=subprocess.PIPE).stdout.decode().rstrip("\n");
    out = [vid_id]; #TODO: info list --> dict
    for _, _, files in os.walk("./dl/"): #extracting file extension which isn't determined at dl time
        ext = [f for f in files if vid_id in f][0][-4:];
        out.append("/home/yobleck/ASMR_pre/dl/{0}{1}".format(vid_id, ext));
    
    #get frame count
    probe = ffmpeg.probe(out[1]);
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None);
    out.append(round(float(eval(video_stream['avg_frame_rate'])) * 
                     float(probe["format"]["duration"]))); #WARNING: EVAL() IS USED HERE to convert fraction frame rate into single number
    
    return out;


def extract_frame(file_path, frame_num):
    #extract frame with ffmpeg
    #convert to seconds from frame. frame / frame rate = seconds as float
    seconds = str(frame_num / (30000 / 1001)); #TODO: don't hard code frame rate
    subprocess.run(["ffmpeg", "-ss", seconds, "-i", file_path, "-vframes", "1",
                    "-f", "image2", "-y", "/home/yobleck/ASMR_pre/frame/frame.jpg"], stderr=subprocess.DEVNULL);
    return 0;


def scan(input_img):
    ping = False;
    #tesseract read image and check for "preview"
    text = pytesseract.image_to_string( ImageEnhance.Contrast(Image.open(input_img)).enhance(5) ).splitlines();
    print("text found:", text);
    if any(item in ["preview","Preview","PREVIEW"] for item in text):
        ping = True;
    return ping;


def main(vids):
    print("downloading...");
    info = dl(vids[0]); 
    print("video info:", info);
    
    #calculate number of times to loop
    loops = 0;
    delta_t = 15;
    lambda_frames = info[2];
    while(lambda_frames > delta_t):
        lambda_frames = lambda_frames / 2;
        loops+=1;
    print("num loops:", loops);
    
    #binary splice frames from video. 1/2 frame, 1/4 frame etc. until text found.
    #then alternate 1/2 of last step up and down till last step to home in on last timestamp of text
    #TODO: process is faster than expected. maybe make linear checking every 1/2 second for first 3-5 min?
    lambda_frames = info[2];
    frame_time = lambda_frames / 2;
    hit = False; any_hits = False;
    for i in range(loops):
        
        print( "extracting frame #{0} at time: {1}s...".format(int(frame_time), frame_time/(30000/1001)) ); #TODO: don't hard code frame rate
        extract_frame(info[1], int(frame_time));
        
        print("scanning frame for \"preview\" text...");
        hit = scan("/home/yobleck/ASMR_pre/frame/frame.jpg");
        print("text match=", hit, "\n");
        
        lambda_frames = lambda_frames / 2;
        if hit:
            any_hits = True;
            frame_time = frame_time + lambda_frames / 2;
        else:
            frame_time = frame_time - lambda_frames / 2;
    
    if any_hits:
        info.append(frame_time);
        with open("./output.txt", "a") as f:
            f.write(str(info) + "\n");
    
    pass;

if __name__ == "__main__":
    sys.argv.append("https://www.youtube.com/watch?v=-0-kisWjfdU"); #https://www.youtube.com/watch?v=FZlnNpttBA0
    main(sys.argv[1:]);

#TODO: jack up contrast of frame.jpg to make text more visible?

"""
HELPFUL LINKS:
https://kkroening.github.io/ffmpeg-python/
https://github.com/kkroening/ffmpeg-python/blob/master/examples/README.md
https://github.com/kkroening/ffmpeg-python/blob/master/examples/video_info.py#L15
https://github.com/kkroening/ffmpeg-python/blob/master/examples/read_frame_as_jpeg.py#L16

https://pypi.org/project/pytesseract/
https://superuser.com/questions/1448665/ffmpeg-how-to-get-last-frame-from-a-video

https://stackoverflow.com/questions/42045362/change-contrast-of-image-in-pil
https://pythonexamples.org/python-pillow-adjust-image-contrast/
"""
