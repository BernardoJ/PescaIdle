"""Offline production step: downsample master, palette-limit, extract foreground.

The shipped game only needs PySide6 and the final PNGs; Pillow is a build tool.
"""
from pathlib import Path
from PIL import Image

root=Path(__file__).resolve().parents[1]
source=Image.open(root/'assets'/'source'/'enseada-original.png').convert('RGB')
scene=source.resize((256,144),Image.Resampling.BOX)
scene=scene.quantize(colors=80,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGBA')
scene.save(root/'assets'/'enseada.png')
# Bank silhouettes in front of the water. Same pixels and palette as the plate.
foreground=Image.new('RGBA',scene.size)
for y in range(108,144):
    for x in range(256):
        left=24+(y-108)//2
        right=240-(y-108)//2
        if x<left or x>right:
            foreground.putpixel((x,y),scene.getpixel((x,y)))
foreground.save(root/'assets'/'margem.png')

for name,size,colors in (('barco',(84,28),32),('pescador',(32,44),40)):
    master=Image.open(root/'assets'/'source'/(name+'-original.png')).convert('RGBA')
    alpha=master.getchannel('A').point(lambda a:255 if a>=100 else 0)
    bounds=alpha.getbbox()
    master=master.crop(bounds).resize(size,Image.Resampling.BOX)
    alpha=master.getchannel('A').point(lambda a:255 if a>=100 else 0)
    rgb=master.convert('RGB').quantize(colors=colors,method=Image.Quantize.MEDIANCUT,
                                     dither=Image.Dither.NONE).convert('RGBA')
    rgb.putalpha(alpha)
    rgb.save(root/'assets'/(name+'.png'))
print('Master prepared as 256 x 144, 80 colors, no dithering; matching foreground.')
