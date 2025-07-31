import conf
import os
from PIL import Image, ImageDraw, ImageFont


class Photo():
    def __init__(self, path):
        self.path = path
        self.min_path = ''
        self.pil_image = Image.open(self.path).convert('RGBA')
        self.witdh, self.height = self.pil_image.size
        self.size = self.pil_image.size

        min_file = self.path.stem + '.min' + self.path.suffix
        self.min_path = self.path.with_name(min_file)
    
    @property
    def is_min(self):
        return self.path.stem.endswith('.min') or self.path.match('*.min.*')
    
    @property
    def has_min(self):
        return self.min_path.exists()
    
    def format(self):
        print(f"Processing image: {self.path}")
        
        if self.is_min:
            print(f"  Skipping .min image: {self.path}")
            return None
        
        # Only watermark and generate .min images if a .min image doesn't already exist
        if self.has_min:
            print(f"  Image already has .min version, skipping processing: {self.path}")
            print(f"  Existing .min file: {self.min_path}")
        else:
            print(f"  No .min file found, processing image: {self.path}")
            if conf.SIGN_ORIGINAL:
                print(f"  Watermarking original image: {self.path}")
                signed_image = self.mark_image(self.pil_image, conf.fontsize)
                self.save_image(signed_image, self.path)
            
            # resize
            ratio = float(conf.MIN_WIDTH) / self.size[0]
            new_image_size = tuple([int(x*ratio) for x in self.size])

            if conf.SIGN_THUMBNAIL:
                print(f"  Creating watermarked thumbnail: {self.min_path}")
                if not conf.SIGN_ORIGINAL:
                    signed_image = self.mark_image(self.pil_image, conf.fontsize)
                # ANTIALIAS is deprecated in newer Pillow versions, using Resampling.LANCZOS instead
                signed_image.thumbnail(new_image_size, Image.Resampling.LANCZOS)
                self.save_image(signed_image, self.min_path)
            else:
                print(f"  Creating thumbnail without watermark: {self.min_path}")
                min_image = self.pil_image.copy()
                # ANTIALIAS is deprecated in newer Pillow versions, using Resampling.LANCZOS instead
                min_image.thumbnail(new_image_size, Image.Resampling.LANCZOS)
                self.save_image(min_image, self.min_path)

        relative_path = str(self.path.relative_to(conf.DIR_PATH))

        # return basic info
        return {
          "type": 'photo',
          'width': self.size[0],
          'height': self.size[1],
          'path': './' + relative_path,
          'min_path': './' + str(self.min_path.relative_to(conf.DIR_PATH))
        }
    
    def save_image(self, img, path):
        if conf.DEBUG:
            img.show()
        else:
            # rgb_img = img.convert('RGB')
            img.save(path, 'PNG')
    
    def mark_image(self, img, fontsize):
        width, height = img.size
        transparent_image = Image.new('RGBA', img.size, (255, 255, 255, 0))
        font = ImageFont.truetype('./assets/font/' + conf.fontfamily, conf.fontsize)
        draw = ImageDraw.Draw(transparent_image)

        # getsize is deprecated in newer Pillow versions, using getbbox instead
        bbox = font.getbbox(conf.copyright)
        t_w = bbox[2] - bbox[0]  # right - left = width
        t_h = bbox[3] - bbox[1]  # bottom - top = height

        x = (width - t_w) / 2
        y = height - 2 * t_h
        draw.text((x, y), conf.copyright, font=font, fill=(255, 255, 255, 125))
        transparent_image = transparent_image.rotate(conf.watermark_rotate)
        signed_image = Image.alpha_composite(img, transparent_image)
        return signed_image
