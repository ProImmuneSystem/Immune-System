from pathlib import Path
from PIL import Image, ImageDraw
folder=Path('compare')
for width in (1440,390):
 for number in range(4):
  a=folder/f'{number}-original-{width}.png';b=folder/f'{number}-mirror-{width}.png'
  if not a.exists() or not b.exists(): continue
  first=Image.open(a).convert('RGB');second=Image.open(b).convert('RGB')
  combined=Image.new('RGB',(first.width+second.width,max(first.height,second.height)+32),'white')
  combined.paste(first,(0,32));combined.paste(second,(first.width,32))
  d=ImageDraw.Draw(combined);d.text((8,8),'WORDPRESS',fill='black');d.text((first.width+8,8),'GITHUB PAGES',fill='black')
  combined.save(folder/f'{number}-side-by-side-{width}.png',optimize=True)
