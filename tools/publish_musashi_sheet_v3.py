from pathlib import Path
from PIL import Image
import shutil
root=Path(__file__).resolve().parents[1]
source=root/'captures/qa/musashi_character_sheet_v3'
dest=root/'assets/characters/musashi/sheet_v3'
dest.mkdir(parents=True,exist_ok=True)
for name in ('three_quarter','front','left_side','back'):
    with Image.open(source/(name+'.png')) as im:
        im.convert('RGB').save(dest/(name+'.jpg'),quality=83,optimize=True)
shutil.copy2(source/'musashi_sheet_exterior_v3.blend',dest/'musashi_sheet_exterior_v3.blend')
print('PUBLISHED',dest)
