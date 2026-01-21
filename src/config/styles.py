from docx.shared import Pt, RGBColor

class ReportStyles:
    """Centralized configuration for report styling."""
    
    # Fonts
    FONT_NAME = 'Aptos Display'
    
    # Font Sizes
    FONT_SIZE_TITLE = Pt(16)
    FONT_SIZE_HEADING = Pt(14)
    FONT_SIZE_NORMAL = Pt(12)
    
    # Colors
    COLOR_BLACK = RGBColor(0, 0, 0)
    COLOR_RED = RGBColor(255, 0, 0)
    
    # Table Styles
    TABLE_STYLE = 'Table Grid'
    
    @classmethod
    def apply_normal_style(cls, doc):
        """Apply base normal style to document."""
        if 'Normal' in doc.styles:
            style = doc.styles['Normal']
            font = style.font
            font.name = cls.FONT_NAME
            font.size = cls.FONT_SIZE_NORMAL

    @classmethod
    def apply_heading_styles(cls, doc):
        """Apply heading styles to document."""
        for level in ['Heading 1', 'Heading 2']:
            if level in doc.styles:
                h_style = doc.styles[level]
                h_font = h_style.font
                h_font.name = cls.FONT_NAME
                h_font.size = cls.FONT_SIZE_HEADING
                h_font.color.rgb = cls.COLOR_BLACK
                h_font.bold = True
                
        if 'Title' in doc.styles:
            title_style = doc.styles['Title']
            title_style.font.name = cls.FONT_NAME
            title_style.font.size = cls.FONT_SIZE_TITLE
            title_style.font.color.rgb = cls.COLOR_BLACK
            title_style.font.bold = True
