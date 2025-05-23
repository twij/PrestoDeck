"""Image decoding utilities for MPRIS artwork."""

class ImageHandler:
    """Handles image loading and display for album artwork."""
    
    def __init__(self, display):
        """Initialize with display context.
        
        Args:
            display: The PrestoDeck display object
        """
        self.display = display
        self.app = None
        
        import jpegdec
        self.jpeg = jpegdec.JPEG(display)
        
        self.JPEG_SCALE_FULL = jpegdec.JPEG_SCALE_FULL
        self.jpegdec = jpegdec
    
    def show_image(self, img_data, x=None, y=None):
        """Displays an album cover image on the screen.
        
        Args:
            img_data: Binary image data (bytes or memoryview)
            x: Optional x position, centered if None
            y: Optional y position, centered if None
            
        Returns:
            True if successful, False if failed
        """
        try:
            if img_data is None:
                print("ERROR: img_data is None")
                return False
            
            if not isinstance(img_data, (bytes, memoryview)):
                print(f"ERROR: img_data is not binary data, type={type(img_data)}")
                return False
                    
            if len(img_data) > 4:
                header = [img_data[0], img_data[1]]
                print(f"Image header bytes: {hex(header[0])}, {hex(header[1])}")
                if not (header[0] == 0xFF and header[1] == 0xD8):
                    print("WARNING: Image data doesn't have JPEG header")
            
            if not isinstance(img_data, memoryview):
                img_data = memoryview(img_data)
                
            print(f"Opening image data of type {type(img_data)} and length {len(img_data)}")
            self.jpeg.open_RAM(img_data)
            
            img_width, img_height = self.jpeg.get_width(), self.jpeg.get_height()
            print(f"Image dimensions: {img_width}x{img_height}")
            
            if x is None or y is None:
                if hasattr(self.app, 'width') and hasattr(self.app, 'height'):
                    display_width = self.app.width
                    display_height = self.app.height
                else:
                    display_width = 480
                    display_height = 480
                
                img_x = x if x is not None else (display_width - img_width) // 2
                img_y = y if y is not None else (display_height - img_height) // 2
            else:
                img_x, img_y = x, y
            
            self.jpeg.decode(img_x, img_y, self.JPEG_SCALE_FULL, dither=True)
            print(f"JPEG image displayed successfully: {img_width}x{img_height}")
            return True
                
        except Exception as e:
            print(f"Failed to load image: {e}")
            import sys
            sys.print_exception(e)
            return False