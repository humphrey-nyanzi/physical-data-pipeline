from docx.shared import Pt, RGBColor

class ReportStyles:
    """Centralized configuration for report styling."""
    
    # Fonts
    FONT_NAME = 'Arial'
    
    # Font Sizes
    FONT_SIZE_TITLE = Pt(18)
    FONT_SIZE_HEADING1 = Pt(14)
    FONT_SIZE_HEADING2 = Pt(12)
    FONT_SIZE_NORMAL = Pt(11)
    
    # Colors
    COLOR_BLACK = RGBColor(0, 0, 0)
    COLOR_RED = RGBColor(192, 0, 0)
    
    # Table Styles
    TABLE_STYLE = 'List Table2 - Accent 5'
    
    @classmethod
    def apply_normal_style(cls, doc):
        """Apply base normal style to document."""
        if 'Normal' in doc.styles:
            style = doc.styles['Normal']
            font = style.font
            font.name = cls.FONT_NAME
            font.size = cls.FONT_SIZE_NORMAL
            
            # Line spacing - more airy
            style.paragraph_format.line_spacing = 1.2
            style.paragraph_format.space_after = Pt(12)
            style.paragraph_format.space_before = Pt(0)

    @classmethod
    def apply_heading_styles(cls, doc):
        # Mapping level to config
        heading_configs = {
            'Heading 1': {'size': cls.FONT_SIZE_HEADING1, 'bold': True},
            'Heading 2': {'size': cls.FONT_SIZE_HEADING2, 'bold': True},
            'Heading 3': {'size': cls.FONT_SIZE_HEADING2, 'bold': False, 'italic': True},
        }

        for level, config in heading_configs.items():
            if level in doc.styles:
                h_style = doc.styles[level]
                h_font = h_style.font
                h_font.name = cls.FONT_NAME
                h_font.size = config['size']
                h_font.color.rgb = cls.COLOR_BLACK
                h_font.bold = config['bold']
                if 'italic' in config:
                    h_font.italic = config['italic']
                
                # Headings spacing - professional rhythm
                h_style.paragraph_format.space_before = Pt(18)
                h_style.paragraph_format.space_after = Pt(8)
                h_style.paragraph_format.line_spacing = 1.15
                
        if 'Title' in doc.styles:
            title_style = doc.styles['Title']
            title_style.font.name = cls.FONT_NAME
            title_style.font.size = cls.FONT_SIZE_TITLE
            title_style.font.color.rgb = cls.COLOR_BLACK
            title_style.font.bold = True
            title_style.paragraph_format.alignment = 1 # CENTER
            title_style.paragraph_format.space_after = Pt(24)
