"""
PDF Invoice Generation Service for VocalLocal
Generates professional PDF invoices for payment confirmations
"""

import os
import io
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    logger.warning("ReportLab not available. PDF invoice generation will be disabled.")
    REPORTLAB_AVAILABLE = False

class PDFInvoiceService:
    """Service for generating PDF invoices"""
    
    def __init__(self):
        self.company_info = {
            'name': 'VocalLocal',
            'tagline': 'AI-Powered Transcription & Translation Platform',
            'address': [
                'VocalLocal Inc.',
                'AI Services Division',
                'support@vocallocal.com',
                'https://vocallocal.com'
            ],
            'logo_path': None  # Can be set to logo file path if available
        }
    
    def generate_invoice_pdf(self, invoice_data: Dict[str, Any]) -> Optional[bytes]:
        """
        Generate a PDF invoice from invoice data
        
        Args:
            invoice_data (dict): Invoice information containing:
                - invoice_id: str
                - customer_name: str
                - customer_email: str
                - amount: float
                - currency: str
                - payment_date: datetime
                - plan_name: str
                - plan_type: str
                - billing_cycle: str
                - payment_method: str (optional)
                - transaction_id: str (optional)
        
        Returns:
            bytes: PDF content as bytes, or None if generation fails
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available. Cannot generate PDF invoice.")
            return None
        
        try:
            # Create a BytesIO buffer to hold the PDF
            buffer = io.BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build the PDF content
            story = []
            styles = getSampleStyleSheet()
            
            # Add custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#2c3e50'),
                alignment=TA_CENTER
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#34495e')
            )
            
            # Company header
            story.append(Paragraph(self.company_info['name'], title_style))
            story.append(Paragraph(self.company_info['tagline'], styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Invoice title and number
            invoice_title = f"INVOICE #{invoice_data['invoice_id']}"
            story.append(Paragraph(invoice_title, header_style))
            story.append(Spacer(1, 20))
            
            # Invoice details table
            invoice_details = [
                ['Invoice Date:', invoice_data['payment_date'].strftime('%B %d, %Y')],
                ['Customer:', invoice_data['customer_name']],
                ['Email:', invoice_data['customer_email']],
                ['Payment Method:', invoice_data.get('payment_method', 'Credit Card')],
            ]
            
            if invoice_data.get('transaction_id'):
                invoice_details.append(['Transaction ID:', invoice_data['transaction_id']])
            
            details_table = Table(invoice_details, colWidths=[2*inch, 4*inch])
            details_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(details_table)
            story.append(Spacer(1, 30))
            
            # Services table
            story.append(Paragraph("Services", header_style))
            
            # Calculate plan features based on plan type
            plan_features = self._get_plan_features(invoice_data['plan_type'])
            
            services_data = [
                ['Description', 'Plan Features', 'Billing Cycle', 'Amount'],
                [
                    invoice_data['plan_name'],
                    plan_features,
                    invoice_data['billing_cycle'].title(),
                    f"{invoice_data['currency']} {invoice_data['amount']:.2f}"
                ]
            ]
            
            services_table = Table(services_data, colWidths=[2*inch, 2.5*inch, 1*inch, 1*inch])
            services_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),  # Right align amount column
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(services_table)
            story.append(Spacer(1, 20))
            
            # Total section
            total_data = [
                ['Subtotal:', f"{invoice_data['currency']} {invoice_data['amount']:.2f}"],
                ['Tax:', f"{invoice_data['currency']} 0.00"],
                ['Total Paid:', f"{invoice_data['currency']} {invoice_data['amount']:.2f}"]
            ]
            
            total_table = Table(total_data, colWidths=[4.5*inch, 1.5*inch])
            total_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(total_table)
            story.append(Spacer(1, 30))
            
            # Payment confirmation
            confirmation_text = f"""
            <b>Payment Confirmed</b><br/>
            Thank you for your payment! Your {invoice_data['plan_name']} subscription is now active.
            You can access all premium features immediately.
            """
            
            story.append(Paragraph(confirmation_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Footer
            footer_text = """
            <b>Questions or Support?</b><br/>
            Email: support@vocallocal.com<br/>
            Website: https://vocallocal.com<br/><br/>
            Thank you for choosing VocalLocal!
            """
            
            story.append(Paragraph(footer_text, styles['Normal']))
            
            # Build the PDF
            doc.build(story)
            
            # Get the PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated PDF invoice for {invoice_data['customer_email']}, size: {len(pdf_content)} bytes")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating PDF invoice: {str(e)}")
            return None
    
    def _get_plan_features(self, plan_type: str) -> str:
        """Get plan features description for the invoice"""
        features = {
            'basic': '280 transcription minutes\n50K translation words\n60 TTS minutes\n50 AI credits',
            'professional': '800 transcription minutes\n160K translation words\n200 TTS minutes\n150 AI credits',
            'premium': '800 transcription minutes\n160K translation words\n200 TTS minutes\n150 AI credits',
            'enterprise': 'Unlimited usage\nPriority support\nCustom integrations'
        }
        
        return features.get(plan_type.lower(), 'Premium AI services')
    
    def save_invoice_to_file(self, pdf_content: bytes, filename: str, directory: str = None) -> str:
        """
        Save PDF content to a file
        
        Args:
            pdf_content (bytes): PDF content
            filename (str): Filename for the PDF
            directory (str): Directory to save the file (optional)
        
        Returns:
            str: Full path to the saved file
        """
        try:
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            file_path = os.path.join(directory or '', filename)
            
            with open(file_path, 'wb') as f:
                f.write(pdf_content)
            
            logger.info(f"Saved PDF invoice to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving PDF invoice: {str(e)}")
            raise
