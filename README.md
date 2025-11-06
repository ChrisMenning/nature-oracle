<img width="768" height="1024" alt="image" src="https://github.com/user-attachments/assets/8fe96961-3098-4c05-9ccd-16bbb9b60349" />
<img width="768" height="1024" alt="image" src="https://github.com/user-attachments/assets/2cb7d15a-4c19-4ab6-882b-3bbfb7a60f75" />

# Nature Oracle
A daily briefing for a passive info display.

## Hardware

To create this retrofuturistic passive information display, I used the following pieces:

* Raspberry Pi Zero 2 W
* Waveshare 2 Inch LCD Module
* KY-040 Rotary Encoder

And for the housing, it is mounted inside a gutted Hanimex Vista Viewer II, which is a analog 35 mm slide viewer. The LCD is mounted in place where the film slide would typically go.

## Software

The Nature Oracle program consists of a slideshow, akin to a PowerPoint presentation, rendered in glourious orange ASCII on a black background for vintage goodness. In its current state, there are a handful of topics structured in the codebase as modules. 

### Get Started

1. Sign up for free API Keys with Open Weather and NASA.
2. Add them to secrets.py (see secrets_template.py to see an example)
3. run nature-oracle.py using python
