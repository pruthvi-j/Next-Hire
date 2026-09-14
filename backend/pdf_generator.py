"""
NEXT HIRE - PDF Report Generation Engine (Phase 9)
Master of Computer Applications (MCA) Academic Project

Generates professional, publication-quality technical interview evaluation reports
using ReportLab with clean styling, candidate benchmarks, multi-dimensional scores,
diagnostic feedback, and complete question-and-answer transcripts.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page count
    along with academic footer on every page.
    """
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header rule
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 750, 558, 750)
        self.drawString(54, 755, "NextHire &bull; Intelligent Mock Technical Interview Chamber")

        # Footer
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Master of Computer Applications (MCA) Capstone Project &bull; Confidential Assessment Report")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def generate_interview_pdf_report(candidate_name, interview_data):
    """
    Builds a complete, beautifully formatted PDF report for an interview session.
    
    Args:
        candidate_name (str): Full name of the candidate
        interview_data (dict): Result payload returned by answer_analyzer.generate_interview_result
        
    Returns:
        io.BytesIO: In-memory binary buffer containing the PDF bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )

    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=15
    )

    style_section = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=14,
        spaceAfter=6
    )

    style_body = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155')
    )

    style_body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=style_body,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0f172a')
    )

    style_bullet = ParagraphStyle(
        'DocBullet',
        parent=style_body,
        leftIndent=12,
        spaceAfter=3
    )

    style_q_text = ParagraphStyle(
        'DocQText',
        parent=style_body,
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )

    style_ans_text = ParagraphStyle(
        'DocAnsText',
        parent=style_body,
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569')
    )

    story = []

    # 1. Header Banner
    session_id = interview_data.get('interview_id', 1)
    session_code = f"#NH-2026-{session_id:03d}"
    role_name = interview_data.get('role_name', 'Software Engineer')
    interview_date = datetime.now().strftime("%d %B %Y")

    story.append(Paragraph("NextHire", style_title))
    story.append(Paragraph("Intelligent Mock Interview Report", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=12))

    # 2. Candidate & Session Meta Table
    overall_score = float(interview_data.get('overall_score', 0))
    overall_score_str = f"{overall_score:.1f}%"
    
    if overall_score >= 85:
        status_label = "Industry Ready (Optimal)"
    elif overall_score >= 70:
        status_label = "Proficient &amp; Qualified"
    elif overall_score >= 50:
        status_label = "Developing Foundation"
    else:
        status_label = "Foundational Review Required"

    meta_table_data = [
        [
            Paragraph(f"<b>Candidate Name:</b> {candidate_name}", style_body),
            Paragraph(f"<b>Target Role:</b> {role_name}", style_body)
        ],
        [
            Paragraph(f"<b>Assessment Date:</b> {interview_date}", style_body),
            Paragraph(f"<b>Session Code:</b> {session_code}", style_body)
        ],
        [
            Paragraph(f"<b>Difficulty Tier:</b> {interview_data.get('difficulty', 'Medium')}", style_body),
            Paragraph(f"<b>Questions Evaluated:</b> {interview_data.get('total_questions', 5)}", style_body)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#edf2f7")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # 3. Overall Readiness Score Banner
    score_banner_data = [
        [
            Paragraph("<font size=11 color='#64748b'>OVERALL READINESS RATING</font><br/><br/>"
                      f"<font size=28 color='#10b981'><b>{overall_score_str}</b></font><br/>"
                      f"<font size=9 color='#0f172a'><b>Status: {status_label}</b></font>", ParagraphStyle('ScoreCenter', alignment=1)),
            Paragraph("<font size=9 color='#334155'>"
                      "<b>Weighted Academic Scoring Model:</b><br/>"
                      "&bull; <b>Technical Knowledge:</b> 40% Weight<br/>"
                      "&bull; <b>Answer Quality:</b> 25% Weight<br/>"
                      "&bull; <b>Communication:</b> 20% Weight<br/>"
                      "&bull; <b>Confidence Estimate:</b> 15% Weight<br/>"
                      "<font size=7.5 color='#64748b'><i>*Confidence estimate based on observable response indicators.</i></font>"
                      "</font>", style_body)
        ]
    ]
    score_banner_table = Table(score_banner_data, colWidths=[200, 304])
    score_banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#86efac")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(score_banner_table)
    story.append(Spacer(1, 14))

    # 4. Multi-Dimensional Competency Breakdown Table
    story.append(Paragraph("Core Competency Dimensions", style_section))

    scores = interview_data.get('scores', {})
    tech = scores.get('technical', {})
    qual = scores.get('quality', {})
    comm = scores.get('communication', {})
    conf = scores.get('confidence', {})

    dim_table_data = [
        [
            Paragraph("<b>Competency Dimension</b>", style_body_bold),
            Paragraph("<b>Score (1-5)</b>", style_body_bold),
            Paragraph("<b>Normalized %</b>", style_body_bold),
            Paragraph("<b>Academic Hiring Weight</b>", style_body_bold)
        ],
        [
            Paragraph("Technical Knowledge &amp; Domain Accuracy", style_body),
            Paragraph(f"{tech.get('score_5', 0):.1f} / 5.0", style_body),
            Paragraph(f"{tech.get('percentage', 0):.0f}%", style_body),
            Paragraph("40%", style_body)
        ],
        [
            Paragraph("Answer Quality &amp; Completeness", style_body),
            Paragraph(f"{qual.get('score_5', 0):.1f} / 5.0", style_body),
            Paragraph(f"{qual.get('percentage', 0):.0f}%", style_body),
            Paragraph("25%", style_body)
        ],
        [
            Paragraph("Communication Clarity &amp; Articulation", style_body),
            Paragraph(f"{comm.get('score_5', 0):.1f} / 5.0", style_body),
            Paragraph(f"{comm.get('percentage', 0):.0f}%", style_body),
            Paragraph("20%", style_body)
        ],
        [
            Paragraph("Confidence Estimate (Observable Indicators)*", style_body),
            Paragraph(f"{conf.get('score_5', 0):.1f} / 5.0", style_body),
            Paragraph(f"{conf.get('percentage', 0):.0f}%", style_body),
            Paragraph("15%", style_body)
        ]
    ]

    dim_table = Table(dim_table_data, colWidths=[224, 90, 100, 90])
    dim_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 5.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(dim_table)
    story.append(Spacer(1, 14))

    # 5. Personalized Feedback (Strengths, Weaknesses, Recommendations)
    story.append(Paragraph("Personalized Diagnostic Evaluation", style_section))

    strengths = interview_data.get('strengths', [])
    weaknesses = interview_data.get('weaknesses', [])
    recommendations = interview_data.get('recommendations', [])

    fb_data = [
        [
            Paragraph("<font color='#059669'><b>VALIDATED STRENGTHS</b></font>", style_body_bold),
            Paragraph("<font color='#d97706'><b>AREAS TO IMPROVE</b></font>", style_body_bold),
            Paragraph("<font color='#4f46e5'><b>RECOMMENDATIONS</b></font>", style_body_bold)
        ]
    ]

    # Convert items to formatted paragraphs
    s_col = [Paragraph(f"&bull; {item.replace('✓', '').replace('•', '').strip()}", style_bullet) for item in (strengths or ['Demonstrated solid foundational technical knowledge.'])]
    w_col = [Paragraph(f"&bull; {item.replace('•', '').strip()}", style_bullet) for item in (weaknesses or ['Give more complete answers with syntax examples.'])]
    r_col = [Paragraph(f"&bull; {item.replace('→', '').replace('•', '').strip()}", style_bullet) for item in (recommendations or ['Practice targeted role scenario problems.'])]

    # Max length padding
    max_len = max(len(s_col), len(w_col), len(r_col))
    s_col.extend([Paragraph("", style_bullet)] * (max_len - len(s_col)))
    w_col.extend([Paragraph("", style_bullet)] * (max_len - len(w_col)))
    r_col.extend([Paragraph("", style_bullet)] * (max_len - len(r_col)))

    for i in range(max_len):
        fb_data.append([s_col[i], w_col[i], r_col[i]])

    fb_table = Table(fb_data, colWidths=[168, 168, 168])
    fb_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#ecfdf5")),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#fffbeb")),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#eef2ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(fb_table)
    story.append(Spacer(1, 16))

    # 6. Question and Answer Summary
    story.append(Paragraph("Question &amp; Answer Technical Audit Summary", style_section))

    questions_details = interview_data.get('questions_details', [])
    if not questions_details:
        story.append(Paragraph("No detailed question transcripts were recorded.", style_body))
    else:
        for q in questions_details:
            q_order = q.get('order', 1)
            q_code = q.get('question_code', 'Q')
            q_lang = q.get('language', 'General')
            q_topic = q.get('topic', 'General')
            q_diff = q.get('difficulty', 'Medium')
            q_text = q.get('question_text', '')
            a_text = q.get('answer_text', '(No answer recorded)')
            feedback = q.get('feedback', '')
            s = q.get('scores', {})

            q_card_data = [
                [
                    Paragraph(f"<b>Question {q_order} &bull; [{q_code}] {q_lang} ({q_topic}, {q_diff})</b>", style_q_text),
                    Paragraph(f"<font color='#6366f1'><b>Scores:</b> Tech {s.get('technical', 1)}/5 | Comm {s.get('communication', 1)}/5 | Qual {s.get('quality', 1)}/5 | Conf {s.get('confidence', 1)}/5</font>", ParagraphStyle('ScoreRight', alignment=2, fontName='Helvetica-Bold', fontSize=8))
                ],
                [
                    Paragraph(f"<b>Prompt:</b> {q_text}", style_body),
                    ""
                ],
                [
                    Paragraph(f"<b>Candidate Answer:</b> \"{a_text}\"", style_ans_text),
                    ""
                ],
                [
                    Paragraph(f"<b>Evaluator Feedback:</b> {feedback}", style_body),
                    ""
                ]
            ]

            q_table = Table(q_card_data, colWidths=[354, 150])
            q_table.setStyle(TableStyle([
                ('SPAN', (0, 1), (1, 1)),
                ('SPAN', (0, 2), (1, 2)),
                ('SPAN', (0, 3), (1, 3)),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#e2e8f0")),
                ('PADDING', (0, 0), (-1, -1), 5.5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            story.append(KeepTogether([q_table, Spacer(1, 8)]))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
