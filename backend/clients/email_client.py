import resend
import os
import logging
import markdown
import weasyprint
import base64
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailClient:
    def __init__(self):
        self.client = resend
        self.client.api_key = os.getenv("RESEND_API_KEY")

    def _markdown_to_html(self, markdown_content: str) -> str:
        """마크다운 텍스트를 HTML로 변환합니다."""
        # 추가 확장 기능을 사용하여 더 나은 HTML 출력
        md = markdown.Markdown(extensions=["tables", "fenced_code"])
        html_content = md.convert(markdown_content)

        # 기본적인 CSS 스타일 추가
        styled_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; \
                    line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                h1 {{ border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f8f9fa; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f8f9fa; }}
                blockquote {{ border-left: 4px solid #3498db; margin: 20px 0; padding-left: 20px; font-style: italic;\
                 background-color: #f8f9fa; }}
                code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-family: 'Monaco', \
                'Consolas', monospace; }}
                pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                ul, ol {{ margin: 10px 0; padding-left: 30px; }}
                .emoji {{ font-size: 1.2em; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        return styled_html

    def _markdown_to_pdf(self, markdown_content: str, filename: str = "report.pdf") -> bytes:
        """마크다운 텍스트를 PDF로 변환합니다."""
        # 먼저 HTML로 변환
        html_content = self._markdown_to_html(markdown_content)

        # PDF를 위한 CSS 스타일 (프린트 최적화)
        pdf_css = """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 12pt;
        }
        h1, h2, h3 {
            color: #2c3e50;
            page-break-after: avoid;
        }
        h1 {
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            font-size: 18pt;
        }
        h2 {
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
            font-size: 14pt;
        }
        h3 {
            font-size: 12pt;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            page-break-inside: avoid;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            font-size: 10pt;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        blockquote {
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            font-style: italic;
            background-color: #f8f9fa;
            page-break-inside: avoid;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 10pt;
        }
        pre {
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            page-break-inside: avoid;
        }
        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }
        li {
            margin-bottom: 5px;
        }
        """

        # HTML에 PDF용 CSS 추가
        pdf_html = html_content.replace("</style>", f"{pdf_css}</style>")

        # PDF 생성
        pdf_bytes = weasyprint.HTML(string=pdf_html).write_pdf()
        return pdf_bytes

    def send_markdown_email_with_pdf(
        self,
        to: str,
        subject: str = "[Porta] 에이전트 보고서 결과",
        markdown_content: str = "",
        pdf_filename: str = "[Porta] 포트폴리오_피드백_보고서",
    ):
        """마크다운 콘텐츠를 HTML 이메일로 발송하고 PDF 파일을 첨부합니다."""
        try:
            # HTML 변환
            html_content = self._markdown_to_html(markdown_content)

            # PDF 변환
            pdf_bytes = self._markdown_to_pdf(markdown_content, pdf_filename)

            # PDF를 base64로 인코딩
            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

            # 첨부파일과 함께 이메일 발송
            email_data = {
                "from": "Porta <porta@resend.dev>",
                "to": to,
                "subject": subject,
                "html": html_content,
                "attachments": [
                    {
                        "filename": f"{pdf_filename}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        "content": pdf_base64,
                        "type": "application/pdf",
                    }
                ],
            }

            r = self.client.Emails.send(email_data)
            logger.info(f"PDF 첨부 이메일 발송 성공: {r}")
            return r

        except Exception as e:
            logger.error(f"PDF 첨부 이메일 발송 실패: {e}")
            raise
