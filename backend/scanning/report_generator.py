import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend

class ReportGenerator:
    def __init__(self, scan_data, project_data=None):
        self.scan = scan_data
        self.project = project_data or {}
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            textColor=colors.HexColor('#1e40af')  # Blue-800
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#374151')  # Gray-700
        ))
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4b5563')  # Gray-600
        ))
        
        # Severity styles
        self.severity_colors = {
            'critical': colors.HexColor('#dc2626'), # Red-600
            'high': colors.HexColor('#ea580c'),     # Orange-600
            'medium': colors.HexColor('#ca8a04'),   # Yellow-600
            'low': colors.HexColor('#2563eb'),      # Blue-600
            'info': colors.HexColor('#6b7280'),     # Gray-500
        }

    def generate(self):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # --- PRE-PROCESSING ---
        # Prepare lists for sorting/separation
        all_vulns = self.scan.get('vulnerabilities', [])
        
        # Severity Map for sorting
        severity_rank = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4,
            'info': 5
        }
        
        # Sort all vulnerabilities by severity
        all_vulns.sort(key=lambda x: severity_rank.get(x.get('severity', 'info').lower(), 100))
        
        main_findings = []
        false_positives = []
        
        # Check if comprehensive scan to separate false positives
        is_comprehensive = self.scan.get('scan_type', '').lower() == 'comprehensive'
        
        for v in all_vulns:
            if not isinstance(v, dict):
                continue
                
            # Check for False Positive
            is_fp = False
            if is_comprehensive and v.get('other_info'):
                try:
                    import json
                    other_info = v.get('other_info')
                    if isinstance(other_info, str):
                        other_info = json.loads(other_info)
                    if isinstance(other_info, dict) and other_info.get('ml_is_fp'):
                        is_fp = True
                except:
                    pass
            
            if is_fp:
                false_positives.append(v)
            else:
                main_findings.append(v)

        # --- REPORT GENERATION ---

        # 1. Title Page
        story.append(Paragraph(f"Security Scan Report", self.styles['ReportTitle']))
        story.append(Spacer(1, 0.25*inch))
        
        # Metadata Table
        data = [
            ['Target URL', self.scan.get('target_url') or 'N/A'],
            ['Scan Date', str(self.scan.get('created_at', datetime.now().strftime('%Y-%m-%d')))],
            ['Project', self.report_project_name()],
            ['Scan Type', self.scan.get('scan_type', 'Unknown').capitalize()],
        ]
        t = Table(data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*inch))

        # 2. Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.2*inch))
        
        summary_text = "This report details the security vulnerabilities found during the scan of the target application."
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        # ML / FP Stats (If Comprehensive)
        if is_comprehensive:
            total_detected = len(main_findings) + len(false_positives)
            fp_count = len(false_positives)
            reduction = (fp_count / total_detected * 100) if total_detected > 0 else 0
            
            story.append(Paragraph("Machine Learning Analysis", self.styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            ml_data = [
                ['Total Detections', 'Confirmed Findings', 'False Positives', 'Noise Reduction'],
                [str(total_detected), str(len(main_findings)), str(fp_count), f"{reduction:.1f}%"]
            ]
            
            ml_table = Table(ml_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            ml_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e0f2fe')), # Light blue header
                ('TEXTCOLOR', (2,1), (2,1), colors.red), # FP count in red
                ('TEXTCOLOR', (3,1), (3,1), colors.green), # Reduction in green
            ]))
            story.append(ml_table)
            story.append(Spacer(1, 0.3*inch))


        # Recalculate summary from main_findings
        summ_counts = {
            'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0
        }
        for v in main_findings:
            sev = v.get('severity', 'info').lower()
            if sev in summ_counts:
                summ_counts[sev] += 1
        
        # Prepare data for stats table
        severity_data = [
            ['Severity', 'Count'],
            ['Critical', summ_counts['critical']],
            ['High', summ_counts['high']],
            ['Medium', summ_counts['medium']],
            ['Low', summ_counts['low']],
            ['Info', summ_counts['info']],
        ]
        
        
        # Stats Table
        st = Table(severity_data, colWidths=[1.5*inch, 1.0*inch])
        st.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            # Color code cells
                ('TEXTCOLOR', (0,1), (0,1), self.severity_colors['critical']),
                ('TEXTCOLOR', (0,2), (0,2), self.severity_colors['high']),
                ('TEXTCOLOR', (0,3), (0,3), self.severity_colors['medium']),
                ('TEXTCOLOR', (0,4), (0,4), self.severity_colors['low']),
                ('TEXTCOLOR', (0,5), (0,5), self.severity_colors['info']),
        ]))
        st.hAlign = 'CENTER'
        story.append(st)
        story.append(Spacer(1, 0.2*inch))
        
        # --- Pie Chart ---
        drawing = Drawing(400, 250) # Taller for legend below
        pc = Pie()
        pc.x = 125 # Centered: (400 - 150) / 2
        pc.y = 80
        pc.width = 150
        pc.height = 150
        pc.data = [
            summ_counts['critical'],
            summ_counts['high'],
            summ_counts['medium'],
            summ_counts['low'],
            summ_counts['info']
        ]
        # remove labels from chart
        pc.labels = None
        
        # Set colors
        pc.slices.strokeWidth = 0.5
        pc.slices[0].fillColor = self.severity_colors['critical']
        pc.slices[1].fillColor = self.severity_colors['high']
        pc.slices[2].fillColor = self.severity_colors['medium']
        pc.slices[3].fillColor = self.severity_colors['low']
        pc.slices[4].fillColor = self.severity_colors['info']
        
        # Hide labels/pointers effectively
        pc.simpleLabels = 0
        pc.sideLabels = 0 
        
        drawing.add(pc)
        
        # Add Legend
        legend = Legend()
        legend.alignment = 'right'
        legend.x = 30 # Centered below (approx width 340)
        legend.y = 20
        legend.columnMaximum = 1 # One item per column = horizontal row
        legend.deltax = 70 # Spacing between columns
        legend.deltay = 0
        legend.colorNamePairs = [
            (self.severity_colors['critical'], 'Critical'),
            (self.severity_colors['high'], 'High'),
            (self.severity_colors['medium'], 'Medium'),
            (self.severity_colors['low'], 'Low'),
            (self.severity_colors['info'], 'Info')
        ]
        legend.fontName = 'Helvetica'
        legend.fontSize = 11
        legend.strokeWidth = 0.5
        legend.dy = 10
        legend.dx = 10
        legend.dxTextSpace = 5
        
        drawing.add(legend)
        
        # Chart Centering Container
        # Wrap drawing in a Table to center it easily
        drawing_table = Table([[drawing]], colWidths=[6*inch])
        drawing_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(drawing_table)
        
        story.append(Spacer(1, 0.5*inch))

        # 3. Detailed Findings
        story.append(Paragraph("Detailed Findings", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.2*inch))

        def render_vulnerabilities(v_list, start_index=1):
            if not v_list:
                story.append(Paragraph("No vulnerabilities found in this section.", self.styles['Normal']))
                return start_index
                
            for i, v in enumerate(v_list, start_index):
                title = v.get('name', 'Unknown Vulnerability')
                severity = v.get('severity', 'info').lower()
                
                # Title with color
                p_style = ParagraphStyle('VulnTitle', parent=self.styles['Heading3'], textColor=self.severity_colors.get(severity, colors.black))
                story.append(Paragraph(f"{i}. {title} ({severity.upper()})", p_style))
                
                # Description
                if v.get('description'):
                    story.append(Paragraph(f"<b>Description:</b>", self.styles['Normal']))
                    story.append(Paragraph(v['description'], self.styles['InfoText']))
                    story.append(Spacer(1, 0.1*inch))
                
                # Remediation
                if v.get('solution'):
                    story.append(Paragraph(f"<b>Remediation:</b>", self.styles['Normal']))
                    story.append(Paragraph(v['solution'], self.styles['InfoText']))
                
                story.append(Spacer(1, 0.2*inch))
                story.append(HRFlowable(width="80%", thickness=0.5, color=colors.lightgrey, spaceBefore=5, spaceAfter=5))
            return start_index + len(v_list)

        render_vulnerabilities(main_findings)
        
        # 4. False Positives (if any and comprehensive)
        if is_comprehensive and false_positives:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("False Positives (AI Detected)", self.styles['SectionHeader']))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
            story.append(Paragraph("The following findings were flagged as False Positives by the AI verification engine.", self.styles['InfoText']))
            story.append(Spacer(1, 0.2*inch))
            
            render_vulnerabilities(false_positives, start_index=len(main_findings)+1)

        # 5. Disclaimer & Legal Notice
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("Disclaimer & Legal Notice", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.2*inch))
        
        disclaimer_text = """
        <b>Accuracy of Results</b><br/>
        Please note that this security scanning tool is in an initial stage of development. While every effort has been made to ensure accuracy, the results provided in this report may contain errors, false positives, or false negatives. This report should be used as a preliminary assessment and does not guarantee the complete security of the target application. We recommend manual verification of all critical findings.<br/><br/>
        
        <b>Legal Disclaimer</b><br/>
        The authors and maintainers of this tool are not responsible for any damage caused by the use or misuse of this software. This tool is intended for educational and authorized security testing purposes only. The user assumes all legal and regulatory responsibility for the use of this tool against any target systems. By using this report, you acknowledge that you have proper authorization to scan the target URL.
        """
        story.append(Paragraph(disclaimer_text, self.styles['InfoText']))

        doc.build(story)
        buffer.seek(0)
        return buffer

    def report_project_name(self):
        if self.project and 'name' in self.project:
            return self.project['name']
        if 'project' in self.scan and isinstance(self.scan['project'], dict):
             return self.scan['project'].get('name', 'Unknown')
        return "Unknown Project"
