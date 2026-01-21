import os
from datetime import datetime
from docx import Document
from src.config.styles import ReportStyles

class WeeklyGPSReportBuilder:
    def __init__(self, matchday_number):
        self.matchday_number = matchday_number
        self.doc = Document()
        self._configure_styles()
        
        # Configuration
        self.TOP_N = 5
        self.MIN_DURATION_MIN = 60
        self.MIN_DISTANCE_KM = 1.0

    def _configure_styles(self):
        """Configure document styles using centralized configuration."""
        ReportStyles.apply_normal_style(self.doc)
        ReportStyles.apply_heading_styles(self.doc)

    def build_report(self, df_all, uploading_teams, missing_teams):
        """Build the complete report."""
        self._add_title()
        self._add_top_performers(df_all)
        self._add_matchday_averages(df_all, uploading_teams)
        self._add_missing_teams(missing_teams)

    def _add_title(self):
        title = self.doc.add_heading(
            f"GPS PHYSICAL PERFORMANCE (CATAPULT) REPORT FOR UPL 2025/2026 MATCHDAY {self.matchday_number}", 
            0
        )
        title.alignment = 1  # Center

    def _add_top_performers(self, df_all):
        self.doc.add_heading(f"TOP {self.TOP_N} PERFORMERS PER METRIC", level=1)
        
        # Disclaimer
        disclaimer = self.doc.add_paragraph()
        runner = disclaimer.add_run("NOTE: Sprint distances should be viewed with caution as speed zones are still being adjusted for various clubs.")
        runner.bold = True
        runner.font.color.rgb = ReportStyles.COLOR_RED
        
        metrics = {
            'Distance (km)': ('Total Distance', 'km', 2),
            'Sprint Distance (m)': ('Sprint Distance', 'm', 1),
            'Top Speed (km/h)': ('Top Speed', 'km/h', 2),
            'Player Load': ('Player Load', '', 1)
        }
        
        for col, (label, unit, decimals) in metrics.items():
            self.doc.add_heading(label, level=2)
            
            if col not in df_all.columns:
                self.doc.add_paragraph("Metric data not found")
                continue

            top = df_all.nlargest(self.TOP_N, col)
            
            if top.empty:
                self.doc.add_paragraph("No data available")
                continue
            
            # Add Table
            table = self.doc.add_table(rows=1, cols=5)
            table.style = 'Table Grid'
            
            # Header Row
            hdr_cells = table.rows[0].cells
            headers = ['S/N', 'Player Name', 'Club', 'Position', f'Value ({unit})' if unit else 'Value']
            for i, text in enumerate(headers):
                hdr_cells[i].text = text
                for paragraph in hdr_cells[i].paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
            
            for i, idx in enumerate(top.index, 1):
                row_cells = table.add_row().cells
                
                # Get parsed data if available
                raw_clean_name = top.loc[idx, 'Clean Name'] if 'Clean Name' in top.columns else top.loc[idx, 'Player Name']
                player_name = str(raw_clean_name).title()
                
                team = top.loc[idx, 'team1']
                position = top.loc[idx, 'Position'] if 'Position' in top.columns else ""
                value = top.loc[idx, col]
                
                row_cells[0].text = str(i)
                row_cells[1].text = player_name
                row_cells[2].text = str(team)
                row_cells[3].text = str(position)
                row_cells[4].text = f"{value:.{decimals}f}"

    def _add_matchday_averages(self, df_all, uploading_teams):
        self.doc.add_page_break()
        self.doc.add_heading("Matchday Averages (Exposure Filtered)", level=1)
        
        # Apply exposure filter
        df_filtered = df_all[
            (df_all['Duration'] >= self.MIN_DURATION_MIN) &
            (df_all['Distance (km)'] >= self.MIN_DISTANCE_KM)
        ].copy()
        
        self.doc.add_paragraph(
            f"Filter: Duration ≥ {self.MIN_DURATION_MIN} min AND Distance ≥ {self.MIN_DISTANCE_KM} km"
        )
        self.doc.add_paragraph(f"Players included: {len(df_filtered)} (of {len(df_all)} total)")
        self.doc.add_paragraph(f"Players excluded: {len(df_all) - len(df_filtered)}")

        self.doc.add_paragraph(f"Report Generated on: {datetime.now():%Y-%m-%d %H:%M}")
        self.doc.add_paragraph(f"Teams Analysed: {len(uploading_teams)}")
        
        self.doc.add_paragraph("")
        
        metrics = {
            'Distance (km)': ('Total Distance', 'km', 2),
            'Sprint Distance (m)': ('Sprint Distance', 'm', 1),
            'Top Speed (km/h)': ('Top Speed', 'km/h', 2),
            'Player Load': ('Player Load', '', 1)
        }

        if df_filtered.empty:
            self.doc.add_paragraph("⚠ No players met exposure criteria")
        else:
            for col, (label, unit, decimals) in metrics.items():
                if col not in df_filtered.columns:
                    continue
                    
                mean_val = df_filtered[col].mean()
                median_val = df_filtered[col].median()
                std_val = df_filtered[col].std()
                count = df_filtered[col].count()
                
                if unit:
                    text = f"{label}: Mean = {mean_val:.{decimals}f} {unit}, Median = {median_val:.{decimals}f} {unit}, SD = {std_val:.{decimals}f}, n = {count}"
                else:
                    text = f"{label}: Mean = {mean_val:.{decimals}f}, Median = {median_val:.{decimals}f}, SD = {std_val:.{decimals}f}, n = {count}"
                
                self.doc.add_paragraph(text, style='List Bullet')

    def _add_missing_teams(self, missing_teams):
        if missing_teams:
            self.doc.add_heading("Teams Not Uploading Data", level=1)
            self.doc.add_paragraph("The following teams did not submit their (Catapult) GPS data:")
            for team in sorted(list(missing_teams)):
                self.doc.add_paragraph(f"{team}", style='List Bullet')

    def save(self, output_path):
        """Save the document."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.doc.save(output_path)
