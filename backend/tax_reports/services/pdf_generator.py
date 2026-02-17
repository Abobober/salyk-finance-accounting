from io import BytesIO
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    A4 = None
    canvas = None

try:
    from pypdf import PdfReader, PdfWriter
except Exception:  # pragma: no cover
    PdfReader = None
    PdfWriter = None


class UnifiedTaxPDFGenerator:
    def __init__(self, data, template_path):
        self.data = data
        self.template_path = Path(template_path)

    def _lines(self):
        return [
            f"Year: {self.data['year']}",
            f"Quarter: {self.data['quarter']}",
            f"Organization: {self.data['organization_name']}",
            f"INN: {self.data['inn']}",
            f"Turnover: {self.data['turnover']}",
            f"Rate: {self.data['rate']}%",
            f"Unified tax: {self.data['unified_tax']}",
            f"Social fund: {self.data['social_fund']}",
            f"Total payable: {self.data['total_payable']}",
        ]

    def _draw_overlay(self, page_width, page_height):
        packet = BytesIO()
        pdf = canvas.Canvas(packet, pagesize=(page_width, page_height))
        pdf.setFont("Helvetica", 10)

        left = page_width * 0.09
        y = page_height * 0.89
        step = 18

        for line in self._lines():
            pdf.drawString(left, y, line)
            y -= step

        pdf.save()
        packet.seek(0)
        return PdfReader(packet).pages[0]

    def _draw_fallback_pdf_with_reportlab(self, output_path):
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        width, height = A4
        pdf = canvas.Canvas(str(output), pagesize=A4)
        pdf.setFont("Helvetica", 11)

        left = width * 0.1
        y = height * 0.9
        step = 20

        pdf.drawString(left, y, "Unified tax report")
        y -= step * 2
        for line in self._lines():
            pdf.drawString(left, y, line)
            y -= step

        pdf.save()

    def _write_minimal_pdf(self, output_path):
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        text_lines = ["Unified tax report", ""] + self._lines()
        escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in text_lines]

        content_parts = ["BT", "/F1 12 Tf", "50 800 Td"]
        for i, line in enumerate(escaped):
            if i == 0:
                content_parts.append(f"({line}) Tj")
            else:
                content_parts.append("0 -18 Td")
                content_parts.append(f"({line}) Tj")
        content_parts.append("ET")
        stream_text = "\n".join(content_parts).encode("latin-1", errors="replace")

        objs = []
        objs.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        objs.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
        objs.append(
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        )
        objs.append(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
        objs.append(
            f"5 0 obj\n<< /Length {len(stream_text)} >>\nstream\n".encode("latin-1")
            + stream_text
            + b"\nendstream\nendobj\n"
        )

        header = b"%PDF-1.4\n"
        body = bytearray()
        offsets = [0]
        current_offset = len(header)
        for obj in objs:
            offsets.append(current_offset)
            body.extend(obj)
            current_offset += len(obj)

        xref_offset = len(header) + len(body)
        xref = [f"xref\n0 {len(offsets)}\n".encode("latin-1")]
        xref.append(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            xref.append(f"{off:010d} 00000 n \n".encode("latin-1"))

        trailer = (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
        ).encode("latin-1")

        output.write_bytes(header + bytes(body) + b"".join(xref) + trailer)

    def generate(self, output_path):
        if (
            canvas is not None
            and PdfReader is not None
            and PdfWriter is not None
            and self.template_path.exists()
        ):
            try:
                template_reader = PdfReader(str(self.template_path))
                writer = PdfWriter()

                first_page = template_reader.pages[0]
                overlay = self._draw_overlay(
                    float(first_page.mediabox.width),
                    float(first_page.mediabox.height),
                )

                for index, page in enumerate(template_reader.pages):
                    if index == 0:
                        page.merge_page(overlay)
                    writer.add_page(page)

                output = Path(output_path)
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("wb") as fh:
                    writer.write(fh)
                return
            except Exception:
                pass

        if canvas is not None and A4 is not None:
            self._draw_fallback_pdf_with_reportlab(output_path)
            return

        self._write_minimal_pdf(output_path)
