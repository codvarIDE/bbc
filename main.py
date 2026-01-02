import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDateEdit, QComboBox, QCheckBox, QTextEdit, QFrame, 
    QGroupBox, QGridLayout, QFileDialog, QStackedWidget, QScrollArea,
    QListWidget, QListWidgetItem, QDateTimeEdit, QTimeEdit, QButtonGroup,
    QRadioButton, QSpinBox, QProgressBar, QMessageBox, QDialog, QFormLayout
)
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QTextCharFormat, QTextCursor,QBrush
from PyQt5.QtCore import Qt, QDate, QDateTime, pyqtSignal, QFileInfo
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QFileInfo

from helper.generate_id import generate_patient_id
from core.core import core

arch = core()
patient_id = generate_patient_id()


class HRGradient(HRFlowable):
    """Custom horizontal line with gradient effect"""
    def draw(self):
        self.canv.setStrokeColor(HexColor("#e02793"))
        self.canv.setLineWidth(2)
        self.canv.line(0, 0, self.width, 0)

class SummaryDialog(QDialog):
    def __init__(self, summary_data, parent=None):
        super().__init__(parent)
      
        self.setWindowTitle(arch['appname']) 
        self.setGeometry(120, 100, 1050, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #e83e8c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #d63384;
            }
            QPushButton#editBtn {
                background-color: #6c757d;
            }
            QPushButton#editBtn:hover {
                background-color: #5a6268;
            }
            /* AI Analysis Button Styling */
            QPushButton#aiBtn {
                background-color: #e83e8c;
                margin-top: 10px;
            }
            QPushButton#aiBtn:hover {
                background-color: #d63384;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
        """)
        
        self.summary_data = summary_data
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Review Your Submission")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #e83e8c;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Please review all information and imaging below before final submission.")
        instructions.setFont(QFont("Segoe UI", 11))
        instructions.setStyleSheet("color: #495057; padding: 10px; background-color: #e9ecef; border-radius: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: 1px solid #dee2e6; border-radius: 5px;")
        
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setSpacing(15)
        
        sections = [
            ("Patient Information", self.summary_data.get('patient_info', {})),
            ("Visit/Study Information", self.summary_data.get('visit_info', {})),
            ("Breast Examination Findings", self.summary_data.get('findings', {})),
            ("Early Detection Indicators", self.summary_data.get('indicators', [])),
            ("Imaging Data", self.summary_data.get('imaging', {}))
        ]
        
        for section_title, section_data in sections:
            if section_data:
                section_group = QGroupBox(section_title)
                section_layout = QVBoxLayout()
                
                # Special Handling for Imaging Data Section
                if section_title == "Imaging Data":
                    self.setup_imaging_section(section_layout, section_data)
                
                # Default Handling for other sections
                elif isinstance(section_data, dict):
                    for key, value in section_data.items():
                        if value:
                            row = QHBoxLayout()
                            key_label = QLabel(f"{key}:")
                            key_label.setStyleSheet("font-weight: bold; color: #495057; min-width: 200px;")
                            value_label = QLabel(str(value))
                            row.addWidget(key_label)
                            row.addWidget(value_label, 1)
                            section_layout.addLayout(row)
                            
                elif isinstance(section_data, list):
                    for item in section_data:
                        item_label = QLabel(f"• {item}")
                        item_label.setStyleSheet("color: #212529; margin-left: 10px;")
                        section_layout.addWidget(item_label)
                
                section_group.setLayout(section_layout)
                summary_layout.addWidget(section_group)
        
        summary_layout.addStretch()
        scroll.setWidget(summary_widget)
        layout.addWidget(scroll)
        
        # Bottom Button Row
        button_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Edit Information")
        self.edit_btn.setObjectName("editBtn")
        self.edit_btn.clicked.connect(self.reject)
        
        self.report_btn = QPushButton("Generate Report")
        self.report_btn.clicked.connect(self.generate_pdf_report)

        
        
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.report_btn)
        button_layout.addStretch()
       
        layout.addLayout(button_layout)
        

    def setup_imaging_section(self, layout, data):
        """Helper to create the image preview and AI button"""
        # 1. Display text metadata first
        for key, value in data.items():
            if key.lower() != 'path': # Don't show path as text
                layout.addWidget(QLabel(f"<b>{key}:</b> {value}"))

        # 2. The 'Real' Image Preview
        image_path = data.get('path') # Assume the dictionary has a 'path' key
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(300)
        image_label.setStyleSheet("border: 1px solid #ddd; background: #000; border-radius: 5px;")

        if image_path and QFileInfo.exists(image_path):
            pixmap = QPixmap(image_path)
            # Scale image to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        else:
            image_label.setText("No Image Preview Available")
            image_label.setStyleSheet("color: white; background: #333;")

        layout.addWidget(image_label)

        # 3. Run AI Analysis Button
        self.ai_btn = QPushButton("Run AI Analysis")
        self.ai_btn.setObjectName("aiBtn")
        self.ai_btn.setCursor(Qt.PointingHandCursor)
        self.ai_btn.clicked.connect(self.on_run_ai_analysis)
        
        # Center the AI button
        ai_btn_layout = QHBoxLayout()
        ai_btn_layout.addStretch()
        ai_btn_layout.addWidget(self.ai_btn)
        ai_btn_layout.addStretch()
        layout.addLayout(ai_btn_layout)

    def on_run_ai_analysis(self):
        # Placeholder for AI logic
        self.ai_btn.setText("Analyzing...")
        self.ai_btn.setEnabled(False)
        print("Starting AI Analysis on image...")
            
    def generate_pdf_report(self):
        # Ensure patient_id is retrieved safely
        patient_id = self.summary_data.get("patient_info", {}).get("Patient ID", "Unknown")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Medical Report", f"Report_{patient_id}.pdf", "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        # Configuration
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
        )

        # Color Palette
        PRIMARY_COLOR = HexColor("#2c3e50")   # Dark Navy
        ACCENT_COLOR = HexColor("#e02793")    # Clinical Blue
        TEXT_COLOR = HexColor("#2d3436")      # Soft Black
        BORDER_COLOR = HexColor("#dfe6e9")    # Light Grey

        styles = getSampleStyleSheet()
        
        # Custom Styles
        styles.add(ParagraphStyle(
            name="MainTitle",
            fontSize=22,
            fontName="Helvetica-Bold",
            textColor=PRIMARY_COLOR,
            alignment=0, # Left aligned
            spaceAfter=10
        ))

        styles.add(ParagraphStyle(
            name="ClinicHeader",
            fontSize=10,
            textColor=colors.grey,
            alignment=2, # Right aligned
        ))

        styles.add(ParagraphStyle(
            name="SectionHeader",
            fontSize=12,
            fontName="Helvetica-Bold",
            textColor=ACCENT_COLOR,
            textTransform='UPPERCASE',
            spaceBefore=20,
            spaceAfter=10
        ))

        story = []

        header_data = [
            [
                Paragraph("MEDICAL SCREENING REPORT", styles["MainTitle"]),
                Paragraph("<b>Jimma Medical Center</b><br/>123 Health , NY<br/>Phone: +251965492118", styles["ClinicHeader"])
            ]
        ]
        header_table = Table(header_data, colWidths=[3.5 * inch, 2.5 * inch])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
        story.append(header_table)
        
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=5, spaceAfter=20))

        # --- 2. PATIENT INFO (2-Column Layout) ---
        story.append(Paragraph("Patient Profile", styles["SectionHeader"]))
        
        p_info = self.summary_data.get("patient_info", {})
        # Chunking data into pairs for a 2-column table layout
        items = list(p_info.items())
        table_data = []
        for i in range(0, len(items), 2):
            row = []
            # Column 1
            row.append(Paragraph(f"<b>{items[i][0]}:</b> {items[i][1]}", styles["Normal"]))
            # Column 2 (if exists)
            if i + 1 < len(items):
                row.append(Paragraph(f"<b>{items[i+1][0]}:</b> {items[i+1][1]}", styles["Normal"]))
            else:
                row.append("")
            table_data.append(row)

        patient_table = Table(table_data, colWidths=[3 * inch, 3 * inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#f8f9fa")),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(patient_table)

        # --- 3. CLINICAL FINDINGS ---
        story.append(Paragraph("Examination Findings", styles["SectionHeader"]))
        
        findings = self.summary_data.get("findings", {})
        findings_data = [[Paragraph(f"<b>{k}</b>", styles["Normal"]), Paragraph(str(v), styles["Normal"])] for k, v in findings.items()]
        
        findings_table = Table(findings_data, colWidths=[2 * inch, 4 * inch])
        findings_table.setStyle(TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(findings_table)

        # --- 4. IMAGING SECTION ---
        imaging = self.summary_data.get("imaging", {})
        image_path = imaging.get("path")
        
        if image_path and QFileInfo.exists(image_path):
            story.append(Paragraph("Imaging Analysis", styles["SectionHeader"]))
            # Professional Frame for the Image
            img = Image(image_path, width=4.0 * inch, height=2.8 * inch)
            img_table = Table([[img]], colWidths=[6 * inch])
            img_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
            ]))
            story.append(img_table)
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<i>Source: {imaging.get('type', 'Radiology Scan')}</i>", styles["ClinicHeader"]))

        # --- 5. FOOTER & SIGNATURE ---
        story.append(Spacer(1, 40))
        
        # Signature Line
        sig_data = [["", "__________________________"], ["", "Authorized Physician Signature"]]
        sig_table = Table(sig_data, colWidths=[3.5 * inch, 2.5 * inch])
        sig_table.setStyle(TableStyle([('ALIGN', (1, 1), (1, 1), 'CENTER')]))
        story.append(sig_table)

        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "This is a confidential medical record. Generated by BCD Systems 2025.",
            styles["ClinicHeader"]
        ))

        # Build PDF
        try:
            doc.build(story)
            QMessageBox.information(self, "Success", "PDF report generated!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")


class BreastScreeningApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(arch['appname'])
        self.setWindowIcon(QIcon(arch['icon']))
        self.selected_image_path = None
        
        self.setGeometry(100, 70, 1150, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI';
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #495057;
            }
            QPushButton {
                background-color: #e83e8c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d63384;
            }
            QPushButton:disabled {
                background-color: #ced4da;
                color: #6c757d;
            }
            QLineEdit, QComboBox, QDateEdit, QDateTimeEdit, QSpinBox, QTextEdit {
                padding: 8px;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
            }
            QLabel {
                color: #212529;
                font-size: 14px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                text-align: center;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #e83e8c;
                border-radius: 5px;
            }
        """)
        
        self.current_page = 0
        self.data = {}
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        palette = QPalette()

        pixmap = QPixmap(arch['background_image']).scaled(
            self.size(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )

        palette.setBrush(QPalette.Window, QBrush(pixmap))
        self.setPalette(palette)
        
        
        
        # Header
        header = QLabel("Breast Cancer Screening Data Entry")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet("color: #e83e8c; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        #add image below header
        logo = QLabel()
        pixmap = QPixmap(arch['icon']).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logo)
        
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(6)  # Changed to 6 for summary page
        main_layout.addWidget(self.progress_bar)
        
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        self.page1 = self.create_page1()
        self.page2 = self.create_page2()
        self.page3 = self.create_page3()
        self.page4 = self.create_page4()
        self.page5 = self.create_page5()
        self.page6 = self.create_summary_page()
        
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)
        self.stacked_widget.addWidget(self.page4)
        self.stacked_widget.addWidget(self.page5)
        self.stacked_widget.addWidget(self.page6)
        
        main_layout.addWidget(self.stacked_widget)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self.show_summary_dialog)
        self.submit_btn.setVisible(False)
        
        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.submit_btn)
        
        main_layout.addLayout(nav_layout)
        self.setLayout(main_layout)
        
        # Update progress
        self.update_progress()
        
    def create_page1(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Section 1: Patient Information
        group = QGroupBox("1. Patient Information")
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Row 1
        grid.addWidget(QLabel("Patient ID:"), 0, 0)
        
        self.patient_id = QLineEdit()
        self.patient_id.setText(generate_patient_id())
        self.patient_id.setReadOnly(True)
       
        grid.addWidget(self.patient_id, 0, 1)
        
        grid.addWidget(QLabel("Patient Name / Anonymous Code:"), 0, 2)
        self.patient_name = QLineEdit()
        self.patient_name.setPlaceholderText("Enter name or anonymous code")
        grid.addWidget(self.patient_name, 0, 3)
        
        # Row 2
        grid.addWidget(QLabel("Date of Birth:"), 1, 0)
        self.dob = QDateEdit()
        self.dob.setCalendarPopup(True)
        self.dob.setDate(QDate.currentDate().addYears(-40))
        grid.addWidget(self.dob, 1, 1)
        
        grid.addWidget(QLabel("Age:"), 1, 2)
        self.age = QSpinBox()
        self.age.setRange(18, 100)
        self.age.valueChanged.connect(self.update_age_from_dob)
        grid.addWidget(self.age, 1, 3)
        
        # Row 3
        grid.addWidget(QLabel("Sex:"), 2, 0)
        self.sex = QComboBox()
        self.sex.addItems(["Female"])
        grid.addWidget(self.sex, 2, 1)
        
        grid.addWidget(QLabel("Menopausal Status:"), 2, 2)
        self.menopause = QComboBox()
        self.menopause.addItems(["Pre-menopause", "Post-menopause", "Unknown"])
        grid.addWidget(self.menopause, 2, 3)
        
        # Row 4
        grid.addWidget(QLabel("Contact Information (optional):"), 3, 0)
        self.contact = QLineEdit()
        self.contact.setPlaceholderText("Phone or email")
        grid.addWidget(self.contact, 3, 1, 1, 3)
        
        group.setLayout(grid)
        layout.addWidget(group)
        
        # Add stretch to push content to top
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def update_age_from_dob(self):
        current_year = QDate.currentDate().year()
        birth_year = self.dob.date().year()
        calculated_age = current_year - birth_year
        self.age.blockSignals(True)
        self.age.setValue(calculated_age)
        self.age.blockSignals(False)
    
    def create_page2(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Section 2: Visit / Study Information
        group = QGroupBox("2. Visit / Study Information")
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Row 1
        grid.addWidget(QLabel("Study ID / Accession Number:"), 0, 0)
        self.study_id = QLineEdit()
        self.study_id.setPlaceholderText("Enter Study ID")
        grid.addWidget(self.study_id, 0, 1)
        
        grid.addWidget(QLabel("Study Date & Time:"), 0, 2)
        self.study_datetime = QDateTimeEdit()
        self.study_datetime.setDateTime(QDateTime.currentDateTime())
        self.study_datetime.setCalendarPopup(True)
        grid.addWidget(self.study_datetime, 0, 3)
        
        # Row 2
        grid.addWidget(QLabel("Imaging Modality:"), 1, 0)
        self.modality = QComboBox()
        self.modality.addItems(["Ultrasound", "Mammography", "MRI"])
        grid.addWidget(self.modality, 1, 1)
        
        grid.addWidget(QLabel("Examination Type:"), 1, 2)
        self.exam_type = QLineEdit()
        self.exam_type.setPlaceholderText("e.g., Screening, Diagnostic")
        grid.addWidget(self.exam_type, 1, 3)
        
        # Row 3
        grid.addWidget(QLabel("Breast Examination Technique:"), 2, 0)
        self.technique_group = QGroupBox()
        self.technique_group.setFlat(True)
        tech_layout = QVBoxLayout()
        self.tech_radial = QCheckBox("Radial")
        self.tech_antiradial = QCheckBox("Anti-radial")
        self.tech_other = QCheckBox("Other")
        tech_layout.addWidget(self.tech_radial)
        tech_layout.addWidget(self.tech_antiradial)
        tech_layout.addWidget(self.tech_other)
        self.technique_group.setLayout(tech_layout)
        grid.addWidget(self.technique_group, 2, 1)
        
        grid.addWidget(QLabel("Health Facility / Institution:"), 2, 2)
        self.facility = QLineEdit()
        grid.addWidget(self.facility, 2, 3)
        
        # Row 4
        grid.addWidget(QLabel("Reporting Clinician:"), 3, 0)
        self.clinician = QLineEdit()
        self.clinician.setPlaceholderText("Name of reporting clinician")
        grid.addWidget(self.clinician, 3, 1, 1, 3)
        
        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def create_page3(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Section 3: Breast Examination Findings
        group = QGroupBox("3. Breast Examination Findings")
        main_grid = QGridLayout()
        main_grid.setSpacing(20)
        
        # Right Breast Column
        right_group = QGroupBox("Right Breast")
        right_layout = QVBoxLayout()
        
        self.right_findings = []
        findings = [
            "Retroareolar duct dilatation",
            "Echogenic duct content",
            "Duct ectasia",
            "Solid mass present",
            "Skin thickening",
            "Nipple retraction",
            "Architectural distortion",
            "Mammillary lymphadenopathy",
            "Axillary lymphadenopathy"
        ]
        
        for finding in findings:
            cb = QCheckBox(finding)
            right_layout.addWidget(cb)
            self.right_findings.append(cb)
        
        right_group.setLayout(right_layout)
        main_grid.addWidget(right_group, 0, 0)
        
        # Left Breast Column
        left_group = QGroupBox("Left Breast")
        left_layout = QVBoxLayout()
        
        self.left_findings = []
        left_findings = [
            "Retroareolar duct dilatation",
            "Echogenic duct content",
            "Solid mass present",
            "Skin thickening",
            "Nipple retraction",
            "Architectural distortion",
            "Mammillary lymphadenopathy",
            "Axillary lymphadenopathy"
        ]
        
        for finding in left_findings:
            cb = QCheckBox(finding)
            left_layout.addWidget(cb)
            self.left_findings.append(cb)
        
        left_group.setLayout(left_layout)
        main_grid.addWidget(left_group, 0, 1)
        
        group.setLayout(main_grid)
        layout.addWidget(group)
        layout.addStretch()
        
        content.setLayout(layout)
        scroll.setWidget(content)
        
        page_layout = QVBoxLayout()
        page_layout.addWidget(scroll)
        page.setLayout(page_layout)
        return page
    
    def create_page4(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Section 4: Early Detection Indicators
        group = QGroupBox("4. Early Detection Indicators")
        indicators_layout = QVBoxLayout()
        
        self.indicators = []
        indicators = [
            "Suspicious mass detected",
            "Suspicious lymph nodes detected",
            "Skin or nipple abnormality detected",
            "Previous examination available",
            "Change compared to previous exam",
            "Stability over time"
        ]
        
        for indicator in indicators:
            cb = QCheckBox(indicator)
            indicators_layout.addWidget(cb)
            self.indicators.append(cb)
        
        group.setLayout(indicators_layout)
        layout.addWidget(group)
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def create_page5(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Section 5: Loading / Imaging Module
        group = QGroupBox("5. Loading / Imaging Module")
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Image upload
        grid.addWidget(QLabel("Upload Image:"), 0, 0)
        self.upload_btn = QPushButton("Select Image")
        self.upload_btn.clicked.connect(self.select_image)
        grid.addWidget(self.upload_btn, 0, 1)
        
        self.image_path_label = QLabel("No image selected")
        self.image_path_label.setStyleSheet("color: #6c757d; font-style: italic;")
        grid.addWidget(self.image_path_label, 0, 2, 1, 2)
        
        # Image Type
        grid.addWidget(QLabel("Image Type:"), 1, 0)
        self.image_type = QComboBox()
        self.image_type.addItems(["Ultrasound", "Mammography", "MRI"])
        grid.addWidget(self.image_type, 1, 1)
        
        # Laterality
        grid.addWidget(QLabel("Laterality:"), 1, 2)
        self.laterality = QComboBox()
        self.laterality.addItems(["Right", "Left", "Bilateral"])
        grid.addWidget(self.laterality, 1, 3)
        
        # Image Date
        grid.addWidget(QLabel("Image Date:"), 2, 0)
        self.image_date = QDateTimeEdit()
        self.image_date.setDateTime(QDateTime.currentDateTime())
        self.image_date.setCalendarPopup(True)
        grid.addWidget(self.image_date, 2, 1)
        
        # Image Reference ID
        grid.addWidget(QLabel("Image Reference ID:"), 2, 2)
        self.image_ref = QLineEdit()
        grid.addWidget(self.image_ref, 2, 3)
        
        # Image Description
        grid.addWidget(QLabel("Image Description / Notes:"), 3, 0)
        self.image_desc = QTextEdit()
        self.image_desc.setMaximumHeight(100)
        grid.addWidget(self.image_desc, 3, 1, 1, 3)
        
        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def create_summary_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        title = QLabel("Data Summary Preview")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #e83e8c; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
     
        
        # Quick summary preview
        preview_group = QGroupBox("Quick Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("color: #212529; padding: 10px;")
        self.preview_label.setFont(QFont("Segoe UI", 10))
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Note
        note = QLabel(" All data will be finalized upon confirmation in the next step.")
        note.setFont(QFont("Segoe UI", 10, QFont.Bold))
        note.setStyleSheet("color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 5px;")
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Medical Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_path:
            self.selected_image_path = file_path
            self.image_path_label.setText(QFileInfo(file_path).fileName())

    
    def next_page(self):
        if self.current_page < 5:
            self.current_page += 1
            self.stacked_widget.setCurrentIndex(self.current_page)
            self.update_progress()
            
            # Update button states
            self.prev_btn.setEnabled(self.current_page > 0)
            
            if self.current_page == 5:  # Summary page
                self.update_summary_preview()
                self.next_btn.setVisible(False)
                self.submit_btn.setVisible(True)
                self.submit_btn.setText("Review & Submit")
    
    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.stacked_widget.setCurrentIndex(self.current_page)
            self.update_progress()
            
            # Update button states
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setVisible(True)
            self.submit_btn.setVisible(False)
    
    def update_progress(self):
        self.progress_bar.setValue(self.current_page + 1)
    
    def update_summary_preview(self):
        """Create a quick preview for the summary page"""
        preview_text = f"""
        <b>Patient:</b> {self.patient_name.text() or 'Anonymous'} (ID: {self.patient_id.text() or 'Not specified'})<br>
        <b>Study:</b> {self.study_id.text() or 'Not specified'} on {self.study_datetime.dateTime().toString('yyyy-MM-dd')}<br>
        <b>Modality:</b> {self.modality.currentText()}<br>
        <b>Findings:</b> {self.count_findings()} total findings across both breasts<br>
        <b>Indicators:</b> {self.count_indicators()} early detection indicators noted<br>
        <b>Images:</b> {self.image_path_label.text() if self.image_path_label.text() != 'No image selected' else 'No images'}
        """
        self.preview_label.setText(preview_text)
    
    def count_findings(self):
        count = 0
        for cb in self.right_findings + self.left_findings:
            if cb.isChecked():
                count += 1
        return count
    
    def count_indicators(self):
        count = 0
        for cb in self.indicators:
            if cb.isChecked():
                count += 1
        return count
    
    def collect_summary_data(self):
        """Collect all data in a structured format for the summary dialog"""
        data = {}
        
        # Patient Information
        data['patient_info'] = {
            'Patient ID': self.patient_id.text(),
            'Name/Code': self.patient_name.text(),
            'Date of Birth': self.dob.date().toString('yyyy-MM-dd'),
            'Age': str(self.age.value()),
            'Sex': self.sex.currentText(),
            'Menopausal Status': self.menopause.currentText(),
            'Contact': self.contact.text() if self.contact.text() else 'Not provided'
        }
        
        # Visit Information
        techniques = []
        if self.tech_radial.isChecked(): techniques.append("Radial")
        if self.tech_antiradial.isChecked(): techniques.append("Anti-radial")
        if self.tech_other.isChecked(): techniques.append("Other")
        
        data['visit_info'] = {
            'Study ID': self.study_id.text(),
            'Study Date': self.study_datetime.dateTime().toString('yyyy-MM-dd hh:mm'),
            'Imaging Modality': self.modality.currentText(),
            'Examination Type': self.exam_type.text(),
            'Techniques': ', '.join(techniques) if techniques else 'None specified',
            'Health Facility': self.facility.text(),
            'Reporting Clinician': self.clinician.text()
        }
        
        # Findings
        right_findings = []
        left_findings = []
        
        for cb in self.right_findings:
            if cb.isChecked():
                right_findings.append(cb.text())
        
        for cb in self.left_findings:
            if cb.isChecked():
                left_findings.append(cb.text())
        
        data['findings'] = {
            'Right Breast Findings': ', '.join(right_findings) if right_findings else 'None',
            'Left Breast Findings': ', '.join(left_findings) if left_findings else 'None'
        }
        
        # Indicators
        indicator_list = []
        for cb in self.indicators:
            if cb.isChecked():
                indicator_list.append(cb.text())
        
        data['indicators'] = indicator_list
        
        # Imaging Data
        data['imaging'] = {
            'Image Type': self.image_type.currentText(),
            'Laterality': self.laterality.currentText(),
            'Image Date': self.image_date.dateTime().toString('yyyy-MM-dd hh:mm'),
            'Image Reference ID': self.image_ref.text(),
            'Image File': self.image_path_label.text(),
            'Description': self.image_desc.toPlainText()[:100] + ('...' if len(self.image_desc.toPlainText()) > 100 else ''),
            'path': self.selected_image_path
        }
        
        return data
    
    def show_summary_dialog(self):
        """Show the detailed summary dialog for final review"""
        summary_data = self.collect_summary_data()
        
        dialog = SummaryDialog(summary_data, self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self.submit_data()
        # If rejected (Edit button clicked), stay on summary page
    
    def submit_data(self):
        """Final submission of data"""
        # Here you would normally save the data to a database or file
        print("Data submitted successfully!")
        
        # Success message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Submission Successful")
        msg.setText("All data has been submitted successfully!")
        msg.setInformativeText("Your breast screening data has been recorded and saved.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
        
        # Optionally reset the form or close
        # self.reset_form()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BreastScreeningApp()
    window.show()
    sys.exit(app.exec_())